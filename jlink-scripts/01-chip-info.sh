#!/bin/bash
# 读取 nRF52840 芯片信息
source "$(dirname "$0")/common.sh"

cat > /tmp/jlink_cmd.jlink << 'EOF'
mem32 0x10000060 2
mem32 0x100000A0 1
mem32 0x100000A4 2
mem32 0x10000100 1
mem32 0x10000104 1
mem32 0x10000110 1
mem32 0x10000114 1
mem32 0x10001208 1
mem32 0x1000120C 1
mem32 0x10001200 2
mem32 0x10001014 1
mem32 0x10001018 1
exit
EOF

echo "========================================="
echo "  nRF52840 Chip Information Reader"
echo "========================================="
echo ""
echo "Register addresses:"
echo "  0x10000060 x2  = Device ID"
echo "  0x100000A0 x1  = Device Address Type"
echo "  0x100000A4 x2  = BLE MAC Address"
echo "  0x10000100 x1  = Part Number"
echo "  0x10000104 x1  = Package Variant"
echo "  0x10000110 x1  = RAM Variant"
echo "  0x10000114 x1  = Flash Variant"
echo "  0x10001208 x1  = APPROTECT (FF=open)"
echo "  0x1000120C x1  = NFCPINS"
echo "  0x10001200 x2  = PSELRESET"
echo "  0x10001014 x1  = Bootloader Address"
echo "  0x10001018 x1  = MBR Params Address"
echo ""
$JLINK $JLINK_OPTS -CommandFile /tmp/jlink_cmd.jlink
