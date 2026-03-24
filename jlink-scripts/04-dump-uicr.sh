#!/bin/bash
# 导出 UICR (User Information Configuration Registers)
# UICR 包含 bootloader 地址、APPROTECT、NFC 配置等重要信息
source "$(dirname "$0")/common.sh"

OUTPUT="${1:-$SCRIPTS_DIR/dump_uicr.bin}"

cat > /tmp/jlink_cmd.jlink << EOF
print "Dumping UICR (0x10001000 - 0x10001400, 1KB) ..."
savebin $OUTPUT 0x10001000 0x400
print "Done!"
exit
EOF

echo "========================================="
echo "  Dump UICR (1KB)"
echo "  Output: $OUTPUT"
echo "========================================="
$JLINK $JLINK_OPTS -CommandFile /tmp/jlink_cmd.jlink

if [ -f "$OUTPUT" ]; then
    echo ""
    ls -lh "$OUTPUT"
    echo ""
    echo "UICR hex dump (first 64 bytes):"
    xxd -l 64 "$OUTPUT"
fi
