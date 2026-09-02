"""Qualidade do equipamento, lida do csireporting.

`resumogeral.Qualidade` guarda a grade com sufixo opcional de reparo ('C', 'Cr',
'Dp', 'Drp'): a primeira letra e' a grade, o resto e' detalhe. O vinculo com o
equipamento na bancada e' `TagSerial` = serial do DMI.
"""

import mysql.connector

# Unica grade que segue o teste com etapa reprovada (equipamento de sucata/peca).
EXEMPT_GRADE = "D"

# Serial que o DMI nao soube ler: nao tem o que consultar.
_INVALID_SERIALS = {"", "-", "N/A", "unknown", "none", "to be filled by o.e.m."}


def fetch_quality(serial):
    """Valor bruto de `Qualidade` para o serial, ou None quando indisponivel.

    Devolve None em vez de estourar quando o serial nao esta' no csireporting ou
    o banco esta' fora - a bancada nao pode parar por causa disso. Quem decide o
    que fazer com o desconhecido e' `audio_failure_blocks`.
    """
    if not serial or serial.strip().lower() in _INVALID_SERIALS:
        return None

    conn = None
    try:
        conn = mysql.connector.connect(
            host="10.3.0.12",
            user="drack",
            password="jdVg2dF2@",
            database="csireporting",
            connection_timeout=5,
        )
        with conn.cursor(dictionary=True, buffered=True) as cursor:
            # TagSerial nao e' chave (121k linhas / 106k seriais distintos) e a
            # maioria das entradas nao tem grade: fica a que tem, e no empate a
            # de RG maior, que e' a entrada mais recente do equipamento.
            cursor.execute(
                "SELECT Qualidade FROM resumogeral "
                "WHERE TagSerial=%s AND Qualidade IS NOT NULL "
                "AND Qualidade NOT IN ('', 'None') "
                "ORDER BY RGMicroexato DESC LIMIT 1",
                (serial.strip(),),
            )
            row = cursor.fetchone()
    except Exception as exc:
        print(f"AVISO: qualidade indisponivel ({type(exc).__name__}: {exc}).")
        return None
    finally:
        if conn is not None:
            conn.close()

    if not row or not row["Qualidade"]:
        return None
    return row["Qualidade"].strip()


def grade_letter(quality):
    """Letra da grade ('Cr' -> 'C'), ou None quando nao ha' grade."""
    if not quality:
        return None
    letter = quality.strip()[:1].upper()
    return letter if letter.isalpha() else None


def blocks_failure(quality):
    """True quando uma etapa reprovada deve travar o teste.

    So' equipamento qualidade D continua com etapa reprovada. Grade desconhecida
    trava: e' mais seguro mandar para conferencia do que aprovar um A/B/C com
    defeito.
    """
    return grade_letter(quality) != EXEMPT_GRADE
