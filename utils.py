
import ftplib
import unicodedata
import requests
import pandas as pd

from bs4 import BeautifulSoup
from io import BytesIO, StringIO
from zipfile import ZipFile
from pathlib import Path
from typing import TypedDict
from urllib.parse import urlparse, unquote, urljoin
from typing import Optional

class ErroLeitura(TypedDict):
    """
    Estrutura padronizada para representar erros ocorridos na leitura
    de arquivos remotos ou arquivos internos de ZIP.
    """

    arquivo: str
    erro: str


class ResultadoProcessamento(TypedDict):
    """
    Estrutura de retorno do processamento da URL informada.

    Chaves
    ------
    conteudo_zip : bytes | None
        Conteúdo binário do ZIP baixado, quando a origem principal for um arquivo ZIP.
        Para pasta FTP ou HTTP/HTTPS com múltiplos arquivos, retorna None.

    arquivos_lidos : list[str]
        Lista com os nomes dos arquivos processados com sucesso.

    arquivos_ignorados : list[str]
        Lista com os nomes dos arquivos ignorados por extensão incompatível
        ou por regra de nome.

    erros : list[ErroLeitura]
        Lista com erros ocorridos durante o processamento.

    df_unificado : pd.DataFrame
        DataFrame final com todos os arquivos concatenados.
    """

    conteudo_zip: bytes | None
    arquivos_lidos: list[str]
    arquivos_ignorados: list[str]
    erros: list[ErroLeitura]
    df_unificado: pd.DataFrame



