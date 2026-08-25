"""Envio de arquivo para compartilhamento SMB no Windows.

O backend Linux monta o share com `mount -t cifs`, o que exige sudo. No Windows
o proprio SO fala SMB: basta autenticar a sessao com `WNetAddConnection2` e
copiar para o caminho UNC como se fosse um diretorio local. Sem privilegio de
administrador e sem dependencia externa.
"""

import ctypes
import shutil
from ctypes import wintypes
from pathlib import Path

mpr = ctypes.WinDLL("mpr", use_last_error=True)

NO_ERROR = 0
ERROR_SESSION_CREDENTIAL_CONFLICT = 1219

RESOURCETYPE_DISK = 0x00000001


class _NETRESOURCE(ctypes.Structure):
    _fields_ = [
        ("dwScope", wintypes.DWORD),
        ("dwType", wintypes.DWORD),
        ("dwDisplayType", wintypes.DWORD),
        ("dwUsage", wintypes.DWORD),
        ("lpLocalName", wintypes.LPWSTR),
        ("lpRemoteName", wintypes.LPWSTR),
        ("lpComment", wintypes.LPWSTR),
        ("lpProvider", wintypes.LPWSTR),
    ]


def _connect(unc_share, username, password):
    resource = _NETRESOURCE()
    resource.dwType = RESOURCETYPE_DISK
    resource.lpLocalName = None  # sem letra de unidade: so' autentica a sessao
    resource.lpRemoteName = unc_share
    resource.lpProvider = None

    rc = mpr.WNetAddConnection2W(ctypes.byref(resource), password, username, 0)
    if rc == NO_ERROR:
        return True, None
    if rc == ERROR_SESSION_CREDENTIAL_CONFLICT:
        # Ja' existe sessao para este servidor, possivelmente com outro usuario.
        # Reaproveitar e' o comportamento util: o Windows nao permite duas.
        return True, None
    return False, f"WNetAddConnection2 falhou ({rc})"


def _disconnect(unc_share):
    mpr.WNetCancelConnection2W(unc_share, 0, True)


def upload(local_path, server, share, username, password, remote_path=""):
    """Copia `local_path` para //server/share/remote_path/."""
    local_path = Path(local_path)
    if not local_path.is_file():
        return False, "Nenhuma foto para enviar"
    if not all([server, share, username, password]):
        return False, "Configuração SMB incompleta"

    # `share` vem no formato Linux ('publico/Relatorios/...'); a conexao e'
    # feita no primeiro componente, que e' o compartilhamento de verdade.
    parts = [p for p in str(share).replace("\\", "/").split("/") if p]
    unc_share = rf"\\{server}\{parts[0]}"

    ok, error = _connect(unc_share, username, password)
    if not ok:
        return False, error

    try:
        target_dir = Path(unc_share).joinpath(*parts[1:])
        if remote_path:
            target_dir = target_dir.joinpath(
                *[p for p in str(remote_path).replace("\\", "/").split("/") if p]
            )
        target_dir.mkdir(parents=True, exist_ok=True)

        destination = target_dir / local_path.name
        shutil.copy2(local_path, destination)
        return True, f"Foto enviada para {destination}"
    except OSError as exc:
        return False, f"Erro ao enviar para SMB: {exc}"
    finally:
        _disconnect(unc_share)
