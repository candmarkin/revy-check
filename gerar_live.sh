#!/bin/sh
set -e

LIVE=/live

echo "[1/3] Preparando pasta de destino..."
mkdir -p "$LIVE"

echo "[2/3] Removendo squashfs antigo..."
rm -f $LIVE/filesystem.squashfs

echo "[3/3] Gerando squashfs com excludes..."
mksquashfs / $LIVE/filesystem.squashfs \
    -comp xz \
    -wildcards \
    -e proc sys dev tmp run mnt media lost+found live

echo "PRONTO -> $LIVE/filesystem.squashfs"
