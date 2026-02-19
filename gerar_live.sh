#!/bin/sh
set -e

WORK=/tmp/live-build
ROOTFS=$WORK/rootfs
LIVE=/live

echo "[1/6] Preparando pastas..."
rm -rf "$WORK"
mkdir -p "$ROOTFS"
mkdir -p "$LIVE"

echo "[2/6] Copiando root atual..."
rsync -a \
    --delete \
    --exclude=/proc \
    --exclude=/sys \
    --exclude=/dev \
    --exclude=/tmp \
    --exclude=/run \
    --exclude=/mnt \
    --exclude=/media \
    --exclude=/lost+found \
    --exclude=/live \
    / "$ROOTFS"

echo "[3/6] Limpando arquivos temporarios..."
rm -rf $ROOTFS/var/log/*
rm -rf $ROOTFS/var/cache/*
rm -rf $ROOTFS/tmp/*

echo "[4/6] Recriando dirs runtime..."
mkdir -p $ROOTFS/proc
mkdir -p $ROOTFS/sys
mkdir -p $ROOTFS/dev
mkdir -p $ROOTFS/run
mkdir -p $ROOTFS/tmp
chmod 1777 $ROOTFS/tmp

echo "[5/6] Removendo squashfs antigo..."
rm -f $LIVE/filesystem.squashfs

echo "[6/6] Gerando squashfs..."
mksquashfs $ROOTFS $LIVE/filesystem.squashfs -comp xz -wildcards

echo "PRONTO -> $LIVE/filesystem.squashfs"
