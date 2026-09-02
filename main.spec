# -*- mode: python ; coding: utf-8 -*-
#
# Empacotamento do RevyCheck para Windows.
#
#     pyinstaller main.spec
#
# O executavel sai em dist/RevyCheck.exe.
#
# O binario NAO carrega segredo: a chave da API, a senha do DEV e as
# credenciais de SMB vem do `revycheck.env`, que fica ao lado do executavel
# e nao entra no bundle. Unica excecao: a URL da API e' embutida no boot via
# `revycheck_api_url_hook.py` (endereco nao e' segredo). Isso e' de
# proposito -- um bundle do PyInstaller e' trivialmente extraivel
# (`pyi-archive_viewer dist/RevyCheck.exe`), entao tudo que for compilado
# junto vaza. Rotacionar a chave passa a ser editar um arquivo no
# compartilhamento, sem rebuild.
#
# NAO adicione `revycheck.env` em `datas`. Docstring tambem viaja no .pyc, e
# comentario nao -- ou seja, segredo em docstring vira segredo publicado.
# Confira o build antes de publicar:
#
#     python scripts/verificar_bundle.py

a = Analysis(
    ['src\\main.py'],
    pathex=['.'],  # para que `from src import ...` resolva
    binaries=[],
    datas=[
        ('keycodes.json', '.'),
        ('assets', 'assets'),
    ],
    hiddenimports=[],
    runtime_hooks=[
        # Fixa REVYCHECK_API_URL=http://10.3.0.116/revy-check no boot do exe,
        # com precedencia de variavel de ambiente (vence revycheck.env).
        'revycheck_api_url_hook.py',
    ],
    hooksconfig={},
    hookspath=[],
    excludes=[
        # Backend do outro SO: importa pulsectl e so' existe no Linux.
        'src.hal.linux',
        'pulsectl',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='RevyCheck',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    # Sem console: o app roda em tela cheia na bancada, e a janela preta do
    # console apareceria por cima. Trocar para True ao depurar traceback.
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
