#!/bin/bash
# 导出 Bootloader 区域 (通常在 flash 末尾 0xF0000-0x100000, 64KB)
# nice!nano bootloader 通常从 0xF4000 开始 (48KB)
source "$(dirname "$0")/common.sh"

OUTPUT="${1:-$SCRIPTS_DIR/dump_bootloader.bin}"

cat > /tmp/jlink_cmd.jlink << EOF
# 先读 bootloader 起始地址
print "=== Bootloader Start Address ==="
mem32 0x10001014 1

# 导出 0xE0000-0x100000 (128KB, 覆盖 bootloader + settings)
print "Dumping bootloader region (0xE0000 - 0x100000) ..."
savebin $OUTPUT 0xE0000 0x20000
print "Done!"
exit
EOF

echo "========================================="
echo "  Dump Bootloader Region (128KB)"
echo "  Output: $OUTPUT"
echo "========================================="
$JLINK $JLINK_OPTS -CommandFile /tmp/jlink_cmd.jlink

if [ -f "$OUTPUT" ]; then
    echo ""
    echo "Bootloader dump saved. File size:"
    ls -lh "$OUTPUT"
fi
