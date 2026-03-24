#!/bin/bash
# 只刷 Bootloader (不擦除 application)
# 适用于恢复 nice!nano 的 Adafruit UF2 bootloader
source "$(dirname "$0")/common.sh"

if [ -z "$1" ]; then
    echo "Usage: $0 <bootloader.hex>"
    echo ""
    echo "This flashes ONLY the bootloader without erasing the full chip."
    echo "Use this to restore the nice!nano UF2 bootloader."
    exit 1
fi

FIRMWARE="$1"

if [ ! -f "$FIRMWARE" ]; then
    echo "Error: File not found: $FIRMWARE"
    exit 1
fi

echo "========================================="
echo "  Flash Bootloader Only (no full erase)"
echo "  File: $FIRMWARE"
echo "========================================="
echo ""
read -p "Confirm? [y/N] " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "Cancelled."
    exit 0
fi

cat > /tmp/jlink_cmd.jlink << EOF
loadfile $FIRMWARE
r
g
exit
EOF

$JLINK $JLINK_OPTS -CommandFile /tmp/jlink_cmd.jlink
echo ""
echo "Bootloader flashed."
