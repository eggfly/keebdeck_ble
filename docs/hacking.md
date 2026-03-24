# Hacking Guide - JLink/SWD for nRF52840

This guide covers using a J-Link debugger to interact with nRF52840 via SWD on macOS.

## Table of Contents

- [Hardware Setup](#hardware-setup)
- [Software Setup](#software-setup)
- [Basic Operations](#basic-operations)
- [Firmware Dump & Flash](#firmware-dump--flash)
- [Blank Chip: Flash from Scratch](#blank-chip-flash-from-scratch)
- [Simulate Blank Chip (Full Erase)](#simulate-blank-chip-full-erase)
- [Bootloader Download & Update](#bootloader-download--update)
- [SoftDevice Explained](#softdevice-explained)
- [nRF52840 Memory Map Reference](#nrf52840-memory-map-reference)
- [UF2 Format Notes](#uf2-format-notes)
- [Troubleshooting](#troubleshooting)

## Hardware Setup

### SWD Wiring (4 wires minimum)

```
J-Link OB          nRF52840
──────────          ────────
SWDIO (DIO)  ────  SWDIO
SWCLK (CLK)  ────  SWCLK
3V3          ────  VDD
GND          ────  GND
RST (optional) ──  nRESET    (recommended - helps recover from sleep/lock)
```

> SWDIO and SWCLK are dedicated debug pins on nRF52840, not GPIOs.

### J-Link OB Clone Notes

- J-Link OB clones work fine with `JLinkExe` but may **NOT** work with `nrfjprog` (error -256)
- If using a clone, stick to `JLinkExe` commands and the scripts in `jlink-scripts/`
- The scripts in this repo are designed for `JLinkExe` specifically

## Software Setup

### Install on macOS

```bash
# J-Link Software Pack (required)
brew install --cask segger-jlink

# nRF Command Line Tools (optional, needs real J-Link)
brew install --cask nordic-nrf-command-line-tools
```

### Verify Connection

```bash
JLinkExe -device NRF52840_XXAA -if SWD -speed 4000 -autoconnect 1
```

Expected output:
```
Found SW-DP with ID 0x2BA01477
Cortex-M4 identified.
```

Type `exit` to quit.

## Basic Operations

### Using the Scripts

All scripts are in `jlink-scripts/`. Make sure they're executable:

```bash
chmod +x jlink-scripts/*.sh
```

| Script | Description |
|--------|-------------|
| `01-chip-info.sh` | Read FICR/UICR registers (Device ID, BLE MAC, APPROTECT, etc.) |
| `02-dump-full-flash.sh` | Export entire 1MB flash to bin file |
| `03-dump-bootloader.sh` | Export bootloader region (0xE0000-0x100000) |
| `04-dump-uicr.sh` | Export UICR configuration registers |
| `05-flash-hex.sh <file>` | Full erase + flash hex/bin firmware |
| `06-erase-all.sh` | Full chip erase (including UICR) |
| `07-reset.sh` | Reset and run |
| `08-read-memory.sh <addr> [n]` | Read N words from any address |
| `09-flash-bootloader-only.sh <file>` | Flash bootloader without full erase |
| `10-gdb-server.sh` | Start GDB server for debugging |
| `11-rtt-viewer.sh` | Real-time logging via RTT |

### Manual JLinkExe Commands

```bash
JLinkExe -device NRF52840_XXAA -if SWD -speed 4000 -autoconnect 1
```

Inside JLinkExe interactive mode:

```
mem32 <addr> <count>       # Read 32-bit words
savebin <file> <addr> <size>  # Dump memory to file
loadfile <file>            # Flash hex/bin file
erase                      # Full chip erase
r                          # Reset
g                          # Go (run)
h                          # Halt
exit                       # Quit
```

## Firmware Dump & Flash

### Dump Full Flash

```bash
./jlink-scripts/02-dump-full-flash.sh
# Output: jlink-scripts/dump_full_flash.bin (1MB)
```

### Dump Bootloader Only

```bash
./jlink-scripts/03-dump-bootloader.sh
# Output: jlink-scripts/dump_bootloader.bin (128KB)
```

### Flash a Hex File (with full erase)

```bash
./jlink-scripts/05-flash-hex.sh firmware/bootloader/nice_nano_bootloader-0.6.0_s140_6.1.1.hex
```

### Flash Without Erase (bootloader only)

```bash
./jlink-scripts/09-flash-bootloader-only.sh firmware/bootloader/nice_nano_bootloader-0.6.0_s140_6.1.1.hex
```

### Compare UF2 with Flash Dump

The UF2 file from the bootloader USB mode (`CURRENT.UF2`) and the JLink flash dump contain the same data, just in different formats:

- **`CURRENT.UF2`**: UF2 container format, 512-byte blocks with 256-byte payloads + headers
- **`dump_full_flash.bin`**: Raw flash image, byte-for-byte copy

To extract raw binary from UF2 and compare:

```python
# Each 512-byte UF2 block: 32-byte header + 256-byte payload + padding + magic
# UF2 payload covers 0x1000-0xAD000 (MBR excluded, SoftDevice + App included)
```

We verified they are **byte-identical** in the overlapping region.

## Blank Chip: Flash from Scratch

A factory-fresh nRF52840 has **completely empty flash (all 0xFF)**. No MBR, no bootloader, no SoftDevice. USB won't work until you flash a bootloader via SWD.

### Step-by-Step: Blank → Working Keyboard

```
Blank nRF52840 (0xFF)
    │
    ▼  JLink SWD
    │
    ├── Step 1: Flash bootloader hex (includes MBR + SoftDevice + Bootloader)
    │            nice_nano_bootloader-0.6.0_s140_6.1.1.hex
    │
    ▼  Now USB works! Double-tap reset → NICENANO USB drive appears
    │
    └── Step 2: Copy zmk.uf2 to NICENANO drive
                 (or flash via JLink)
```

### Flashing Commands

```bash
# Option A: Use the script
./jlink-scripts/05-flash-hex.sh firmware/bootloader/nice_nano_bootloader-0.6.0_s140_6.1.1.hex

# Option B: Manual JLinkExe
JLinkExe -device NRF52840_XXAA -if SWD -speed 4000 -autoconnect 1
> erase
> loadfile firmware/bootloader/nice_nano_bootloader-0.6.0_s140_6.1.1.hex
> r
> g
> exit
```

> **Important**: The `nice_nano_bootloader-0.6.0_s140_6.1.1.hex` file is a **merged hex** that contains MBR + SoftDevice S140 v6.1.1 + Bootloader all in one file. You only need to flash this single file.

### After Flashing Bootloader

1. Disconnect J-Link
2. Connect USB-C cable to the board
3. Double-tap the Reset button/pad
4. A USB drive named `NICENANO` should appear
5. Copy your `zmk.uf2` file to the drive
6. Board auto-reboots with new firmware

## Simulate Blank Chip (Full Erase)

Want to test the "fresh chip" experience? Full erase wipes everything:

```bash
./jlink-scripts/06-erase-all.sh
```

This erases:
- Application firmware
- Bootloader
- SoftDevice
- MBR
- UICR (including APPROTECT, reset pin config, bootloader address)
- NVS storage (Bluetooth pairings, settings)

### What Happens After Full Erase

After erasing, the chip is in factory-blank state:
- **All flash = 0xFF**
- **UICR = 0xFF** (no bootloader address, no reset pin config)
- **FICR unchanged** (factory-programmed, read-only: Device ID, BLE MAC, calibration)
- **USB does NOT work** (no bootloader)
- **BLE does NOT work** (no SoftDevice)
- **Chip runs nothing** - CPU fetches from 0x00000000, sees 0xFFFFFFFF, faults immediately
- **SWD still works** - you can always re-flash via J-Link

### Recovery from Blank

```bash
# Just flash the bootloader hex again
./jlink-scripts/05-flash-hex.sh firmware/bootloader/nice_nano_bootloader-0.6.0_s140_6.1.1.hex
```

> This is completely safe. You can erase and re-flash as many times as you want (flash endurance: ~10,000 write/erase cycles per page).

## Bootloader Download & Update

### Included Bootloader Files

| File | Description |
|------|-------------|
| `nice_nano_bootloader-0.6.0_s140_6.1.1.hex` | Nice!Nano bootloader v0.6.0 with SoftDevice S140 v6.1.1 (merged hex) |
| `pca10056_bootloader-0.5.0-dirty_s140_6.1.1.hex` | Nordic DK (PCA10056) bootloader v0.5.0 with S140 v6.1.1 |

### Download Latest Bootloader

**Recommended: Adafruit upstream v0.10.0** (2026-02, includes nice_nano builds):

| File | URL | Purpose |
|------|-----|---------|
| Merged hex (JLink flash) | [nice_nano_bootloader-0.10.0_s140_6.1.1.hex](https://github.com/adafruit/Adafruit_nRF52_Bootloader/releases/download/0.10.0/nice_nano_bootloader-0.10.0_s140_6.1.1.hex) | Flash to blank chip via JLink |
| UF2 update (no SoftDevice) | [update-nice_nano_bootloader-0.10.0_nosd.uf2](https://github.com/adafruit/Adafruit_nRF52_Bootloader/releases/download/0.10.0/update-nice_nano_bootloader-0.10.0_nosd.uf2) | Update existing bootloader via USB |
| DFU zip | [nice_nano_bootloader-0.10.0_s140_6.1.1.zip](https://github.com/adafruit/Adafruit_nRF52_Bootloader/releases/download/0.10.0/nice_nano_bootloader-0.10.0_s140_6.1.1.zip) | OTA/serial update |

- All releases: https://github.com/adafruit/Adafruit_nRF52_Bootloader/releases

**Nice-Keyboards fork (outdated):**
- v0.5.1.1 from June 2021, no pre-built merged `.hex` files
- https://github.com/Nice-Keyboards/Adafruit_nRF52_Bootloader/releases

### Which Bootloader to Use?

| Scenario | Recommended |
|----------|-------------|
| Blank chip via JLink | Adafruit **v0.10.0** merged hex (includes MBR + SoftDevice + Bootloader) |
| Update existing bootloader via USB | Adafruit v0.10.0 `_nosd.uf2` |
| Already working with v0.6.0 | Can keep using, or update to v0.10.0 |

> The merged hex (`*_s140_6.1.1.hex`) contains everything: MBR + SoftDevice S140 v6.1.1 + Bootloader + UICR config. Single file, single `loadfile` command.

### UF2 Bootloader Update (without J-Link)

If you already have a working bootloader and just want to update it:

1. Enter bootloader mode (double-tap reset)
2. Download `update-nice_nano_bootloader-0.10.0_nosd.uf2`
3. Copy it to the NICENANO USB drive
4. Bootloader self-updates

> The `_nosd` variant updates only the bootloader without touching SoftDevice.

### SoftDevice S140 Separate Download

Normally not needed (included in merged hex), but if you need it separately:
- Bundled in the Adafruit bootloader repo: `lib/softdevice/s140_nrf52_6.1.1/s140_nrf52_6.1.1_softdevice.hex`
- Nordic official: https://www.nordicsemi.com/Products/Development-software/s140/download

## SoftDevice Explained

SoftDevice 是 **Nordic 官方的闭源 BLE 协议栈**，可以理解为一个"蓝牙驱动固件"。

nRF52840 芯片本身不自带蓝牙功能——射频硬件有，但驱动蓝牙协议的软件需要额外烧录。没有 SoftDevice，ZMK 的蓝牙完全不工作。

### 它提供什么

- BLE 广播、连接、配对、bonding
- 链路层加密 (AES-CCM)
- 自适应跳频 (AFH)
- 射频硬件时序控制（通过 PPI 实现零 CPU 参与的精确收发）
- 中断优先级隔离（SoftDevice 占用最高优先级，应用代码不会干扰蓝牙时序）

### 架构关系

```
Flash 低地址 ──────────────────────────────────────── 高地址

  MBR → SoftDevice S140 → ZMK Application → Bootloader
  4KB     148KB              ~824KB            40KB
          ^^^^^^^^^^^^^^
          闭源 BLE 协议栈
          应用通过 SVC 软中断调用它
```

ZMK 不直接操作射频硬件，而是通过软中断（SVC call）请求 SoftDevice 发蓝牙包。两者运行在不同的中断优先级，互不干扰。

### SoftDevice 型号

| 型号 | 支持角色 | 适用芯片 |
|------|---------|---------|
| **S140** | BLE Central + Peripheral | nRF52840 (本项目使用) |
| S132 | BLE Central + Peripheral | nRF52832 |
| S112 | 仅 BLE Peripheral | 精简版，Flash 占用更小 |

### 版本说明

- 本项目使用 **S140 v6.1.1**，对应 nRF5 SDK
- Nordic 后来推出 nRF Connect SDK (基于 Zephyr)，用开源 Zephyr BLE 协议栈替代 SoftDevice
- 但 nice!nano 的 Adafruit UF2 Bootloader 方案仍然依赖 SoftDevice
- SoftDevice 的应用起始地址固定为 **0x26000** (S140 v6.x)

### nosd 文件的含义

在 bootloader 发布文件中经常看到 `_nosd` 后缀：

| 文件类型 | 包含内容 | 用途 |
|----------|---------|------|
| `*_s140_6.1.1.hex` | MBR + SoftDevice + Bootloader + UICR | JLink 刷空白芯片（完整刷入） |
| `*_nosd.uf2` | 仅 Bootloader 代码 | USB U 盘模式升级 bootloader（不动 SoftDevice） |
| `*_nosd.hex` | Bootloader + MBR（无 SoftDevice） | JLink 只更新 bootloader |

## nRF52840 Memory Map Reference

```
Address Range           Size    Description
───────────────────────────────────────────────────
0x00000000 - 0x000FFFFF  1MB    Flash
0x10000000 - 0x100001FF  512B   FICR (Factory Info, read-only)
0x10001000 - 0x100013FF  1KB    UICR (User Config, erasable)
0x20000000 - 0x2003FFFF  256KB  RAM
0x40000000+                     Peripherals
0xE0000000+                     ARM CoreSight (debug)
```

### Key FICR Registers

| Address | Name | Description |
|---------|------|-------------|
| `0x10000060` | DEVICEID[0:1] | 64-bit unique device ID |
| `0x100000A4` | DEVICEADDR[0:1] | BLE MAC address |
| `0x10000100` | INFO.PART | Part number (0x52840) |
| `0x10000104` | INFO.VARIANT | Package variant |
| `0x10000110` | INFO.RAM | RAM variant |

### Key UICR Registers

| Address | Name | Description |
|---------|------|-------------|
| `0x10001014` | NRFFW[1] | Bootloader start address |
| `0x10001018` | NRFFW[2] | MBR params page address |
| `0x10001200` | PSELRESET[0:1] | Reset pin selection |
| `0x10001208` | APPROTECT | Access port protection (0xFF=open) |
| `0x1000120C` | NFCPINS | NFC pin config (0xFE=disabled) |

## UF2 Format Notes

UF2 (USB Flashing Format) is a file format designed for flashing via USB mass storage.

### Structure

Each 512-byte block:
```
Offset  Size  Field
0       4     Magic 0 (0x0A324655 "UF2\n")
4       4     Magic 1 (0x9E5D5157)
8       4     Flags
12      4     Target address in flash
16      4     Payload size (usually 256)
20      4     Block number
24      4     Total blocks
28      4     Family ID
32      476   Data (payload + padding)
508     4     Magic End (0x0AB16F30)
```

### Family IDs

| ID | Meaning |
|----|---------|
| `0xADA52840` | Nordic nRF52840 (used by zmk.uf2) |
| `0x239A00B3` | Adafruit nRF52 (used by CURRENT.UF2 backup) |

### CURRENT.UF2 vs zmk.uf2

| | CURRENT.UF2 | zmk.uf2 |
|---|---|---|
| Content | Full flash dump (SoftDevice + App) | Application only |
| Start address | 0x001000 | 0x026000 |
| Family ID | 0x239A00B3 | 0xADA52840 |
| Purpose | Backup / export | Flash new firmware |

## Troubleshooting

### "No probes connected via USB"
- Check USB cable (must be data cable, not charge-only)
- Try different USB port
- Check `system_profiler SPUSBDataType` for J-Link device

### nrfjprog error -256
- This is a J-Link OB clone compatibility issue
- Use `JLinkExe` directly instead of `nrfjprog`
- All scripts in this repo use `JLinkExe`

### Can't connect to target
- Verify SWD wiring (SWDIO, SWCLK, GND, VCC)
- Try connecting RST line
- Check VTref voltage in JLinkExe output (should be ~3.3V)
- If chip is in deep sleep, RST connection is needed

### APPROTECT is enabled (reads as 0x00)
- Chip is read-protected, can't dump firmware
- `erase` command in JLinkExe will clear APPROTECT (but also erases all firmware)
- After erase, re-flash bootloader from scratch

### JLinkExe command file errors ("Unknown command")
- JLinkExe command files don't support `#` comments or `print`
- Each line must be a valid JLink command
- Use bash `echo` for messages, keep `.jlink` files as pure commands
