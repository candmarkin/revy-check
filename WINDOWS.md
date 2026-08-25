# Porte para Windows (Python/Pygame)

O `revy-check` roda em Windows 10/11 com **todos** os testes atuais: USB por
porta física, vídeo, áudio, ethernet, wifi, câmera, tela, teclado e touchpad.
A mesma árvore roda em Debian, sem fork.

Como usar: seção "Instalação (Windows 10/11)" do [README](README.md).
Este documento explica **como** cada teste foi portado e o que ficou em aberto.

Validado em Dell OptiPlex 7080, Windows 11 Pro 26200, Python 3.10.11:
`scripts/smoke_test.py` fecha com 13 PASS.

---

## 1. Estrutura: camada de hardware

A detecção de hardware saiu de dentro dos passos e foi para `src/hal/`:

```
src/hal/
    __init__.py       escolhe o backend por sys.platform e reexporta a API
    linux.py          sysfs, procfs, iw/nmcli, PulseAudio
    windows.py        fachada do backend Windows
    _win_cfgmgr.py    device tree (cfgmgr32) -- o "sysfs" do Windows
    _win_usb.py       portas USB físicas
    _win_display.py   saídas de vídeo (CCD API)
    _win_audio.py     estado do jack (registro MMDevices)
    _win_net.py       adaptadores de rede (registro + psutil)
    _win_wifi.py      Native Wifi API (wlanapi)
    _win_smb.py       envio de foto por SMB
    _win_kiosk.py     trava de atalhos (hook WH_KEYBOARD_LL)
```

`src/functions/` ficou só com os passos e a interface. A lista de nomes em
`src/hal/__init__.py` **é** a interface: um backend que não implementar tudo
quebra no import, e não no meio de um teste na bancada.

O pacote se chama `hal` e não `platform` de propósito: `python src/main.py`
coloca `src/` no `sys.path[0]`, e um pacote chamado `platform` sombrearia o
módulo `platform` da biblioteca padrão para o processo inteiro.

`src/functions/hw_paths.py` foi absorvido por `src/hal/linux.py`.

---

## 2. USB por porta física

`DEVPKEY_Device_LocationPaths`, lido do `cfgmgr32.dll`, descreve o caminho
físico no device tree — mesma propriedade de estabilidade do sysfs:

```
Linux    0000:00:14.0/3.2
Windows  PCIROOT(0)#PCI(1400)#USBROOT(0)#USB(3)#USB(2)
```

O `USBROOT(0)` é descartado: é o hub raiz do controlador, equivalente ao número
de bus que o backend Linux também joga fora porque muda entre boots.

`Class=Mass Storage` (`bInterfaceClass == 08`) vira `DEVPKEY_Device_Service ==
"USBSTOR"`. Confirmado no registro desta bancada — os nós `USB\VID_...` de
pendrives já vistos carregam `Service = USBSTOR` e `DeviceDesc = USB Mass
Storage Device`.

As interfaces de dispositivo composto (`...&MI_00`) entram no mesmo registro de
porta em vez de serem descartadas: em pendrive com emulação de CD quem carrega
o `USBSTOR` é a interface, e o pai aparece como `USBCCGP`. O USBSTOR de
qualquer nó da porta vence.

O painel do chassi (ACPI `_PLD`, `physical_location/panel` no Linux) não tem
equivalente. O mais próximo é o segundo location path, em formato ACPI
(`...#ACPI(RHUB)#ACPI(HS10)`), usado só como dica visual no cadastro.

**Descartados:** `pyusb`/`libusb` exigem trocar o driver da porta por WinUSB
(Zadig) e não suportam hotplug no Windows. `Get-PnpDeviceProperty` custaria um
subprocess PowerShell por dispositivo.

## 3. Vídeo

`QueryDisplayConfig` com `QDC_ALL_PATHS`. O flag é o ponto todo: além dos
monitores ativos ele enumera os alvos **desconectados**, sem os quais "conecte
o monitor na porta X" não teria o que esperar. `targetInfo.targetAvailable` é o
`status == "connected"` do DRM.

O identificador gravado no banco combina tecnologia, `connectorInstance` e
`target_id`: `DISPLAYPORT-0#200195`.

> O `target_id` entra na chave porque `(tecnologia, connectorInstance)` **não**
> é único em máquina com mais de uma GPU. Nesta bancada apareceram dois
> `DISPLAYPORT-0`, com target 4352 e 200195. O `adapterId` não serve de
> desempate: é um LUID regerado a cada boot.

Alvos `MIRACAST`/`INDIRECT_WIRED`/`INDIRECT_VIRTUAL` são filtrados — não são
porta física. Nesta máquina apareceram 16 deles, que entrariam no teste como
portas eternamente desconectadas. `INTERNAL`/`DISPLAYPORT_EMBEDDED` são o
equivalente de eDP/LVDS e ficam fora do teste de portas.

