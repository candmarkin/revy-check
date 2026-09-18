"""Qualidade do produto no GAT.

O GAT nao expoe API: a qualidade vive no SQL Server da vistoria (base `gat`,
tabela `dbo.ESAL`), acessado via pyodbc. A bancada precisa tanto do pacote
`pyodbc` (entra pelo requirements.txt) quanto do driver ODBC da Microsoft
instalado no sistema (`msodbcsql18`). Sem driver a consulta devolve None e cai
na politica de TRAVA_QUANDO_DESCONHECIDA, em vez de derrubar a bancada.
"""

try:
    import pyodbc
except ImportError:  # bancada sem pyodbc nao pode morrer no import
    pyodbc = None

# Qualidades que permitem concluir o checklist com teste reprovado.
QUALIDADES_COM_REPROVACAO_LIVRE = frozenset({"D", "DP", "DRP", "Dr", "Dn", "Dpr"})

# 56,8% das linhas de ESAL tem AL_QUALIDADE NULL (1.031.837 de 1.816.972,
# medido em 2026-09). Tratar desconhecido como "pode reprovar" deixaria o
# travamento sem efeito pratico, entao o padrao e' travar.
TRAVA_QUANDO_DESCONHECIDA = True

_SERVIDOR = "10.3.0.12"
_PORTA = 1433
_BANCO = "gat"
_USUARIO = "revy_readonly"
_SENHA = "jdVg2dF2"

# Nomes diferentes entre Windows (desenvolvimento) e a bancada Debian, onde o
# pacote da Microsoft registra o mesmo driver. O primeiro instalado vence.
_DRIVERS_PREFERIDOS = (
    "ODBC Driver 18 for SQL Server",
    "ODBC Driver 17 for SQL Server",
    "SQL Server",
)

# AL_SERIAL nao tem indice e nao e' unico (1,8 milhao de linhas; 1.002 serials
# tem mais de uma linha, com qualidade divergente entre elas). O desempate
# pega o registro mais recente, que e' o estado atual da unidade: se o registro
# novo ainda nao tem qualidade, trava, em vez de ressuscitar uma qualidade
# antiga permissiva. AL_CODIGO/AL_COD_FILIAL so' fecham empate de data.
_SQL = (
    "SELECT TOP 1 AL_QUALIDADE FROM gat.dbo.ESAL "
    "WHERE AL_SERIAL = ? "
    "ORDER BY AL_DAT_ULT_ALT DESC, AL_CODIGO DESC, AL_COD_FILIAL DESC"
)

# O GAT grava o rotulo junto do valor ('Qualidade Dp'), as vezes duplicado
# ('Qualidade Qualidade B'): 99,7% das linhas preenchidas vem assim (782.971
# de 785.135), entao comparar com 'Dp' cru nunca casaria e travaria tudo.
_PREFIXO = "QUALIDADE"
_SEM_INFORMACAO = ("", "NULL", "NONE", "NAO INFORMADA", "NÃO INFORMADA")


def _driver():
    """Nome do driver ODBC instalado, ou None se a maquina nao tem nenhum."""
    if pyodbc is None:
        return None
    try:
        instalados = pyodbc.drivers()
    except Exception:
        return None
    for driver in _DRIVERS_PREFERIDOS:
        if driver in instalados:
            return driver
    return None


def _connection_string(driver):
    return (
        f"DRIVER={{{driver}}};SERVER={_SERVIDOR},{_PORTA};DATABASE={_BANCO};"
        f"UID={_USUARIO};PWD={_SENHA};TrustServerCertificate=yes"
    )


def _normalizar(valor):
    """Tira o rotulo 'Qualidade' (repetido ou nao) e devolve o valor limpo."""
    if valor is None:
        return None
    texto = str(valor).strip()
    while texto.upper().startswith(_PREFIXO):
        texto = texto[len(_PREFIXO):].strip()
    return texto or None


def fetch_quality(serial):
    """Qualidade do GAT para o serial, ou None quando nao ha' informacao.

    Devolve o valor ja' sem o rotulo ('Dp', 'C'), que e' o que o HUD e o log
    exibem. Nunca levanta: erro de consulta devolve None e cai na politica de
    TRAVA_QUANDO_DESCONHECIDA, em vez de derrubar a bancada com traceback.
    """
    if not serial or serial == "N/A":
        return None

    driver = _driver()
    if driver is None:
        return None

    conn = None
    try:
        # timeout e' o login timeout do ODBC; a consulta em si varre a tabela
        # sem indice (~1-2 s, 8 s na primeira com o cache frio).
        conn = pyodbc.connect(_connection_string(driver), timeout=10)
        with conn.cursor() as cursor:
            cursor.execute(_SQL, (serial,))
            row = cursor.fetchone()
    except Exception:
        return None
    finally:
        if conn is not None:
            conn.close()

    return _normalizar(row[0] if row else None)


def allows_reprove(quality):
    """True quando a qualidade do GAT permite concluir com teste reprovado."""
    normalizada = _normalizar(quality)
    if normalizada is None or normalizada.upper() in _SEM_INFORMACAO:
        return not TRAVA_QUANDO_DESCONHECIDA
    return normalizada.upper() in QUALIDADES_COM_REPROVACAO_LIVRE
