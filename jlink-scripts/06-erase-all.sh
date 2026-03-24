#!/bin/bash
# 全片擦除 (包括 UICR)
# 这会清除 APPROTECT，可用于解锁被保护的芯片
source "$(dirname "$0")/common.sh"

echo "========================================="
echo "  Full Chip Erase (including UICR)"
echo "========================================="
echo ""
echo "WARNING: This will erase EVERYTHING:"
echo "  - Application firmware"
echo "  - Bootloader"
echo "  - SoftDevice"
echo "  - UICR (including APPROTECT)"
echo ""
read -p "Are you sure? [y/N] " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "Cancelled."
    exit 0
fi

cat > /tmp/jlink_cmd.jlink << 'EOF'
erase
r
exit
EOF

$JLINK $JLINK_OPTS -CommandFile /tmp/jlink_cmd.jlink
echo ""
echo "Chip erased."
