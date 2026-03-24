#!/bin/bash
# 刷入 hex/bin 固件
source "$(dirname "$0")/common.sh"

if [ -z "$1" ]; then
    echo "Usage: $0 <firmware.hex|firmware.bin>"
    echo ""
    echo "Examples:"
    echo "  $0 firmware.hex          # 刷入 hex 文件 (自带地址信息)"
    echo "  $0 firmware.bin          # 刷入 bin 文件 (从 0x0 开始)"
    exit 1
fi

FIRMWARE="$1"

if [ ! -f "$FIRMWARE" ]; then
    echo "Error: File not found: $FIRMWARE"
    exit 1
fi

echo "========================================="
echo "  Flash Firmware"
echo "  File: $FIRMWARE"
echo "  Size: $(ls -lh "$FIRMWARE" | awk '{print $5}')"
echo "========================================="
echo ""
read -p "Confirm flash? This will ERASE the chip first! [y/N] " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "Cancelled."
    exit 0
fi

cat > /tmp/jlink_cmd.jlink << EOF
erase
loadfile $FIRMWARE
r
g
exit
EOF

$JLINK $JLINK_OPTS -CommandFile /tmp/jlink_cmd.jlink
echo ""
echo "Flash complete. Chip is running."
