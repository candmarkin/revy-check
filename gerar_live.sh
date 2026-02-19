#!/usr/bin/env bash
set -e

echo "=== GERANDO GOLDEN IMAGE DO SISTEMA ATUAL ==="

LIVE_DIR="/live"
IMG_DIR="/tmp/live-image-root"

echo "[1/6] Criando pastas..."
sudo rm -rf $IMG_DIR
sudo mkdir -p $IMG_DIR

sudo mkdir -p $LIVE_DIR
sudo rm -f $LIVE_DIR/filesystem.squashfs

echo "[2/6] Copiando sistema..."
sudo rsync -aAX --numeric-ids 
/ $IMG_DIR 
--exclude=$IMG_DIR 
--exclude=/proc/* 
--exclude=/sys/* 
--exclude=/dev/* 
--exclude=/run/* 
--exclude=/tmp/* 
--exclude=/mnt/* 
--exclude=/media/* 
--exclude=/lost+found 
--exclude=/swapfile 
--exclude=/var/tmp/* 
--exclude=/var/run/* 
--exclude=/var/lock/* 
--exclude=/var/cache/apt/archives/* 
--exclude=/var/lib/systemd/random-seed

echo "[3/6] Limpando identidade da máquina..."
sudo rm -f $IMG_DIR/etc/machine-id
sudo rm -f $IMG_DIR/var/lib/dbus/machine-id
sudo touch $IMG_DIR/etc/machine-id

echo "[4/6] Limpando logs/cache..."
sudo rm -rf $IMG_DIR/var/log/*
sudo rm -rf $IMG_DIR/root/.bash_history
sudo rm -rf $IMG_DIR/home/*/.bash_history 2>/dev/null || true

echo "[5/6] Limpando apt..."
sudo chroot $IMG_DIR apt clean || true
sudo rm -rf $IMG_DIR/var/lib/apt/lists/*

echo "[6/6] Gerando squashfs (modo PXE rápido)..."
sudo mksquashfs $IMG_DIR $LIVE_DIR/filesystem.squashfs 
-comp zstd -Xcompression-level 15 
-b 1M -noappend

echo ""
echo "=== PRONTO ==="
echo "Arquivo gerado em: $LIVE_DIR/filesystem.squashfs"
