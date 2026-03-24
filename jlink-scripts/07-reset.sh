#!/bin/bash
# 复位芯片
source "$(dirname "$0")/common.sh"

cat > /tmp/jlink_cmd.jlink << 'EOF'
r
g
exit
EOF

echo "Resetting chip..."
$JLINK $JLINK_OPTS -CommandFile /tmp/jlink_cmd.jlink
echo "Chip reset and running."