def baixar_extrair_juntar(url_zip: str) -> ResultadoProcessamento:
    """
    Processa automaticamente a URL informada, identificando se ela aponta para:

    1. um arquivo `.zip`,
    2. um arquivo tabular compatível (`.csv`, `.xlsx`, `.xls`, `.ods`),
    3. uma pasta FTP contendo múltiplos arquivos,
    4. uma página HTTP/HTTPS com arquivos listados,
    5. uma página HTTP/HTTPS ou pasta FTP com subpastas contendo arquivos.

    A função adota a estratégia correspondente:

    - Se for arquivo `.zip`, baixa o ZIP, extrai em memória os arquivos
      compatíveis e concatena todos em um único DataFrame.
    - Se for arquivo tabular compatível, baixa e retorna seu conteúdo como DataFrame.
    - Se for pasta FTP, lista recursivamente os arquivos da estrutura,
      baixa os arquivos compatíveis e concatena todos em um único DataFrame.
    - Se for página HTTP/HTTPS, faz o parsing da listagem, identifica links
      para arquivos compatíveis e, se necessário, percorre subpastas
      automaticamente.

    Extensões suportadas:
    - .csv
    - .xlsx
    - .xls
    - .ods

    Para arquivos CSV, a função tenta automaticamente múltiplos encodings:
    - utf-8
    - utf-8-sig
    - latin1

    Além disso, tenta inferir o separador automaticamente. Caso a inferência
    falhe, utiliza ';' como fallback.

    Regra adicional de ignorar arquivos
    ----------------------------------
    Arquivos cujo nome contenha a palavra 'dicionario' são ignorados,
    independentemente de:
    - acentuação
    - letras maiúsculas/minúsculas

    Regra adicional de mesclagem por grupo
    --------------------------------------
    A função identifica automaticamente um grupo de mesclagem a partir do nome
    do arquivo de origem, considerando o último bloco do nome (separado por '_').

    Exemplos:
    - AC_202401_HOSP_CONS.zip -> grupo 'CONS'
    - AC_202401_HOSP_DET.zip  -> grupo 'DET'
    - AC_202401_HOSP_REM.zip  -> grupo 'REM'

    Arquivos do mesmo grupo são concatenados entre si. Ao final, a função:
    - retorna um DataFrame unificado com todos os grupos;
    - adiciona a coluna `grupo_mescla`;
    - salva um arquivo `.csv` por grupo na pasta atual de execução
      (`Path.cwd()`), com nomes no padrão `mescla_<GRUPO>.csv`.

    Parâmetros
    ----------
    url_zip : str
        URL da origem dos dados. Pode ser:
        - URL HTTP/HTTPS/FTP de um arquivo .zip
        - URL HTTP/HTTPS/FTP de um arquivo compatível
        - URL FTP apontando para uma pasta
        - URL HTTP/HTTPS apontando para uma página com listagem de arquivos
        - URL HTTP/HTTPS/FTP apontando para uma estrutura com subpastas

    Retorno
    -------
    ResultadoProcessamento
        Estrutura com:
        - "conteudo_zip": bytes do ZIP baixado, quando aplicável
        - "arquivos_lidos": lista de arquivos lidos com sucesso
        - "arquivos_ignorados": lista de arquivos ignorados
        - "erros": lista de erros ocorridos
        - "df_unificado": DataFrame unificado com todos os dados concatenados

    Efeitos colaterais
    ------------------
    Para cada grupo de mesclagem encontrado, a função salva um arquivo `.csv`
    na pasta atual de execução do notebook, no formato:
    - `mescla_CONS.csv`
    - `mescla_DET.csv`
    - `mescla_REM.csv`
    - etc.

    Se ocorrer erro ao salvar algum arquivo de saída, o erro será registrado na
    lista `erros`, sem interromper o processamento dos demais grupos.

    Raises
    ------
    requests.HTTPError
        Se ocorrer erro ao baixar um arquivo via HTTP/HTTPS.
    ValueError
        Se a URL não for suportada ou se nenhum arquivo compatível for lido.
    """
    extensoes_tabulares_suportadas: set[str] = {".csv", ".xlsx", ".xls", ".ods"}

    def nome_deve_ser_ignorado(nome_arquivo: str) -> bool:
        """
        Verifica se o nome do arquivo deve ser ignorado com base na presença
        da palavra 'dicionario', desconsiderando:
        - acentuação
        - letras maiúsculas/minúsculas

        Parâmetros
        ----------
        nome_arquivo : str
            Nome do arquivo ou caminho completo.

        Retorno
        -------
        bool
            True se o arquivo deve ser ignorado; caso contrário, False.
        """
        nome_base: str = Path(nome_arquivo).stem
        nome_normalizado: str = unicodedata.normalize("NFKD", nome_base)
        nome_sem_acento: str = "".join(
            caractere
            for caractere in nome_normalizado
            if not unicodedata.combining(caractere)
        ).lower()

        return "dicionario" in nome_sem_acento

    def obter_grupo_mescla(nome_arquivo: str, grupo_padrao: Optional[str] = None) -> str:
        """
        Identifica o grupo de mesclagem de um arquivo com base no último bloco
        do nome, separado por underscore.

        Exemplos:
        - AC_202401_HOSP_CONS.zip -> CONS
        - AC_202401_HOSP_DET.csv  -> DET
        - AC_202401_HOSP_REM.xls  -> REM

        Se `grupo_padrao` for informado, ele terá prioridade sobre a inferência
        pelo nome do arquivo. Isso é útil para manter o agrupamento de arquivos
        extraídos de um ZIP com base no nome do próprio ZIP.

        Parâmetros
        ----------
        nome_arquivo : str
            Nome do arquivo ou caminho.
        grupo_padrao : Optional[str], opcional
            Grupo a ser usado diretamente, quando necessário.

        Retorno
        -------
        str
            Grupo de mesclagem identificado.
        """
        if grupo_padrao:
            return grupo_padrao

        nome_base: str = Path(nome_arquivo).stem
        nome_normalizado: str = unicodedata.normalize("NFKD", nome_base)
        nome_sem_acento: str = "".join(
            caractere
            for caractere in nome_normalizado
            if not unicodedata.combining(caractere)
        )

        nome_sem_acento = nome_sem_acento.replace("-", "_")
        partes_nome: list[str] = [parte for parte in nome_sem_acento.split("_") if parte]

        if not partes_nome:
            return "SEM_GRUPO"

        return partes_nome[-1].upper()

    def normalizar_nome_arquivo_saida(grupo_mescla: str) -> str:
        """
        Normaliza o nome do grupo para uso seguro como nome de arquivo.

        Regras aplicadas:
        - remove acentuação;
        - converte para maiúsculas;
        - substitui caracteres não alfanuméricos por underscore;
        - remove underscores duplicados nas extremidades.

        Parâmetros
        ----------
        grupo_mescla : str
            Nome do grupo de mesclagem.

        Retorno
        -------
        str
            Nome normalizado para uso em arquivo.
        """
        grupo_normalizado: str = unicodedata.normalize("NFKD", grupo_mescla)
        grupo_sem_acento: str = "".join(
            caractere
            for caractere in grupo_normalizado
            if not unicodedata.combining(caractere)
        ).upper()

        caracteres_processados: list[str] = []
        for caractere in grupo_sem_acento:
            if caractere.isalnum():
                caracteres_processados.append(caractere)
            else:
                caracteres_processados.append("_")

        nome_normalizado: str = "".join(caracteres_processados).strip("_")

        while "__" in nome_normalizado:
            nome_normalizado = nome_normalizado.replace("__", "_")

        return nome_normalizado or "SEM_GRUPO"

    def ler_arquivo(conteudo_bytes: bytes, nome_arquivo: str) -> pd.DataFrame | None:
        """
        Lê um arquivo em memória a partir de seus bytes, de acordo com sua extensão.

        Extensões suportadas:
        - .csv
        - .xlsx
        - .xls
        - .ods

        Parâmetros
        ----------
        conteudo_bytes : bytes
            Conteúdo binário do arquivo.
        nome_arquivo : str
            Nome do arquivo, utilizado para identificar sua extensão.

        Retorno
        -------
        pd.DataFrame | None
            DataFrame com os dados lidos, ou None se a extensão não for suportada.

        Raises
        ------
        ValueError
            Se o arquivo CSV não puder ser lido com os encodings testados.
        """
        extensao: str = Path(nome_arquivo).suffix.lower()

        if extensao == ".csv":
            encodings_teste: list[str] = ["utf-8", "utf-8-sig", "latin1"]

            for encoding in encodings_teste:
                try:
                    texto: str = conteudo_bytes.decode(encoding)

                    try:
                        return pd.read_csv(
                            StringIO(texto),
                            sep=None,
                            engine="python",
                            low_memory=False
                        )
                    except Exception:
                        return pd.read_csv(
                            StringIO(texto),
                            sep=";",
                            low_memory=False
                        )
                except Exception:
                    continue

            raise ValueError(f"Falha ao ler CSV: {nome_arquivo}")

        if extensao == ".xlsx":
            return pd.read_excel(BytesIO(conteudo_bytes), engine="openpyxl")

        if extensao == ".xls":
            return pd.read_excel(BytesIO(conteudo_bytes), engine="xlrd")

        if extensao == ".ods":
            return pd.read_excel(BytesIO(conteudo_bytes), engine="odf")

        return None

    def baixar_arquivo_remoto(url: str) -> bytes:
        """
        Baixa um arquivo remoto em memória a partir de uma URL HTTP, HTTPS ou FTP.

        Parâmetros
        ----------
        url : str
            URL completa do arquivo remoto.

        Retorno
        -------
        bytes
            Conteúdo binário do arquivo baixado.

        Raises
        ------
        requests.HTTPError
            Se ocorrer erro no download via HTTP/HTTPS.
        ValueError
            Se o esquema da URL não for suportado.
        """
        url_parseada = urlparse(url)
        esquema: str = url_parseada.scheme.lower()

        if esquema in {"http", "https"}:
            resposta: requests.Response = requests.get(url, timeout=300)
            resposta.raise_for_status()
            return resposta.content

        if esquema == "ftp":
            host: str = url_parseada.hostname or ""
            caminho_remoto: str = unquote(url_parseada.path)

            if not host or not caminho_remoto:
                raise ValueError(f"URL FTP inválida: {url}")

            diretorio_remoto: str = str(Path(caminho_remoto).parent).replace("\\", "/")
            nome_arquivo: str = Path(caminho_remoto).name

            if not nome_arquivo:
                raise ValueError(f"A URL FTP não aponta para um arquivo: {url}")

            buffer = BytesIO()

            with ftplib.FTP(host, timeout=300) as ftp:
                ftp.login()

                if diretorio_remoto not in {"", "."}:
                    ftp.cwd(diretorio_remoto)

                ftp.retrbinary(f"RETR {nome_arquivo}", buffer.write)

            return buffer.getvalue()

        raise ValueError(f"Esquema de URL não suportado: {esquema}")

    def listar_arquivos_ftp(url_ftp: str) -> list[str]:
        """
        Lista recursivamente os arquivos contidos em uma pasta FTP.

        A função percorre a pasta informada e suas subpastas, retornando
        os caminhos completos dos arquivos encontrados. Isso permite tratar
        estruturas mistas com arquivos soltos no diretório e arquivos dentro
        de subpastas.

        Parâmetros
        ----------
        url_ftp : str
            URL FTP apontando para uma pasta.

        Retorno
        -------
        list[str]
            Lista com os caminhos completos dos arquivos encontrados na
            estrutura FTP.

        Raises
        ------
        ValueError
            Se a URL FTP for inválida.
        """
        url_parseada = urlparse(url_ftp)
        host: str = url_parseada.hostname or ""
        caminho_pasta: str = unquote(url_parseada.path).rstrip("/")

        if not host:
            raise ValueError(f"URL FTP inválida: {url_ftp}")

        def montar_url_ftp(caminho_relativo: str) -> str:
            """
            Monta a URL FTP completa para um caminho relativo da estrutura.

            Parâmetros
            ----------
            caminho_relativo : str
                Caminho relativo do arquivo no servidor FTP.

            Retorno
            -------
            str
                URL FTP completa.
            """
            caminho_relativo_limpo: str = caminho_relativo.lstrip("/")
            return f"ftp://{host}/{caminho_relativo_limpo}"

        def listar_arquivos_ftp_recursivamente(
            ftp: ftplib.FTP,
            caminho_atual: str
        ) -> list[str]:
            """
            Lista recursivamente arquivos em um diretório FTP já conectado.

            Parâmetros
            ----------
            ftp : ftplib.FTP
                Conexão FTP já autenticada.
            caminho_atual : str
                Caminho atual a ser percorrido.

            Retorno
            -------
            list[str]
                Lista de URLs FTP dos arquivos encontrados.
            """
            arquivos_encontrados_local: list[str] = []

            try:
                for nome, fatos in ftp.mlsd(caminho_atual or "."):
                    tipo_item: str = fatos.get("type", "")
                    if nome in {".", ".."}:
                        continue

                    caminho_item: str = f"{caminho_atual}/{nome}" if caminho_atual else nome

                    if tipo_item == "file":
                        arquivos_encontrados_local.append(montar_url_ftp(caminho_item))
                    elif tipo_item == "dir":
                        arquivos_encontrados_local.extend(
                            listar_arquivos_ftp_recursivamente(ftp, caminho_item)
                        )

                return arquivos_encontrados_local

            except (ftplib.error_perm, AttributeError):
                diretorio_original: str = ftp.pwd()

                try:
                    if caminho_atual:
                        ftp.cwd(caminho_atual)

                    for nome in ftp.nlst():
                        nome_limpo: str = Path(nome).name

                        if nome_limpo in {".", ".."}:
                            continue

                        try:
                            ftp.cwd(nome_limpo)
                            subdiretorio: str = (
                                f"{caminho_atual}/{nome_limpo}"
                                if caminho_atual
                                else nome_limpo
                            )

                            arquivos_encontrados_local.extend(
                                listar_arquivos_ftp_recursivamente(ftp, subdiretorio)
                            )

                            ftp.cwd("..")

                        except ftplib.error_perm:
                            caminho_arquivo: str = (
                                f"{caminho_atual}/{nome_limpo}"
                                if caminho_atual
                                else nome_limpo
                            )
                            arquivos_encontrados_local.append(
                                montar_url_ftp(caminho_arquivo)
                            )

                finally:
                    ftp.cwd(diretorio_original)

                return arquivos_encontrados_local

        with ftplib.FTP(host, timeout=300) as ftp:
            ftp.login()
            return list(dict.fromkeys(listar_arquivos_ftp_recursivamente(ftp, caminho_pasta)))

    def listar_arquivos_http(
        url_pasta: str,
        urls_visitadas: Optional[set[str]] = None
    ) -> list[str]:
        """
        Lista arquivos disponíveis em uma página HTTP/HTTPS com links e,
        quando houver subpastas, percorre essas subpastas automaticamente.

        A função trata estruturas mistas com:
        - arquivos soltos na página atual;
        - subpastas contendo arquivos;
        - arquivos ZIP e arquivos tabulares suportados.

        Parâmetros
        ----------
        url_pasta : str
            URL HTTP/HTTPS da página de listagem.
        urls_visitadas : Optional[set[str]], opcional
            Conjunto interno de controle das URLs já visitadas durante a
            recursão. Quando não informado, é inicializado automaticamente.

        Retorno
        -------
        list[str]
            Lista com URLs completas dos arquivos encontrados na página
            informada e em suas subpastas.

        Raises
        ------
        requests.HTTPError
            Se ocorrer erro ao acessar alguma página HTTP/HTTPS.
        """
        if urls_visitadas is None:
            urls_visitadas = set()

        base_url: str = url_pasta if url_pasta.endswith("/") else f"{url_pasta}/"

        if base_url in urls_visitadas:
            return []

        urls_visitadas.add(base_url)

        resposta: requests.Response = requests.get(base_url, timeout=300)
        resposta.raise_for_status()

        soup = BeautifulSoup(resposta.text, "html.parser")
        arquivos_encontrados: list[str] = []

        url_base_parseada = urlparse(base_url)
        host_base: str = url_base_parseada.netloc

        for link in soup.find_all("a", href=True):
            href: str = link["href"].strip()

            if not href or href in {"../", "./", "/"}:
                continue

            if href.startswith("#") or href.startswith("?"):
                continue

            url_absoluta: str = urljoin(base_url, href)
            url_absoluta_parseada = urlparse(url_absoluta)

            if url_absoluta_parseada.netloc != host_base:
                continue

            caminho: str = url_absoluta_parseada.path
            nome_arquivo: str = Path(caminho).name

            if not nome_arquivo:
                continue

            if nome_deve_ser_ignorado(nome_arquivo):
                continue

            extensao: str = Path(nome_arquivo).suffix.lower()

            if extensao == ".zip" or extensao in extensoes_tabulares_suportadas:
                arquivos_encontrados.append(url_absoluta)
                continue

            eh_subpasta: bool = href.endswith("/") or caminho.endswith("/")

            if eh_subpasta:
                arquivos_encontrados.extend(
                    listar_arquivos_http(
                        url_pasta=url_absoluta,
                        urls_visitadas=urls_visitadas
                    )
                )

        return list(dict.fromkeys(arquivos_encontrados))

    def processar_zip_bytes(
        conteudo_zip: bytes,
        nome_origem_zip: str,
        grupo_mescla_padrao: Optional[str] = None
    ) -> tuple[list[pd.DataFrame], list[str], list[str], list[ErroLeitura]]:
        """
        Processa um conteúdo ZIP já carregado em memória, extraindo e lendo
        os arquivos compatíveis encontrados dentro dele.

        Os DataFrames extraídos recebem:
        - `arquivo_origem`
        - `grupo_mescla`

        Quando `grupo_mescla_padrao` é informado, todos os arquivos do ZIP
        herdam esse grupo. Isso é útil para manter juntos arquivos derivados
        de um mesmo ZIP cujo nome já define o agrupamento lógico, como:
        - AC_202401_HOSP_CONS.zip
        - AC_202401_HOSP_DET.zip
        - AC_202401_HOSP_REM.zip

        Parâmetros
        ----------
        conteudo_zip : bytes
            Conteúdo binário do arquivo ZIP.
        nome_origem_zip : str
            Nome do arquivo ZIP de origem, utilizado para rastreabilidade.
        grupo_mescla_padrao : Optional[str], opcional
            Grupo de mesclagem a ser aplicado aos arquivos extraídos do ZIP.

        Retorno
        -------
        tuple[list[pd.DataFrame], list[str], list[str], list[ErroLeitura]]
            Tupla contendo:
            - lista de DataFrames lidos
            - lista de arquivos lidos com sucesso
            - lista de arquivos ignorados
            - lista de erros
        """
        lista_dfs_local: list[pd.DataFrame] = []
        arquivos_lidos_local: list[str] = []
        arquivos_ignorados_local: list[str] = []
        erros_local: list[ErroLeitura] = []

        with ZipFile(BytesIO(conteudo_zip)) as arquivo_zip:
            for nome_arquivo in arquivo_zip.namelist():
                if nome_arquivo.endswith("/"):
                    continue

                if nome_deve_ser_ignorado(nome_arquivo):
                    arquivos_ignorados_local.append(nome_arquivo)
                    continue

                try:
                    with arquivo_zip.open(nome_arquivo) as arquivo:
                        conteudo_arquivo: bytes = arquivo.read()
                        df_temp: pd.DataFrame | None = ler_arquivo(conteudo_arquivo, nome_arquivo)

                        if df_temp is None:
                            arquivos_ignorados_local.append(nome_arquivo)
                            continue

                        grupo_mescla: str = obter_grupo_mescla(
                            nome_arquivo=nome_arquivo,
                            grupo_padrao=grupo_mescla_padrao
                        )

                        df_temp["arquivo_origem"] = f"{nome_origem_zip}::{nome_arquivo}"
                        df_temp["grupo_mescla"] = grupo_mescla
                        lista_dfs_local.append(df_temp)
                        arquivos_lidos_local.append(nome_arquivo)

                except Exception as erro:
                    erros_local.append(
                        {
                            "arquivo": nome_arquivo,
                            "erro": str(erro)
                        }
                    )

        return (
            lista_dfs_local,
            arquivos_lidos_local,
            arquivos_ignorados_local,
            erros_local
        )

    def salvar_csvs_por_grupo(dfs_por_grupo: dict[str, list[pd.DataFrame]]) -> None:
        """
        Salva um arquivo CSV por grupo de mesclagem na pasta atual de execução.

        O nome de cada arquivo segue o padrão:
        - `mescla_<GRUPO>.csv`

        Exemplo:
        - grupo `CONS` -> `mescla_CONS.csv`
        - grupo `DET`  -> `mescla_DET.csv`

        Se ocorrer erro ao salvar um grupo específico, o erro é registrado
        na lista `erros` e o processamento dos demais grupos continua.

        Parâmetros
        ----------
        dfs_por_grupo : dict[str, list[pd.DataFrame]]
            Dicionário em que cada chave é um grupo de mesclagem e cada valor
            é a lista de DataFrames pertencentes àquele grupo.
        """
        for grupo_atual, dfs_do_grupo in dfs_por_grupo.items():
            if not dfs_do_grupo:
                continue

            nome_arquivo_saida: str = (
                f"mescla_{normalizar_nome_arquivo_saida(grupo_atual)}.csv"
            )
            caminho_saida: Path = Path.cwd() / nome_arquivo_saida

            try:
                df_grupo: pd.DataFrame = pd.concat(dfs_do_grupo, ignore_index=True)
                df_grupo.to_csv(caminho_saida, index=False, encoding="utf-8-sig")
            except Exception as erro:
                erros.append(
                    {
                        "arquivo": nome_arquivo_saida,
                        "erro": f"Falha ao salvar CSV do grupo '{grupo_atual}': {erro}"
                    }
                )

    url_parseada = urlparse(url_zip)
    esquema: str = url_parseada.scheme.lower()
    extensao_url: str = Path(url_parseada.path).suffix.lower()

    conteudo_zip: bytes | None = None
    lista_dfs: list[pd.DataFrame] = []
    arquivos_lidos: list[str] = []
    arquivos_ignorados: list[str] = []
    erros: list[ErroLeitura] = []

    # Caso 1: a URL aponta diretamente para um arquivo ZIP
    if extensao_url == ".zip":
        nome_zip_principal: str = Path(url_parseada.path).name

        if nome_deve_ser_ignorado(nome_zip_principal):
            arquivos_ignorados.append(nome_zip_principal)
        else:
            conteudo_zip = baixar_arquivo_remoto(url_zip)
            grupo_zip_principal: str = obter_grupo_mescla(nome_zip_principal)

            (
                lista_dfs,
                arquivos_lidos,
                arquivos_ignorados,
                erros
            ) = processar_zip_bytes(
                conteudo_zip=conteudo_zip,
                nome_origem_zip=nome_zip_principal,
                grupo_mescla_padrao=grupo_zip_principal
            )

    # Caso 2: a URL aponta diretamente para um arquivo tabular compatível
    elif extensao_url in extensoes_tabulares_suportadas:
        nome_arquivo: str = Path(url_parseada.path).name

        if nome_deve_ser_ignorado(nome_arquivo):
            arquivos_ignorados.append(nome_arquivo)
        else:
            conteudo_arquivo: bytes = baixar_arquivo_remoto(url_zip)
            df_temp: pd.DataFrame | None = ler_arquivo(conteudo_arquivo, nome_arquivo)

            if df_temp is None:
                raise ValueError(f"Extensão não suportada: {nome_arquivo}")

            df_temp["arquivo_origem"] = nome_arquivo
            df_temp["grupo_mescla"] = obter_grupo_mescla(nome_arquivo)
            lista_dfs.append(df_temp)
            arquivos_lidos.append(nome_arquivo)

    # Caso 3: a URL aponta para uma pasta FTP
    elif esquema == "ftp":
        arquivos_remotos: list[str] = listar_arquivos_ftp(url_zip)

        for url_arquivo in arquivos_remotos:
            nome_arquivo_remoto: str = Path(urlparse(url_arquivo).path).name
            extensao_remota: str = Path(nome_arquivo_remoto).suffix.lower()

            if nome_deve_ser_ignorado(nome_arquivo_remoto):
                arquivos_ignorados.append(nome_arquivo_remoto)
                continue

            try:
                conteudo_arquivo = baixar_arquivo_remoto(url_arquivo)

                if extensao_remota == ".zip":
                    grupo_zip_remoto: str = obter_grupo_mescla(nome_arquivo_remoto)

                    (
                        dfs_zip,
                        arquivos_lidos_zip,
                        arquivos_ignorados_zip,
                        erros_zip
                    ) = processar_zip_bytes(
                        conteudo_zip=conteudo_arquivo,
                        nome_origem_zip=nome_arquivo_remoto,
                        grupo_mescla_padrao=grupo_zip_remoto
                    )

                    lista_dfs.extend(dfs_zip)
                    arquivos_lidos.extend(
                        [f"{nome_arquivo_remoto}::{nome}" for nome in arquivos_lidos_zip]
                    )
                    arquivos_ignorados.extend(
                        [f"{nome_arquivo_remoto}::{nome}" for nome in arquivos_ignorados_zip]
                    )
                    erros.extend(erros_zip)
                    continue

                df_temp = ler_arquivo(conteudo_arquivo, nome_arquivo_remoto)

                if df_temp is None:
                    arquivos_ignorados.append(nome_arquivo_remoto)
                    continue

                df_temp["arquivo_origem"] = nome_arquivo_remoto
                df_temp["grupo_mescla"] = obter_grupo_mescla(nome_arquivo_remoto)
                lista_dfs.append(df_temp)
                arquivos_lidos.append(nome_arquivo_remoto)

            except Exception as erro:
                erros.append(
                    {
                        "arquivo": nome_arquivo_remoto,
                        "erro": str(erro)
                    }
                )

    # Caso 4: a URL aponta para uma página HTTP/HTTPS com listagem de arquivos
    # ou subpastas contendo arquivos
    elif esquema in {"http", "https"}:
        arquivos_remotos: list[str] = listar_arquivos_http(url_zip)

        for url_arquivo in arquivos_remotos:
            nome_arquivo_remoto: str = Path(urlparse(url_arquivo).path).name
            extensao_remota: str = Path(nome_arquivo_remoto).suffix.lower()

            if nome_deve_ser_ignorado(nome_arquivo_remoto):
                arquivos_ignorados.append(nome_arquivo_remoto)
                continue

            try:
                conteudo_arquivo = baixar_arquivo_remoto(url_arquivo)

                if extensao_remota == ".zip":
                    grupo_zip_remoto: str = obter_grupo_mescla(nome_arquivo_remoto)

                    (
                        dfs_zip,
                        arquivos_lidos_zip,
                        arquivos_ignorados_zip,
                        erros_zip
                    ) = processar_zip_bytes(
                        conteudo_zip=conteudo_arquivo,
                        nome_origem_zip=nome_arquivo_remoto,
                        grupo_mescla_padrao=grupo_zip_remoto
                    )

                    lista_dfs.extend(dfs_zip)
                    arquivos_lidos.extend(
                        [f"{nome_arquivo_remoto}::{nome}" for nome in arquivos_lidos_zip]
                    )
                    arquivos_ignorados.extend(
                        [f"{nome_arquivo_remoto}::{nome}" for nome in arquivos_ignorados_zip]
                    )
                    erros.extend(erros_zip)
                    continue

                df_temp = ler_arquivo(conteudo_arquivo, nome_arquivo_remoto)

                if df_temp is None:
                    arquivos_ignorados.append(nome_arquivo_remoto)
                    continue

                df_temp["arquivo_origem"] = nome_arquivo_remoto
                df_temp["grupo_mescla"] = obter_grupo_mescla(nome_arquivo_remoto)
                lista_dfs.append(df_temp)
                arquivos_lidos.append(nome_arquivo_remoto)

            except Exception as erro:
                erros.append(
                    {
                        "arquivo": nome_arquivo_remoto,
                        "erro": str(erro)
                    }
                )

    else:
        raise ValueError(
            "URL não suportada. Informe uma URL de arquivo .zip, "
            "arquivo tabular compatível, pasta FTP ou página HTTP/HTTPS "
            "com listagem de arquivos."
        )

    if not lista_dfs:
        raise ValueError("Nenhum arquivo compatível foi encontrado ou lido com sucesso.")

    dfs_por_grupo: dict[str, list[pd.DataFrame]] = {}

    for df_temp in lista_dfs:
        if "grupo_mescla" in df_temp.columns and not df_temp.empty:
            grupo_atual: str = str(df_temp["grupo_mescla"].iloc[0])
        elif "grupo_mescla" in df_temp.columns:
            grupo_atual = "SEM_GRUPO"
        else:
            grupo_atual = "SEM_GRUPO"

        if grupo_atual not in dfs_por_grupo:
            dfs_por_grupo[grupo_atual] = []

        dfs_por_grupo[grupo_atual].append(df_temp)

    salvar_csvs_por_grupo(dfs_por_grupo)

    lista_dfs_agrupados: list[pd.DataFrame] = [
        pd.concat(dfs_do_grupo, ignore_index=True)
        for dfs_do_grupo in dfs_por_grupo.values()
        if dfs_do_grupo
    ]

    df_unificado: pd.DataFrame = pd.concat(lista_dfs_agrupados, ignore_index=True)

    return {
        "conteudo_zip": conteudo_zip,
        "arquivos_lidos": arquivos_lidos,
        "arquivos_ignorados": arquivos_ignorados,
        "erros": erros,
        "df_unificado": df_unificado
    }
    
def baixar_arquivo(url: str, nome_arquivo: Optional[str] = None) -> Path:
    """
    Baixa um arquivo a partir de uma URL e o salva na pasta atual de execução.

    Se `nome_arquivo` não for informado, o nome do arquivo será extraído
    automaticamente a partir do final da URL.

    Parâmetros
    ----------
    url : str
        URL do arquivo que será baixado.
    nome_arquivo : str | None, opcional
        Nome que será usado para salvar o arquivo localmente.
        Se não for informado, o nome será obtido a partir da URL.

    Retorno
    -------
    Path
        Caminho completo do arquivo salvo.

    Exceções
    --------
    requests.HTTPError
        Lançada se a requisição HTTP retornar erro.
    ValueError
        Lançada se não for possível determinar o nome do arquivo.
    """
    if nome_arquivo is None:
        nome_arquivo = url.rstrip("/").split("/")[-1]

    if not nome_arquivo:
        raise ValueError("Não foi possível determinar o nome do arquivo a partir da URL.")

    caminho_saida = Path.cwd() / nome_arquivo

    resposta = requests.get(url)
    resposta.raise_for_status()

    with open(caminho_saida, "wb") as arquivo:
        arquivo.write(resposta.content)

    return caminho_saida