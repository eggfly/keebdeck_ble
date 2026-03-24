#!/bin/bash
# 读取任意内存地址
source "$(dirname "$0")/common.sh"

if [ -z "$1" ]; then
    echo "Usage: $0 <address> [count]"
    echo ""
    echo "Examples:"
    echo "  $0 0x0 16           # 读取 Flash 起始 16 个 32-bit words"
    echo "  $0 0x10000000 8     # 读取 FICR"
    echo "  $0 0x10001000 8     # 读取 UICR"
    echo "  $0 0x20000000 8     # 读取 RAM 起始"
    echo ""
    echo "nRF52840 Memory Map:"
    echo "  0x00000000 - 0x000FFFFF  Flash (1MB)"
    echo "  0x10000000 - 0x100001FF  FICR (Factory Info)"
    echo "  0x10001000 - 0x100013FF  UICR (User Config)"
    echo "  0x20000000 - 0x2003FFFF  RAM (256KB)"
    echo "  0x40000000+             Peripherals"
    exit 1
fi

ADDR="$1"
COUNT="${2:-8}"

cat > /tmp/jlink_cmd.jlink << EOF
mem32 $ADDR $COUNT
exit
EOF

echo "Reading $COUNT words from $ADDR ..."
$JLINK $JLINK_OPTS -CommandFile /tmp/jlink_cmd.jlink
