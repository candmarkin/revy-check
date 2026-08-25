# -*- mode: python ; coding: utf-8 -*-
#
# Empacotamento do RevyCheck para Windows.
#
#     pyinstaller main.spec
#
# O executavel sai em dist/RevyCheck.exe.
#
# ATENCAO antes de distribuir: as credenciais do MySQL e do SMB estao no
# codigo-fonte. Um bundle do PyInstaller e' trivialmente extraivel
# (`pyi-archive_viewer dist/RevyCheck.exe`), entao o .exe carrega as senhas em
# claro para toda maquina onde for instalado. Ver a secao de seguranca do
# WINDOWS.md.

a = Analysis(
    ['src\\main.py'],
    pathex=['.'],  # para que `from src import ...` resolva
    binaries=[],
    datas=[
        ('keycodes.json', '.'),
        ('assets', 'assets'),
    ],
    hiddenimports=[
        # O mysql-connector carrega os plugins de autenticacao e as locales por
        # nome, em runtime: o PyInstaller nao os enxerga na analise estatica e o
        # .exe morre no primeiro connect com "Authentication plugin ... not
        # supported".
        'mysql.connector.plugins',
        'mysql.connector.plugins.mysql_native_password',
        'mysql.connector.plugins.caching_sha2_password',
        'mysql.connector.locales.eng.client_error',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
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
