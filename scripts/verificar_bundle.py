#!/usr/bin/env python3
"""Confere que o .exe empacotado nao leva segredo nenhum dentro.

Bundle do PyInstaller e' arquivo, nao cofre: `pyi-archive_viewer
dist/RevyCheck.exe` lista e extrai tudo que entrou, e docstring/comentario
viaja junto com o .pyc. Entao nao basta olhar `datas` no .spec -- o segredo
pode ter entrado por um literal esquecido no fonte.

Este script abre o CArchive do .exe (e o PYZ que mora dentro dele),
descompacta cada entrada e procura os *valores* que estao no `revycheck.env`,
nao o nome das variaveis. Se um valor aparecer, ele esta no binario e vaza com
o binario.

Uso:

    python scripts/verificar_bundle.py                 # dist/RevyCheck.exe
    python scripts/verificar_bundle.py caminho/App.exe

Codigo de saida: 0 se o bundle esta limpo, 1 se algum valor vazou (ou se o
arquivo nao e' um bundle PyInstaller). Nenhum valor de segredo e' impresso.
"""

import marshal
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Cookie no fim do .exe: magico, tamanho do CArchive, offset/tamanho da TOC,
# versao do Python e nome da libpython. Formato estavel do PyInstaller.
COOKIE_MAGIC = b"MEI\014\013\012\013\016"
COOKIE_FMT = "!8sIIii64s"
COOKIE_LEN = struct.calcsize(COOKIE_FMT)
TOC_ENTRY_FMT = "!iIIIBc"
TOC_ENTRY_LEN = struct.calcsize(TOC_ENTRY_FMT)


def segredos(caminho_env):
    """Valores nao vazios do revycheck.env. Sao eles que nao podem estar no exe."""
    valores = {}
    if not caminho_env.is_file():
        return valores
    for linha in caminho_env.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, _, valor = linha.partition("=")
        valor = valor.strip().strip('"').strip("'")
        if valor:
            valores[chave.strip()] = valor.encode("utf-8")
    return valores


def entradas_carchive(bruto):
    """Uma tupla (nome, bytes descompactados) por entrada do CArchive."""
    fim = bruto.rfind(COOKIE_MAGIC)
    if fim < 0:
        raise ValueError("nao e' um bundle PyInstaller (cookie MEI ausente)")

    _, len_arquivo, toc_off, toc_len, _, _ = struct.unpack(
        COOKIE_FMT, bruto[fim:fim + COOKIE_LEN]
    )
    inicio = len(bruto) - len_arquivo
    pos = inicio + toc_off
    limite = pos + toc_len

    while pos < limite:
        tam_entrada, dpos, dlen, _ulen, comprimido, _tipo = struct.unpack(
            TOC_ENTRY_FMT, bruto[pos:pos + TOC_ENTRY_LEN]
        )
        nome = bruto[pos + TOC_ENTRY_LEN:pos + tam_entrada]
        nome = nome.rstrip(b"\x00").decode("utf-8", "replace")
        dados = bruto[inicio + dpos:inicio + dpos + dlen]
        if comprimido:
            try:
                dados = zlib.decompress(dados)
            except zlib.error:
                pass  # entrada nao-zlib: procura no bruto mesmo
        yield nome, dados
        pos += tam_entrada


def entradas_pyz(dados):
    """Modulos de dentro do PYZ. Cada um e' zlib separado, entao precisa abrir."""
    _magico, _py_magico, toc_off = struct.unpack("!4s4sI", dados[:12])
    toc = marshal.loads(dados[toc_off:])
    itens = toc.items() if isinstance(toc, dict) else toc
    for nome, (_tipo, off, tam) in itens:
        pedaco = dados[off:off + tam]
        try:
            pedaco = zlib.decompress(pedaco)
        except zlib.error:
            pass
        yield nome, pedaco


def main():
    exe = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "dist" / "RevyCheck.exe"
    if not exe.is_file():
        print(f"FAIL  {exe} nao existe. Rode `pyinstaller main.spec` primeiro.")
        return 1

    valores = segredos(ROOT / "revycheck.env")
    if not valores:
        print("WARN  revycheck.env sem valores preenchidos: nada para comparar.")

    bruto = exe.read_bytes()
    try:
        entradas = list(entradas_carchive(bruto))
    except (ValueError, struct.error) as exc:
        print(f"FAIL  {exe.name}: {exc}")
        return 1

    # Alvo 1: arquivo de config empacotado. Nunca deve entrar no bundle.
    empacotados = [n for n, _ in entradas if n.lower().endswith(".env")]

    # Alvo 2: valor de segredo em qualquer entrada, inclusive dentro do PYZ.
    vazamentos = []
    for nome, dados in entradas:
        alvos = [(nome, dados)]
        if nome.lower().endswith(".pyz"):
            try:
                alvos.extend(("PYZ:" + m, d) for m, d in entradas_pyz(dados))
            except (ValueError, struct.error, EOFError) as exc:
                print(f"WARN  PYZ {nome} ilegivel ({exc}); conteudo nao verificado.")
        for rotulo, blob in alvos:
            for chave, valor in valores.items():
                if valor in blob:
                    vazamentos.append((chave, rotulo))

    print(f"exe        {exe} ({len(bruto) // 1024} KiB)")
    print(f"entradas   {len(entradas)}")
    print(f"config     {'FAIL ' + ', '.join(empacotados) if empacotados else 'OK nenhum .env no bundle'}")
    for chave in valores:
        onde = [r for c, r in vazamentos if c == chave]
        print(f"{chave:24} {'FAIL vazou em ' + ', '.join(sorted(set(onde))) if onde else 'OK ausente do binario'}")

    if empacotados or vazamentos:
        print("\nFAIL  nao publique este build. Tire o valor do fonte e rotacione o "
              "que vazou -- o binario ja pode ter circulado.")
        return 1
    print("\nOK    bundle sem segredo. A config vem do revycheck.env ao lado do .exe.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
