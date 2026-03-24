#!/bin/bash
# 导出 nRF52840 完整 1MB Flash
source "$(dirname "$0")/common.sh"

OUTPUT="${1:-$SCRIPTS_DIR/dump_full_flash.bin}"

cat > /tmp/jlink_cmd.jlink << EOF
print "Dumping full 1MB flash to $OUTPUT ..."
savebin $OUTPUT 0x0 0x100000
print "Done!"
exit
EOF

echo "========================================="
echo "  Dump Full Flash (1MB)"
echo "  Output: $OUTPUT"
echo "========================================="
$JLINK $JLINK_OPTS -CommandFile /tmp/jlink_cmd.jlink

if [ -f "$OUTPUT" ]; then
    echo ""
    echo "Flash dump saved. File size:"
    ls -lh "$OUTPUT"
    echo ""
    echo "MD5:"
    md5 "$OUTPUT" 2>/dev/null || md5sum "$OUTPUT"
fi