**Descartado:** `WmiMonitorConnectionParams` só lista monitor conectado.
Serve como checagem cruzada, não como fonte.

## 4. Áudio: detecção de jack

O Windows mantém o estado de cada endpoint no registro, em
`MMDevices\Audio\Render\{GUID}`:

```
DeviceState  1 = ACTIVE     (plugado)
DeviceState  8 = UNPLUGGED  (o jack existe e está vazio)
FormFactor   3 = Headphones, 5 = Headset, 1 = Speakers
```

Mesma informação que `IMMDeviceEnumerator` + `DEVICE_STATE_UNPLUGGED`
entregariam via Core Audio, sem `pycaw`/`comtypes` — e independente do idioma
do Windows: o nome do endpoint é traduzido ("Auscultadores", "Fones de
ouvido"), o FormFactor não.

Endpoints Bluetooth também se declaram Headphones. Um headset pareado ficaria
"conectado" desde o início e a etapa passaria sem ninguém plugar nada no jack.
O filtro sobe até o dispositivo pai pelo nó PnP do endpoint
(`SWD\MMDEVAPI\{...}`) e aceita só `HDAUDIO\`, `USB\` ou `PCI\`.

Verificado na bancada com um QCY H3 pareado e ativo: `headphone_connected()`
devolve `False`, e o jack analógico do Realtek aparece como `UNPLUGGED`.

Tons e teste de microfone não mudaram — `pygame.sndarray` e `sounddevice` já
são multiplataforma.

`pulse_available()` virou `jack_detection_available()`, com o mesmo contrato: o
`main.py` cai em `ask_operator()` quando a máquina não expõe jack.

## 5. WiFi

Native Wifi API (`wlanapi.dll`) por `ctypes`, não `netsh`: a saída do `netsh` é
traduzida, e numa bancada em português o parser quebraria. `WlanScan` força uma
varredura de verdade no rádio em vez de devolver cache, e
`WlanGetNetworkBssList` dá dBm e frequência reais — a mesma forma de dado que
`iw scan` produz no Linux.

Uma diferença de comportamento: `wifi_enable()` no Windows **não liga o rádio**.
`WlanSetInterface` exige privilégio e não vence o modo avião; o caminho
suportado é o operador ligar. A função devolve o estado real com uma instrução,
em vez de fingir que ligou.

## 6. Resto do mapeamento

| Função | Linux | Windows |
|---|---|---|
| Serial | `dmi/id/product_serial` | `Win32_BIOS.SerialNumber` (uma chamada PowerShell, em cache) |
| Fabricante / modelo | `dmi/id/sys_vendor`, `product_name` | registro `HARDWARE\DESCRIPTION\System\BIOS` |
| Modelo (Lenovo) | `dmi/id/product_version` | `SystemVersion` na mesma chave |
| CPU vendor / nome | `/proc/cpuinfo` | registro `...\CentralProcessor\0` |
| RAM | `/proc/meminfo` | `GlobalMemoryStatusEx` |
| Disco / IP | `lsblk`, `hostname -I` | `psutil` |
| Ethernet carrier | `/sys/class/net/X/carrier` | `psutil.net_if_stats().isup` |
| Interfaces cabeadas | `/sys/class/net/*` | registro da classe de rede (`*IfType`, `*PhysicalMediaType`, `*NdisDeviceType`) |
| Câmera | `cv2.CAP_ANY` | `cv2.CAP_MSMF` |
| Foto local | `/tmp/revy_photos` | `%TEMP%\revy_photos` |
| Upload SMB | `mount -t cifs` + sudo | `WNetAddConnection2` + cópia para UNC (sem admin) |
| Trava Alt+Tab | `gsettings` | hook `WH_KEYBOARD_LL` em thread própria |
| Relógio NTP | `sudo date` | `SetSystemTime`, com fallback `w32tm /resync` |

Só o serial usa PowerShell, e uma vez por execução — não existe no registro.
O resto é registro ou API direta.

### Detalhes que não são óbvios

**Adaptadores virtuais.** O registro não separa placa de rede real de cliente
VPN: um adaptador Fortinet registra `*PhysicalMediaType` 14 e `*NdisDeviceType`
0, igual a uma placa física. O filtro cruza com `psutil` (só o que existe
agora) e descarta por descrição do driver. Nesta bancada, entre 37 adaptadores,
sobrou exatamente a Intel I219-LM.

**Nome da interface.** `Ethernet 6` é renomeável pelo usuário, ao contrário do
`eno2` do Linux. Quando o cadastro traz um nome que não existe e a máquina tem
uma única placa cabeada, o teste usa essa placa: o teste físico (conectar,
remover, conectar) continua valendo, e reprovar por divergência de nome seria
falso negativo. O cadastro também já sugere o nome quando só há uma.

**Hook de teclado.** Roda em thread própria com bomba de mensagens. LL hooks
são entregues na thread que os instalou, e essa thread precisa estar
processando mensagens — pendurar no loop do pygame deixaria o hook mudo sempre
que um passo bloqueasse esperando hardware. Ctrl+Alt+Del continua funcionando:
o SO não permite interceptá-lo. Para fechar a máquina de verdade, o caminho é o
Shell Launcher do Windows Enterprise/IoT.

**Timeout do smoke test.** Era `SIGALRM`, que só existe no Unix — no Windows o
timeout ficava desligado e uma checagem travada segurava o script inteiro.
Agora é por thread, e funciona nos dois.

---

## 7. Banco de dados

`scripts/add_platform_column.sql` adiciona `devices.platform` e marca as linhas
existentes como `linux`.

A mesma porta física tem nomes diferentes em cada SO, então um cadastro feito
na linha Debian encontra o registro do modelo no Windows e reprova todas as
portas, porque nenhuma string casa. Cada modelo precisa de um cadastro por SO.

`_find_device()` filtra por `platform` junto com o `cpu_vendor` que já existia,
e `send_to_db()` grava a coluna. Ambos detectam o erro 1054 (coluna inexistente)
e caem na consulta antiga com um aviso no console — o app roda antes e depois da
migração.

Não dá para normalizar em vez de duplicar. Para USB seria mecânico
(`PCI(1400)` → `0000:00:14.0`), mas para vídeo a numeração de connector do DRM
(`HDMI-A-1`) e o `connectorInstance` do Windows não têm correspondência
garantida.

---

## 8. Segurança — resolver antes de distribuir o `.exe`

Credenciais hardcoded, já no histórico do git:

- MySQL `10.3.0.12` / `drack` / senha — em `device_info.py`, `save_log.py`,
  `app_flow.py`, `database.py`, `cadastro.py`, `scripts/smoke_test.py`
- SMB `172.16.48.33` / `marcos` / senha — em `camera.py`

Empacotar em `.exe` piora o quadro: um bundle PyInstaller é trivialmente
extraível (`pyi-archive_viewer`, que está no próprio `.venv` do projeto), e o
binário vai para máquinas que saem da fábrica.

Antes do primeiro `.exe`: mover para arquivo de config ou variável de ambiente,
e rotacionar as duas — devem ser consideradas comprometidas independente do
porte.

---

## 9. Em aberto

| Item | Situação |
|---|---|
| USB com pendrive plugado | O caminho completo (enumeração, location path, filtro por serviço) foi validado; falta o teste na bancada com um pendrive de verdade em cada porta |
| Fluxo completo do `main.py` | Cada peça foi testada isolada e o smoke test passa; falta uma execução ponta a ponta com o equipamento cadastrado |
| Máquina com GPU discreta | Alvos da dGPU e da iGPU podem apontar para a mesma porta física. O cadastro por delta de conexão resolve, mas não foi visto em bancada |
| `src/alltests.py` | Monólito legado, com marcadores de conflito de merge commitados; não faz parse. O entrypoint é `src/main.py` |
| `src/main_new.py`, `functions/audiotest.py`, `functions/audio_tests.py`, `functions/database.py`, `functions/*_test.py` | Não são importados pelo `main.py`. Não foram portados |
| Autostart / kiosk | Não automatizado. Ver seção 6 para as opções |

---

## Referências

- [DEVPKEY_Device_LocationPaths](https://learn.microsoft.com/en-us/windows-hardware/drivers/install/devpkey-device-locationpaths)
- [CM_Get_DevNode_PropertyW](https://learn.microsoft.com/en-us/windows/win32/api/cfgmgr32/nf-cfgmgr32-cm_get_devnode_propertyw)
- [QueryDisplayConfig](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-querydisplayconfig)
- [DISPLAYCONFIG_TARGET_DEVICE_NAME](https://learn.microsoft.com/en-us/windows/win32/api/wingdi/ns-wingdi-displayconfig_target_device_name)
- [IKsJackDescription](https://learn.microsoft.com/en-us/windows/win32/api/devicetopology/nn-devicetopology-iksjackdescription2)
- [Native Wifi API](https://learn.microsoft.com/en-us/windows/win32/nativewifi/portal)
- [WNetAddConnection2](https://learn.microsoft.com/en-us/windows/win32/api/winnetwk/nf-winnetwk-wnetaddconnection2w)
- [SetWindowsHookEx](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setwindowshookexw)
