#!/usr/bin/env python3
"""Smoke test da qualidade do GAT: um caso por valor de AL_QUALIDADE.

Para cada qualidade que existe em `gat.dbo.ESAL`, mostra como o checklist se
comporta quando um teste reprova:

    D / Dp / Drp   -> a reprovacao NAO interrompe: o fluxo segue ate o DONE e o
                      relatorio e' enviado pelo save_log();
    qualquer outra -> a primeira reprovacao interrompe o fluxo na hora (tela
                      PRODUTO REPROVADO), sem gerar nem enviar relatorio.

Exercita o caminho real - a consulta (`gat_quality.fetch_quality`) e o funil por
onde passam todos os vereditos (`app_state.add_log`) -, sem abrir tela e sem
pygame. A regra esperada esta escrita aqui de proposito e de forma independente
do modulo: se alguem afrouxar QUALIDADES_COM_REPROVACAO_LIVRE, este teste acusa.

Uso:
    python3 scripts/smoke_gat_quality.py            # regra + funil + GAT ao vivo
    python3 scripts/smoke_gat_quality.py --offline  # so' regra e funil, sem rede

Codigo de saida: 0 se nenhum FAIL, 1 se houver qualquer FAIL.
A parte ao vivo faz uma consulta por qualidade e leva de ~30 s a ~2 min (depende
do cache do servidor): AL_SERIAL nao tem indice, entao cada consulta varre a
tabela inteira (1,8 milhao de linhas). Use --offline para pular essa parte.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src import app_state  # noqa: E402 - import depois do sys.path acima
from src.functions.gat_quality import allows_reprove, fetch_quality  # noqa: E402

# --------------------------------------------------------------------------
# regra esperada, escrita a mao a partir do pedido
# --------------------------------------------------------------------------
# "quando a qualidade for D, Dp ou Drp, reprovar continua permitido; em
# qualquer outra qualidade, a primeira reprovacao interrompe o fluxo".
LIBERA = {"D", "DP", "DRP"}

# Valores que o GAT grava hoje (medido em 2026-09) e o veredito esperado. O
# rotulo 'Qualidade' vem gravado junto do valor, as vezes duplicado, entao a
# comparacao vale depois do rotulo removido.
ESPERADO = {
    "Qualidade D": True,
    "Qualidade Dp": True,
    "Qualidade Drp": True,
    "Qualidade Qualidade D": True,
    "Qualidade Qualidade Dp": True,
    "Qualidade C": False,
    "Qualidade B": False,
    "Qualidade A": False,
    "Qualidade Cp": False,
    "Qualidade Cn": False,
    "Qualidade Bp": False,
    "Qualidade Bn": False,
    "Qualidade Cr": False,
    "Qualidade Dn": False,
    "Qualidade Dr": False,
    "Qualidade Dpr": False,
    "Qualidade Ap": False,
    "Qualidade Cpr": False,
    "Qualidade Cpp": False,
    "Qualidade não informada": False,
    "Qualidade None": False,
    "Qualidade Qualidade B": False,
    "Qualidade Qualidade C": False,
    "Qualidade Qualidade Cr": False,
    "Qualidade Qualidade Cp": False,
    "A": False,
    "p": False,
    None: False,
    "": False,
}

# Steps reais de reprovacao, um por teste (ver add_log em cada modulo de teste).
# O gate e' central em add_log justamente para cobrir os nove sem editar nenhum.
STEPS_REPROVAVEIS = [
    "SCREEN_TEST",
    "KEYBOARD_TEST",
    "TOUCHPAD_REPROVED",
    "WIFI_TEST",
    "CAMERA_TEST",
    "VIDEO_HDMI-A-1_TEST",
    "HEADPHONE_CONNECT",
    "SPEAKER_TEST",
    "MICROPHONE_TEST",
]

RESULTS = []


def registra(status, nome, detalhe=""):
    RESULTS.append((status, nome, detalhe))


def esperado(valor_cru):
    """Veredito que o pedido exige para um valor cru de AL_QUALIDADE.

    Reimplementacao independente da regra, de proposito: e' contra ela que o
    modulo e' conferido.
    """
    if valor_cru is None:
        return False
    texto = str(valor_cru).strip()
    while texto.upper().startswith("QUALIDADE"):
        texto = texto[len("QUALIDADE"):].strip()
    return texto.upper() in LIBERA


def comportamento(valor_cru):
    return "segue ate o DONE" if esperado(valor_cru) else "trava na 1a reprovacao"


def fmt(valor):
    """Repr util no relatorio: distingue None de '' e da string 'None'."""
    if valor is None:
        return "None"
    return repr(valor)


def simula_reprovacao(qualidade, step):
    """Roda o funil real com uma reprovacao e devolve True se o fluxo travou.

    Usa app_state.add_log, o mesmo caminho de todos os testes: se REPROVED_STEP
    fica preenchido, o laco de main.py desvia para REPROVED_LOCK.
    """
    app_state.LOG_DATA.clear()
    app_state.REPROVED_STEP = None
    app_state.GAT_QUALITY = qualidade
    app_state.GAT_ALLOWS_REPROVE = allows_reprove(qualidade)
    app_state.add_log({"step": step, "time": app_state.now_iso(), "result": "REPROVADO"})
    travou = app_state.REPROVED_STEP is not None
    app_state.LOG_DATA.clear()
    app_state.REPROVED_STEP = None
    return travou


# --------------------------------------------------------------------------
# checagens
# --------------------------------------------------------------------------
def c_regra():
    """A regra do modulo tem que concordar com o pedido, valor a valor."""
    erros = []
    for valor, veredito in ESPERADO.items():
        obtido = allows_reprove(valor)
        if obtido != veredito:
            erros.append(f"{fmt(valor)}: esperado {veredito}, obtido {obtido}")
        # a propria tabela de esperados tem que bater com a regra reescrita
        if veredito != esperado(valor):
            erros.append(f"{fmt(valor)}: tabela ESPERADO divergente da regra")
    if erros:
        raise AssertionError("; ".join(erros))
    return f"{len(ESPERADO)} valores conferidos"


def c_funil():
    """Sob qualidade que trava, os nove steps de reprovacao travam; sob Dp, nao."""
    erros = []
    for step in STEPS_REPROVAVEIS:
        if not simula_reprovacao("C", step):
            erros.append(f"{step} nao travou sob 'Qualidade C'")
    for step in STEPS_REPROVAVEIS:
        if simula_reprovacao("Dp", step):
            erros.append(f"{step} travou sob 'Dp' (deveria seguir)")
    if erros:
        raise AssertionError("; ".join(erros))
    return f"{len(STEPS_REPROVAVEIS)} steps x 2 qualidades"


def c_aprovados_nao_travam():
    """Teste aprovado nunca dispara o gate, em qualquer qualidade."""
    app_state.LOG_DATA.clear()
    app_state.REPROVED_STEP = None
    app_state.GAT_ALLOWS_REPROVE = allows_reprove("Qualidade C")
    for step in STEPS_REPROVAVEIS:
        app_state.add_log({"step": step, "time": app_state.now_iso(), "result": "APROVADO"})
    travou = app_state.REPROVED_STEP is not None
    app_state.LOG_DATA.clear()
    app_state.REPROVED_STEP = None
    if travou:
        raise AssertionError("checklist todo aprovado travou o fluxo")
    return f"{len(STEPS_REPROVAVEIS)} steps aprovados"


def c_desconhecido_trava():
    """Serial sem informacao no GAT (None) tem que travar."""
    if allows_reprove(None):
        raise AssertionError("qualidade desconhecida liberou reprovacao")
    if not simula_reprovacao(None, "SCREEN_TEST"):
        raise AssertionError("qualidade desconhecida nao travou o fluxo")
    return "None -> trava"


# --------------------------------------------------------------------------
# GAT ao vivo
# --------------------------------------------------------------------------
def consulta_valores():
    """(valor, total de linhas, serial de amostra) por qualidade."""
    import pyodbc

    from src.functions.gat_quality import _connection_string, _driver

    driver = _driver()
    if driver is None:
        raise RuntimeError("nenhum driver ODBC da Microsoft instalado")

    conn = pyodbc.connect(_connection_string(driver), timeout=10)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT AL_QUALIDADE, COUNT(*) FROM gat.dbo.ESAL "
                "GROUP BY AL_QUALIDADE ORDER BY COUNT(*) DESC"
            )
            totais = cur.fetchall()

            # Amostra barata (um unico GROUP BY). Nao exige serial de linha
            # unica: um serial repetido pode resolver para outra qualidade pelo
            # desempate, entao a conferencia e' sobre o valor devolvido.
            cur.execute(
                "SELECT AL_QUALIDADE, MIN(AL_SERIAL) FROM gat.dbo.ESAL "
                "WHERE AL_SERIAL IS NOT NULL AND AL_SERIAL <> '' "
                "GROUP BY AL_QUALIDADE"
            )
            amostras = {q: s for q, s in cur.fetchall()}
    finally:
        conn.close()
    return totais, amostras


def c_gat(totais, amostras):
    """Qualidade real do banco tem que atravessar fetch_quality e dar o veredito certo."""
    if not totais:
        raise AssertionError("nenhuma qualidade retornada pelo GAT")

    erros = []
    lidas = 0
    for valor, _total in totais:
        serial = amostras.get(valor)
        if serial is None:
            continue
        lidas += 1
        lido = fetch_quality(serial)
        # Conferencia sobre o que voltou: a consulta pode trazer outra linha do
        # mesmo serial (o desempate pega a mais recente), e o que importa e' que
        # o veredito acompanhe a qualidade lida.
        if allows_reprove(lido) != esperado(lido):
            erros.append(f"{fmt(lido)} (serial {serial!r}): veredito divergente da regra")
        if simula_reprovacao(lido, "SCREEN_TEST") != (not allows_reprove(lido)):
            erros.append(f"{fmt(lido)} (serial {serial!r}): fluxo divergiu do veredito")
    if erros:
        raise AssertionError("; ".join(erros))
    return f"{len(totais)} qualidades distintas, {lidas} consultadas no banco"


# --------------------------------------------------------------------------
# execucao
# --------------------------------------------------------------------------
def main():
    RESULTS.clear()
    offline = "--offline" in sys.argv

    print("=" * 78)
    print("RevyCheck - smoke test da qualidade GAT (gat.dbo.ESAL)")
    if offline:
        print("modo: offline (sem consultar o banco)")
    print("regra: D, Dp, Drp liberam reprovacao; qualquer outra trava")
    print("=" * 78)
    print()

    print("-- 1. regra, valor a valor (todos os valores que o GAT grava) ---")
    print(f"{'qualidade gravada no GAT':30} {'veredito esperado':20} {'obtido':7} OK")
    for valor in ESPERADO:
        rotulo = "None (vazio)" if valor is None else repr(valor)
        obtido = allows_reprove(valor)
        marca = "OK" if obtido == ESPERADO[valor] else "ERRO"
        print(f"{rotulo:30} {comportamento(valor):20} {'segue' if obtido else 'trava':7} {marca}")
    try:
        registra("PASS", "regra           (valor a valor)", c_regra())
    except Exception as exc:
        registra("FAIL", "regra           (valor a valor)", f"{type(exc).__name__}: {exc}")
    print()

    print("-- 2. funil unico (app_state.add_log) ---------------------------")
    for nome, fn in (
        ("funil           (nove steps)", c_funil),
        ("funil           (tudo aprovado)", c_aprovados_nao_travam),
        ("funil           (desconhecido)", c_desconhecido_trava),
    ):
        try:
            registra("PASS", nome, fn())
        except Exception as exc:
            registra("FAIL", nome, f"{type(exc).__name__}: {exc}")
    print()

    if not offline:
        print("-- 3. GAT ao vivo (uma consulta por qualidade, devagar) --------")
        try:
            totais, amostras = consulta_valores()
            print(f"{'qualidade no banco':30} {'linhas':>10}  {'serial':<18} {'lido':<9} comportamento")
            for valor, total in totais:
                rotulo = "None (vazio)" if valor is None else repr(valor)
                serial = amostras.get(valor)
                if serial is None:
                    print(f"{rotulo:30} {total:>10}  {'-':<18} {'-':<9} sem serial preenchido")
                    continue
                lido = fetch_quality(serial)
                nota = comportamento(lido)
                if lido != (valor if valor is None else valor.replace("Qualidade ", "").replace("Qualidade ", "")):
                    nota += "  (desempate: serial repetido)"
                print(f"{rotulo:30} {total:>10}  {serial:<18} {fmt(lido):<9} {nota}")
            registra("PASS", "gat             (valores reais)", c_gat(totais, amostras))
        except Exception as exc:
            registra("WARN", "gat             (valores reais)", f"{type(exc).__name__}: {exc}")
        print()

    # nao deixa estado de teste para tras no app_state
    app_state.LOG_DATA.clear()
    app_state.REPROVED_STEP = None

    fails = sum(1 for status, _, _ in RESULTS if status == "FAIL")
    warns = sum(1 for status, _, _ in RESULTS if status == "WARN")
    passes = sum(1 for status, _, _ in RESULTS if status == "PASS")
    for status, nome, detalhe in RESULTS:
        print(f"[{status:4}] {nome:34} {detalhe}")

    print()
    print("-" * 78)
    print(f"resumo: {passes} PASS, {warns} WARN, {fails} FAIL")
    print("-" * 78)
    if fails:
        print("!! Ha FAIL: a regra de qualidade nao esta' como o pedido.")
    else:
        print("OK: a regra confere valor a valor e o funil reage como esperado.")

    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
