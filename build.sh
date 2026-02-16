#!/bin/bash

# Script de build para RevyCheck Rust

set -e

echo "==================================="
echo "RevyCheck - Build Script"
echo "==================================="

# Verificar se Rust está instalado
if ! command -v cargo &> /dev/null; then
    echo "❌ Rust não está instalado!"
    echo "Instale com: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
    exit 1
fi

echo "✓ Rust encontrado: $(rustc --version)"

# Verificar dependências do sistema (Linux)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo ""
    echo "Verificando dependências do sistema..."
    
    MISSING_DEPS=()
    
    if ! pkg-config --exists gtk+-3.0; then
        MISSING_DEPS+=("libgtk-3-dev")
    fi
    
    if ! pkg-config --exists alsa; then
        MISSING_DEPS+=("libasound2-dev")
    fi
    
    if ! pkg-config --exists mysqlclient; then
        MISSING_DEPS+=("libmysqlclient-dev")
    fi
    
    if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
        echo "❌ Dependências faltando: ${MISSING_DEPS[*]}"
        echo "Instale com:"
        echo "  sudo apt-get install -y ${MISSING_DEPS[*]} pkg-config libssl-dev"
        exit 1
    fi
    
    echo "✓ Todas as dependências do sistema estão instaladas"
fi

echo ""
echo "Compilando em modo Release..."
echo ""

cargo build --release

echo ""
echo "==================================="
echo "✅ Build concluído com sucesso!"
echo "==================================="
echo ""
echo "Binário: target/release/revy-check"
echo ""
echo "Para executar:"
echo "  ./target/release/revy-check"
echo ""
