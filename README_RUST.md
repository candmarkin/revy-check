# RevyCheck - Rust + egui

Esta é a versão reescrita do sistema de testes RevyCheck em Rust com interface gráfica egui.

## Características

- **Interface gráfica moderna** com egui (em vez de Pygame)
- **Performance nativa** com Rust
- **Tipagem forte** e segurança de memória
- **Multiplataforma** (Linux principalmente, com suporte básico para Windows/macOS)

## Estrutura do Projeto

```
src/
├── main.rs           # Entry point
├── app.rs            # Aplicação principal e máquina de estados
├── audio.rs          # Testes de áudio (alto-falantes, fone, microfone)
├── config.rs         # Estruturas de configuração
├── database.rs       # Conexão com MySQL
├── device_info.rs    # Leitura de informações do dispositivo
├── ethernet.rs       # Teste de porta Ethernet
├── keyboard.rs       # Teste de teclado
├── log_manager.rs    # Gerenciamento de logs
├── screen.rs         # Teste de tela
├── system_utils.rs   # Utilitários do sistema (NTP, Alt+Tab, etc)
├── usb.rs            # Teste de portas USB
└── video.rs          # Teste de portas de vídeo
```

## Dependências

### Sistema (Linux)

```bash
# Debian/Ubuntu
sudo apt-get install -y \
    libgtk-3-dev \
    libasound2-dev \
    libmysqlclient-dev \
    pkg-config \
    libssl-dev

# Arch Linux
sudo pacman -S gtk3 alsa-lib mariadb-libs openssl
```

### Rust

Certifique-se de ter o Rust instalado:

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

## Compilação

### Debug (desenvolvimento)

```bash
cargo build
```

### Release (produção)

```bash
cargo build --release
```

O binário estará em `target/release/revy-check`

## Execução

```bash
# Debug
cargo run

# Release
./target/release/revy-check
```

## Diferenças da versão Python

### Melhorias

1. **Performance**: Muito mais rápido e com menor uso de memória
2. **Tipagem**: Erros detectados em tempo de compilação
3. **Concorrência**: Melhor suporte para operações assíncronas
4. **Interface**: egui é mais moderna e responsiva que Pygame

### Limitações atuais

1. **PulseAudio**: A detecção de fone de ouvido está simplificada (usa botão em vez de detecção automática)
2. **Hot-reload**: Não há hot-reload, é necessário recompilar
3. **Cadastro de portas**: A funcionalidade de cadastro inicial não foi portada (pode ser adicionada)

## Modo DEV

Pressione `Ctrl+Shift+D+V` para ativar o modo desenvolvedor, que permite:
- Sair com ESC
- Ver informações de debug

## Configuração do Banco de Dados

O sistema espera as seguintes tabelas no MySQL:

- `devices`: Informações dos dispositivos
- `device_usb_ports`: Mapeamento de portas USB
- `device_video_ports`: Mapeamento de portas de vídeo
- `logs`: Logs dos testes

Credenciais estão hardcoded em `src/database.rs` (mesmas da versão Python).

## TODO

- [ ] Implementar detecção automática de fone de ouvido via PulseAudio/PipeWire
- [ ] Portar funcionalidade de cadastro de portas
- [ ] Adicionar testes unitários
- [ ] Melhorar tratamento de erros
- [ ] Adicionar internacionalização
- [ ] Criar instalador/empacotamento

## Licença

Mesmo que o projeto original.
