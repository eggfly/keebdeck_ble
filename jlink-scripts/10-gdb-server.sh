#!/bin/bash
# 启动 JLink GDB Server，用于实时调试
source "$(dirname "$0")/common.sh"

PORT="${1:-2331}"

echo "========================================="
echo "  JLink GDB Server"
echo "  Port: $PORT"
echo "========================================="
echo ""
echo "Connect with GDB:"
echo "  arm-none-eabi-gdb firmware.elf"
echo "  (gdb) target remote localhost:$PORT"
echo ""

JLinkGDBServer -device $DEVICE -if $IF -speed $SPEED -port $PORT
