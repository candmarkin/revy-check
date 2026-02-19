#!/bin/sh
set -e

LIVE=/live

echo "[1/3] Preparando pasta de destino..."
mkdir -p "$LIVE"

echo "[2/3] Removendo squashfs antigo..."
rm -f $LIVE/filesystem.squashfs

echo "[3/3] Gerando squashfs com excludes..."
mksquashfs / $LIVE/filesystem.squashfs -e /proc/* /dev/* /sys/* /mnt/* /tmp/* -comp xz -b 1048576 -Xdict-size 100% -Xbcj x86 -always-use-fragments -noappend -no-wildcards

echo "PRONTO -> $LIVE/filesystem.squashfs"
