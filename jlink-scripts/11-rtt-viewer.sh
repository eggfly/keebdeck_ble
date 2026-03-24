#!/bin/bash
# 启动 RTT (Real-Time Transfer) 日志查看
# RTT 是 SEGGER 的实时日志协议，比 UART 快很多
# ZMK 固件支持 RTT logging
source "$(dirname "$0")/common.sh"

echo "========================================="
echo "  JLink RTT Viewer"
echo "  (Real-Time Transfer logging)"
echo "========================================="
echo ""
echo "If ZMK is built with CONFIG_LOG=y and"
echo "CONFIG_USE_SEGGER_RTT=y, you'll see logs here."
echo ""

JLinkRTTClient &
RTT_PID=$!

cat > /tmp/jlink_cmd.jlink << 'EOF'
r
g
sleep 100000
EOF

$JLINK $JLINK_OPTS -CommandFile /tmp/jlink_cmd.jlink

kill $RTT_PID 2>/dev/null
