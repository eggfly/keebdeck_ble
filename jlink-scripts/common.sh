#!/bin/bash
# Common variables for all JLink scripts
DEVICE="NRF52840_XXAA"
IF="SWD"
SPEED="4000"
JLINK="JLinkExe"
JLINK_OPTS="-device $DEVICE -if $IF -speed $SPEED -autoconnect 1"
SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
