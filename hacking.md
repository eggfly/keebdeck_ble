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
- [32.768KHz External Crystal](#32768khz-external-crystal)
- [SuperMini NRF52840 上拉电阻问题](#supermini-nrf52840-上拉电阻问题)
- [nRF52840 封装对比: aQFN73 vs QFN48](#nrf52840-封装对比-aqfn73-vs-qfn48)
- [电源控制 (EXT_POWER) 架构](#电源控制-ext_power-架构)
- [BLE 键盘功耗与续航估算](#ble-键盘功耗与续航估算)
- [nRF52840 内置 DC-DC / LDO 与 Zephyr 配置](#nrf52840-内置-dc-dc--ldo-与-zephyr-配置)
  - [DC-DC 开关纹波对 BLE 射频的影响](#dc-dc-开关纹波对-ble-射频的影响)
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

## 32.768KHz External Crystal

E73-2G4M08S1C 模块内置了 32MHz 主晶振（给射频和 CPU 用），但 **32.768KHz 晶振需外接**（引脚 11/XL1 和 13/XL2）。

### 为什么需要外接 32K 晶振

两个原因都有，但**主要是低功耗**。

#### 1. 低功耗（主要原因）

nRF52840 在 System ON/OFF 低功耗模式下会关掉 32MHz 高频晶振，仅靠 32.768KHz 低频时钟源来维持 RTC（实时计数器）和唤醒定时器。nRF52840 内部有一个 LFRC（低频 RC 振荡器）可以替代，但：

- **LFRC 精度差**（~250 ppm vs 外部晶振 ~20 ppm）
- **LFRC 功耗反而更高**（需要周期性校准，校准本身耗电）

对于键盘这种长时间休眠、靠定时器唤醒扫描按键的场景，外部 32K 晶振能显著降低平均功耗。

#### 2. 蓝牙（间接相关）

BLE 协议栈（SoftDevice S140）依赖低频时钟来调度连接事件的定时。如果时钟精度差（用 LFRC），协议栈需要提前更多时间打开接收窗口来补偿漂移，这意味着：

- 射频开启时间更长 → 功耗更高
- 连接稳定性可能受影响

### 结论

模块为了控制成本/体积没有内置 32K 晶振，但对于 BLE 键盘这种低功耗应用，外接一颗是必须的。nice!nano 等成熟方案都会贴这颗晶振。

## SuperMini NRF52840 上拉电阻问题

SuperMini NRF52840（又名 "ProMicro NRF52840"）早期批次存在一个上拉电阻导致的高漏电问题。

> 信息来源: [joric/nrfmicro wiki - Alternatives](https://github.com/joric/nrfmicro/wiki/Alternatives)、[sasodoma/nrf52840-promicro](https://github.com/sasodoma/nrf52840-promicro)（反向工程原理图）、ZMK Discord

### 电路拓扑

该电阻（原理图中标号 **R4**）位于 P-FET (AO3401A) 的栅极和 VDDH 之间，是一个上拉电阻：

```
VDDH ──┬── R4 (上拉) ──┬── P-FET Gate (AO3401A)
        │                │
        │                └── POWER_PIN (P0.13, nRF52840)
        │
        ├── P-FET Source
        │
        └── P-FET Drain ── LDO (ME6211C33) ── EXT_VCC (3.3V 给外设)
```

R4 的作用：MCU 启动时 P0.13 尚未初始化，上拉到 VDDH 让 P-FET 栅极为高电平（P-FET 关断），防止 VCC 在 boot 期间误输出。

### 为什么 5.6K 会漏电

当 ZMK 进入低功耗模式或 VCC cutoff 模式（P0.13 输出低电平）时：

- 5.6K 电阻直接连接在 VDDH 和 GND 之间（通过 P0.13 拉低）
- 漏电 = VDDH / R4 ≈ 3.6V / 5.6K ≈ **643 μA**

这就是为什么早期 SuperMini 睡眠电流高达 ~700 μA 的原因。早期批次复用了 USB CC 线上的 5.1K 电阻料号来省 BOM，导致这个问题。

### 修复时间线

| 时间 | R4 阻值 | 漏电 | 备注 |
|------|---------|------|------|
| 2023-09 ~ 2024-03 | **5.6K** (0402) | ~643 μA | 复用 CC 电阻料号省 BOM |
| **2024-04** | **10M** (0201) | ~0.36 μA | 工厂修复，[ZMK Discord 确认](https://discord.com/channels/719497620560543766/1157825408130101349/1228533671972311060) |
| 2024-09+ (红色/TENSTAR 版) | **500K~600K** | ~6 μA | 不同供应商，也在可接受范围 |

### 现状

**电阻仍然存在，但阻值已从 5.6K 换成 10M（或 500K+）。** 不是去掉了，是换了值：

- 10M 时漏电 = 3.6V / 10M ≈ 0.36 μA（可忽略）
- 功能不变（仍然在 boot 时上拉 P-FET 栅极）
- 栅极充电时间 t = R × C_gate 仍在皮秒级，不影响开关速度

### 如果你拿到了旧批次

可以自行焊接修复：

1. **去焊 R4**（去掉也能工作，只是 boot 时 VCC 会短暂输出）
2. **或替换为 10M**（推荐，0201 封装）

R4 的物理位置在 P-FET 旁边，nice!nano 原理图中同位置用的也是这个上拉。参见反向工程项目 [sasodoma/nrf52840-promicro](https://github.com/sasodoma/nrf52840-promicro) 的 KiCad 原理图。

### 其他已知硬件问题

来自 [nrfmicro wiki](https://github.com/joric/nrfmicro/wiki/ALternatives#supermini-nrf52840) 的总结：

| 问题 | 状态 |
|------|------|
| LED 颜色反了（红=蓝牙，蓝=充电，应该反过来） | 截至 2025-03 仍未修复 |
| 电压分压器 (P0.24) 未贴片，充电时无法测量电池电压 | 未修复 |
| 部分晚期批次用普通硅二极管替代肖特基二极管 (W5)，漏电 60μA vs 4μA | 随批次不同，[#85](https://github.com/joric/nrfmicro/issues/85) |
| 32.768kHz 晶振质量问题 | 可通过 [ZMK 固件配置](https://zmk.dev/docs/troubleshooting/connection-issues#mitigating-a-faulty-oscillator) 缓解 |

## nRF52840 封装对比: aQFN73 vs QFN48

nRF52840 有三种封装。本项目使用的 E73-2G4M08S1C 模组内部是 **aQFN73 (7x7mm)**，引脚最全。如果自己贴片想用更容易焊接的 **QFN48 (6x6mm)**，会丢失以下引脚。

> 数据来源: nRF52840 Product Specification v1.7, Section 7.1 Pin assignments (Table 145 & 146)

### 封装概览

| | aQFN73 (7x7mm) | QFN48 (6x6mm) |
|---|---|---|
| 封装类型 | BGA 风格（底部焊球） | QFN（四边引脚，露铜焊盘） |
| 焊接难度 | 难（需要回流焊/热风枪，无法手工检查焊点） | 较易（引脚可见，可拖焊） |
| 总引脚数 | 73 | 48 |
| GPIO 数量 | **48** | **32** |
| 供电模式 | Normal Voltage + **High Voltage** | **仅 Normal Voltage**（VDD/VDDH 内部短接） |
| USB 硬件 | 有（D+/D-/VBUS） | **无** |

### QFN48 丢失的 GPIO（16 个）

| 丢失引脚 | 说明 | 影响 |
|----------|------|------|
| **P0.16** | GPIO | nice!nano 用作 LED 控制引脚 |
| **P0.25** | GPIO | |
| **P0.27** | GPIO | |
| **P1.01** | GPIO, low frequency I/O | |
| **P1.02** | GPIO, low frequency I/O | |
| **P1.03** | GPIO, low frequency I/O | |
| **P1.04** | GPIO, low frequency I/O | |
| **P1.05** | GPIO, low frequency I/O | |
| **P1.06** | GPIO, low frequency I/O | |
| **P1.07** | GPIO, low frequency I/O | |
| **P1.10** | GPIO, low frequency I/O | |
| **P1.11** | GPIO, low frequency I/O | |
| **P1.12** | GPIO, low frequency I/O | |
| **P1.13** | GPIO, low frequency I/O | |
| **P1.14** | GPIO, low frequency I/O | |
| **P1.15** | GPIO, low frequency I/O | |

规律：**P1 端口几乎全军覆没**，仅保留了 P1.00、P1.08、P1.09。P0 端口丢失 3 个。

### QFN48 丢失的特殊功能引脚

| 丢失引脚 | 功能 | 影响 |
|----------|------|------|
| **D+** | USB D+ | **无法使用 USB 硬件** |
| **D-** | USB D- | **无法使用 USB 硬件** |
| **VBUS** | USB 5V 输入 | 无 USB 3.3V 稳压器输入 |
| **VDDH** | 高压电源输入 | 无法使用 High Voltage 模式 |
| **DCCH** | 高压 DC/DC 输出 | 无高压 DC/DC 转换 |

### QFN48 保留的 GPIO（32 个）

```
P0 端口 (29个):
P0.00  P0.01  P0.02  P0.03  P0.04  P0.05  P0.06  P0.07  P0.08
P0.09  P0.10  P0.11  P0.12  P0.13  P0.14  P0.15  P0.17  P0.18
P0.19  P0.20  P0.21  P0.22  P0.23  P0.24  P0.26  P0.28  P0.29
P0.30  P0.31

P1 端口 (3个):
P1.00  P1.08  P1.09
```

### 对键盘项目的影响

| 方面 | 影响 |
|------|------|
| **USB** | QFN48 **不能用 USB**，只能纯蓝牙。无法 UF2 拖拽烧录，只能用 SWD/DFU |
| **供电** | 无 High Voltage 模式，不能从 VDDH 直接取锂电池电压（3.0~4.2V），需外部 LDO 降压到 VDD 范围 |
| **键盘矩阵** | 32 个 GPIO 对 6R×13C 矩阵（需要 19 个 GPIO）仍然够用 |
| **外设** | I2C/SPI/UART 不受影响（可映射到任意保留的 GPIO） |
| **电池检测** | P0.31/AIN7 和 P0.29/AIN5 仍保留，可做电压分压检测 |

### 结论

QFN48 焊接容易很多，但**丧失 USB 功能**是最大代价。对于纯蓝牙键盘项目，如果能接受 SWD 烧录（或 BLE DFU），QFN48 的 32 个 GPIO 足够驱动键盘矩阵 + I2C 显示屏。但如果需要 USB 有线模式或 UF2 拖拽烧录，必须用 aQFN73。

## 电源控制 (EXT_POWER) 架构

BLE 键盘需要在不用时切断外设电源来省电。nRF52840 方案普遍用一个 GPIO 控制 P-FET 或 LDO 的 EN 引脚来实现。

### 核心问题：MCU 能切断自己的电源吗？

**不能，也不应该。** nice!nano 等方案的关键是有**两条独立的供电路径**：

```
锂电池 3.0~4.2V
    │
    ▼
  VDDH ──┬──→ nRF52840 内部 REG1 (DC-DC) ──→ VDD 1.8V (MCU 核心供电，永远在线)
          │
          └──→ P-FET (AO3401A) ──→ 外部 LDO (ME6217C33) ──→ EXTVCC 3.3V (外设)
                    ↑
                P0.13 控制栅极
```

- **MCU 供电**：电池 → VDDH → 芯片内部 DC-DC → VDD，**始终在线**，P0.13 管不到
- **外设供电**：电池 → VDDH → P-FET → LDO → EXTVCC（VCC 排针），**可被 P0.13 切断**

ZMK 的 `EXT_POWER` 功能切断的只是 LED、OLED、传感器等外设的 3.3V，MCU 自己照常运行维持蓝牙连接。

### 错误设计：单 LDO 同时供电 MCU 和外设

如果电路简化成只有一个 LDO，用 P0.13 控制它的 EN：

```
电池 → 唯一的 LDO → 3.3V → 同时给 VDD 和外设
              ↑
          P0.13 拉低 EN → 全部断电 → MCU 也死了 → P0.13 变高阻 → LDO 恢复？
```

**这是自杀电路。** MCU 拉低 EN → 自己失电 → GPIO 变高阻 → LDO 可能恢复 → MCU 重启 → 又拉低 EN → 无限重启振荡。即使不振荡，MCU 也丢失了所有 RAM 状态（蓝牙连接、按键状态、定时器）。

要让 EXT_POWER 正常工作，**必须保证 MCU 的供电路径不经过它控制的开关**。方案：

1. **用 VDDH 模式**（推荐）：电池直连 VDDH，内部 DC-DC 给 MCU 供电，外部 LDO 只管外设
2. **两个 LDO**：一个始终给 MCU，另一个受控给外设
3. **不做 EXT_POWER**：如果外设功耗可接受，直接省掉这个电路

### 物理开关 vs 软件 EXT_POWER

| | 物理开关 | 软件 EXT_POWER (P0.13) |
|---|---|---|
| **断电范围** | 整个板子（MCU + 外设）全部断电 | 只断外设，MCU 保持运行 |
| **蓝牙状态** | 丢失（重新开机需重连） | 保持（MCU 在深睡眠中维持 bond） |
| **唤醒方式** | 手动拨动开关 | 按键唤醒（GPIO 中断） |
| **睡眠电流** | 0 μA（完全断电） | ~2-5 μA（MCU deep sleep + RTC） |
| **适用场景** | 长期存放、运输、防止意外耗电 | 日常使用中省电（关 LED/OLED） |

**结论：两者不冲突，建议都加。**

- **物理开关**：串联在电池正极，长期不用时彻底断电，防止电池过放
- **EXT_POWER (P0.13)**：日常使用中软件控制外设电源，不影响蓝牙连接

大多数成熟方案（nice!nano、nrfmicro）都同时有物理开关位和 EXT_POWER 控制。

### P0.13 有什么特殊的？

查 nRF52840 datasheet Table 145（aQFN73 引脚分配）：

- P0.13 是**普通 Digital I/O，无任何限制标注**
- 不像很多 P1.xx 引脚有 "Standard drive, low frequency I/O only" 限制
- 支持 High drive strength 配置
- 不是复用功能引脚（不像 P0.09/P0.10 是 NFC，P0.18 可配置为 RESET）

Boot 时 PIN_CNF 寄存器复位值 = 0x00000002：方向=输入，输入缓冲=断开，无上下拉。**P0.13 在 boot 时是高阻态**，所以需要外部上拉电阻保证 P-FET 栅极为确定电平。

选 P0.13 没有硬件上的强制原因——任何普通 GPIO 都能驱动 P-FET 栅极。P0.13 是 nice!nano 确立的事实标准，后续兼容板沿用。

### nice!nano v1→v2 极性变化：从 P-FET 控制到 LDO CE 控制

v1 和 v2 的 active level 从 LOW 变成 HIGH，原因不是加了反相器，而是**控制点从 P-FET 栅极换成了 LDO CE（使能）引脚**。

**nice!nano v1 拓扑（GPIO_ACTIVE_LOW）：**

```
VDDH ─── P-FET (DMP2088LCP3) ─── LDO (AP2112K) ─── EXTVCC
  Source     ↑ Gate                  EN 接 VIN (永远使能)
             │
         P0.13 (POWER_PIN)
```

- P0.13 LOW → P-FET 栅极 LOW → Vgs 很负 → P-FET 导通 → LDO 有 VIN → EXTVCC ON
- P0.13 HIGH → P-FET 关断 → LDO 断电 → EXTVCC OFF
- **控制逻辑：LOW = 开，HIGH = 关 → ACTIVE_LOW**

**nice!nano v2 / SuperMini 拓扑（GPIO_ACTIVE_HIGH）：**

```
VDDH ─── LDO (XC6220/ME6217) ─── EXTVCC
           ↑ CE (使能，active HIGH)
           │
       R4 (10M 上拉到 VDDH)
           │
       P0.13 (POWER_PIN)
```

- P0.13 HIGH → CE HIGH → LDO 使能 → EXTVCC ON
- P0.13 LOW → CE LOW → LDO 关闭 → EXTVCC OFF（此时 VDDH 通过 R4 漏电到 GND）
- **控制逻辑：HIGH = 开，LOW = 关 → ACTIVE_HIGH**
- **P-FET 不再出现在 EXTVCC 通路中**（SuperMini 的 AO3401A 用于 USB/电池供电切换）

**为什么改？**

| | v1 (P-FET 方案) | v2 (LDO CE 方案) |
|---|---|---|
| 元器件 | P-FET + LDO（EN 常开） | 仅 LDO（CE 可控） |
| BOM 数量 | 多一颗 MOSFET | 少一颗 |
| 关断漏电 | P-FET 完全断开 VIN，≈0μA | LDO 自身 shutdown 电流 ~0.1μA |
| 压降 | P-FET Rds_on 损耗 (~50mΩ) | 无 FET 压降 |
| 上拉电阻 | 不需要（或在栅极） | 需要（CE 上拉保证 boot 时默认开启） |

v2 方案更简洁：新一代 LDO（XC6220 shutdown <1μA，ME6217 shutdown ~0.1μA）的关断电流足够低，不再需要用 P-FET 彻底切断供电。

> SuperMini 的 R4（10M 上拉）和 5.6K 漏电问题也由此解释：R4 连接在 LDO CE 和 VDDH 之间。P0.13 拉低关闭 LDO 时，电流从 VDDH 通过 R4 流向 GND。5.6K 时 3.6V/5.6K = 643μA；换 10M 后 3.6V/10M = 0.36μA。

### 各板子电源控制引脚对比

| 板子 | Power Pin | Active Level | 控制方式 |
|------|-----------|-------------|---------|
| **nice!nano v1** | P0.13 | LOW | P-FET 栅极 |
| **nice!nano v2** | P0.13 | HIGH | LDO CE 引脚 |
| **SuperMini** | P0.13 | HIGH | LDO CE (ME6217) |
| **Mikoto** | P0.13 | HIGH | |
| **52840nano V2** | P0.13 | HIGH | |
| **Kinesis Adv360 Pro** | P0.13 | HIGH | |
| **nrfmicro** (全系列) | P1.09 | LOW | P-FET 栅极 |
| **Puchi-BLE** | P1.09 | LOW | 沿用 nrfmicro |
| **BlueMicro840** | P0.12 | HIGH | |
| **Pillbug** | P1.07 | LOW | |
| **nice!60** | P0.05 | LOW | |
| **XIAO BLE** | P0.14 | LOW | open-drain 模式 |
| **Glove80 LH / RH** | P0.31 / P0.19 | HIGH | 左右手不同引脚 |

> P0.13 是最流行的选择。ACTIVE_LOW 的板子多用 P-FET 方案，ACTIVE_HIGH 的板子多用 LDO CE 方案。

## BLE 键盘功耗与续航估算

> 数据来源: nRF52840 Product Specification v1.7, Section 5.2 Current consumption

### nRF52840 各状态功耗（DC-DC 模式，3V 供电，25°C）

| 状态 | 电流 | 说明 |
|------|------|------|
| **System OFF** | 0.40 μA | 无 RAM 保持，仅 reset 唤醒 |
| **System ON 深睡眠** | 1.29 μA | VDDH 供电，无 RAM，REGO=3.3V，任意事件唤醒 |
| **System ON 深睡眠 + RAM** | 2.35 μA | 全 256KB RAM 保持，任意事件唤醒 |
| **System ON + RTC** | 3.16 μA | 全 RAM + RTC（LFRC 时钟），用于定时唤醒 |
| **CPU 运行** | 3.3 mA | 64MHz，DC-DC，从 flash 执行 |
| **BLE TX 0dBm** | 6.40 mA | 1 Mbps BLE，DC-DC |
| **BLE RX** | 6.26 mA | 1 Mbps BLE，DC-DC |
| **BLE TX 8dBm** | 16.40 mA | 最大功率发射 |

### BLE 键盘各工作模式估算（无背光）

假设条件：背光 LED 关闭，使用外部 32K 晶振（LFXO），DC-DC 模式。

| 工作模式 | 平均电流 | 计算依据 |
|----------|----------|----------|
| **深睡眠**（无 BLE 连接） | ~3-5 μA | MCU System ON + RAM + RTC + 外围漏电 |
| **空闲已连接**（BLE 保持，无按键） | ~100-200 μA | 连接间隔 75ms，每次射频 ~1.5ms，6.3mA × 1.5/75 ≈ 126 μA + 基础 3μA |
| **打字中**（BLE 低延迟） | ~2-3 mA | 连接间隔 7.5-15ms，矩阵扫描 + CPU 处理 + 射频 |

> ZMK 固件在无按键操作一段时间后，会自动从「打字中」→「空闲已连接」→「深睡眠」逐级降低功耗。

### 8 颗背光 LED + 升压驱动功耗分析

键盘背光使用白色 LED（Vf ≈ 3.0-3.2V），锂电池电压 3.0-4.2V 不够直接驱动串联 LED，需要升压 DC-DC LED 驱动芯片。

#### LED 驱动拓扑

```
电池 3.0~4.2V ─→ Boost LED Driver ─→ 升压到 ~6.4V ─→ LED 串联组
                        ↑                              │
                   PWM 调光 (MCU GPIO)            2 串 × 4 并 (2S4P)
                   EN 使能 (EXT_POWER)            每串 2 颗 LED
```

**推荐配置：2S4P**（2 颗串联 × 4 路并联）
- 每串 Vf = 3.2V × 2 = 6.4V
- 升压芯片输出：~6.8V（含余量）
- 每路独立限流，通过 PWM 调占空比实现调光

#### 常见升压 LED 驱动 IC

| 芯片 | 输入 | 输出 | 效率 | Iq (工作) | Iq (关断) | 封装 | 备注 |
|------|------|------|------|-----------|-----------|------|------|
| TPS61160 | 3.0-5.5V | 最高 27V | ~87% | 25 μA | 1 μA | SOT-23-5 | 经典 LED boost，PWM 调光 |
| TPS61169 | 2.7-5.5V | 最高 18V | ~85% | 25 μA | 1 μA | SOT-23-5 | 低 EMI 版本 |
| SGM3140 | 2.5-5.5V | 可调 | ~80% | 10 μA | <1 μA | SOT-23-6 | 超低成本，常用于手电 |
| LP5907 + 分立 boost | - | - | - | - | - | - | 需更多元件，不推荐 |

#### 8 颗白色 LED 功耗计算

| 亮度等级 | 每颗 LED 电流 | 总 LED 电流 | LED 功耗 | 电池端电流 (η=85%) | 说明 |
|----------|-------------|-----------|---------|-------------------|------|
| **全亮** | 20 mA | 160 mA | 6.4V × 80mA × 2串 = 1024 mW | **~33 mA** @3.7V | 室内偏亮，伤眼 |
| **中亮** | 10 mA | 80 mA | 512 mW | **~16 mA** | 日常使用 |
| **低亮** | 3 mA | 24 mA | 154 mW | **~5 mA** | 暗光环境 |
| **微亮** | 1 mA | 8 mA | 51 mW | **~2 mA** | 夜间定位 |
| **关闭** | 0 | 0 | 0 | **~1 μA** | 驱动 IC shutdown |

> 计算方式：电池端电流 = LED 功耗 / (Vbat × η) = Vout × Iout / (3.7V × 0.85)
> 注意：2S4P 拓扑中，Iout = 4 路 × 每路电流，Vout ≈ 6.4V

### 每日功耗模型

#### 场景 A：无背光（EXT_POWER 关闭）

```
每日消耗 = 3h × 2.5mA + 5h × 0.15mA + 16h × 0.005mA
         = 7.50 + 0.75 + 0.08
         = 8.33 mAh/天
```

#### 场景 B：背光低亮（3mA/LED），打字时开启

```
每日消耗 = 3h × (2.5 + 5)mA + 5h × 0.15mA + 16h × 0.005mA
         = 22.50 + 0.75 + 0.08
         = 23.33 mAh/天
```

#### 场景 C：背光中亮（10mA/LED），全天开启

```
每日消耗 = 3h × (2.5 + 16)mA + 5h × (0.15 + 16)mA + 16h × 0.005mA
         = 55.50 + 80.75 + 0.08
         = 136.33 mAh/天
```

### 常见电池续航估算

| 电池型号 | 容量 | 无背光 | 低亮打字时开 | 中亮全天开 |
|----------|------|--------|------------|----------|
| 301230 | 110 mAh | ~13 天 | ~5 天 | <1 天 |
| 401230 | 130 mAh | ~16 天 | ~6 天 | ~1 天 |
| 502030 | 250 mAh | ~30 天 | ~11 天 | ~2 天 |
| 503035 | 500 mAh | ~60 天 | ~21 天 | ~4 天 |
| 603450 | 1000 mAh | ~120 天 | ~43 天 | ~7 天 |
| 704060 | 2000 mAh | ~240 天 | ~86 天 | ~15 天 |

> **关键结论**：背光 LED 即使只有 8 颗，在中亮以上也会成为功耗主导。建议：
> - 默认关闭背光，按需开启
> - 使用 PWM 调光，低亮（1-3mA/LED）足够暗光环境使用
> - 设置自动熄灭超时（30 秒无操作关背光）
> - 升压驱动 IC 的 EN 引脚必须接 EXT_POWER，深睡眠时完全关断（<1μA）

### 影响续航的关键因素

| 因素 | 影响 | 建议 |
|------|------|------|
| **背光 LED 亮度** | 低亮 ~5mA vs 中亮 ~16mA vs 全亮 ~33mA | PWM 调光 + 自动熄灭超时 |
| **背光开启时长** | 全天开 vs 仅打字时开 | 设 30s 超时自动关闭 |
| **升压驱动 IC 关断电流** | 工作 ~25μA vs shutdown ~1μA | EN 接 EXT_POWER |
| **OLED 显示屏** | +10-20 mA | 设置自动熄屏超时 |
| **BLE 连接间隔** | 7.5ms (低延迟) vs 75ms (省电) | ZMK 自动切换 |
| **外部 32K 晶振** | LFXO vs LFRC：影响睡眠时校准功耗 | 必须贴外部晶振 |
| **DC-DC vs LDO** | DC-DC 效率 >80%，LDO ~50% | E73 参考设计已用 DC-DC |
| **上拉电阻漏电** | SuperMini 旧批次 R4=5.6K 漏 643μA | 确认 R4 ≥ 10M |
| **EXT_POWER LDO 关断电流** | XC6220 <1μA，ME6217 ~0.1μA | 选低 Iq 的 LDO |

## nRF52840 内置 DC-DC / LDO 与 Zephyr 配置

### 两级稳压器架构

nRF52840 内部有 **REG0** 和 **REG1** 两级稳压器，每级都可以选择 LDO 或 DC-DC 模式：

```
锂电池 3.0~4.2V
  │
  ▼ VDDH
┌─────────────────────────────────────┐
│  REG0 (高压级)                       │
│  VDDH (2.5-5.5V) → VDD             │
│  输出电压可配: 1.8/2.1/2.4/2.7/3.0/3.3V │
│  外供能力: 最大 25mA                 │
│  控制寄存器: DCDCEN0 (0x40000580)    │
│  外部电感引脚: DCCH                  │
└──────────┬──────────────────────────┘
           ▼ VDD
┌─────────────────────────────────────┐
│  REG1 (核心级)                       │
│  VDD → 1.3V 核心电压                │
│  输出到 DEC4 引脚                    │
│  控制寄存器: DCDCEN (0x40000578)     │
│  外部电感引脚: DCC                   │
└─────────────────────────────────────┘
```

### 两种供电模式

| 模式 | 条件 | 使用的稳压器 | 典型场景 |
|------|------|------------|---------|
| **Normal Voltage** | VDD 与 VDDH 短接，1.7-3.6V | 仅 REG1 | CR2032 纽扣电池、QFN48 封装 |
| **High Voltage** | VDDH 2.5-5.5V，VDD 由 REG0 输出 | REG0 + REG1 | **LiPo 电池 (3.7V)**、USB 5V |

> QFN48 封装的 VDD 与 VDDH 内部短接，只能用 Normal Voltage 模式。aQFN73 和 E73 模组支持 High Voltage 模式。

### REG0 输出电压配置（UICR REGOUT0, 地址 0x10001304）

| REGOUT0 值 | 输出电压 | 备注 |
|-----------|---------|------|
| 0 | 1.8V | |
| 1 | 2.1V | |
| 2 | 2.4V | |
| 3 | 2.7V | |
| 4 | 3.0V | |
| 5 | **3.3V** | 推荐：可同时给外部传感器/LED 供 3.3V |
| 7 (默认) | 1.8V | 空白芯片默认值 |

> 配置的输出电压不能大于 VDDH - 0.3V（最小压差要求）。

### 为什么 VDD 可以改成 3.3V？什么时候需要改？

#### 片内反馈电阻，寄存器选档

REG0 和 REG1 的反馈网络**全部集成在芯片内部**，不需要外部电阻分压器。这和普通外部 DC-DC（如 TPS63020）不同——那些需要两颗外部电阻设定输出电压。

nRF52840 的做法是：片内有多组反馈电阻，通过 UICR REGOUT0 寄存器选择接入哪组，实现输出电压切换。写寄存器 = 换电阻档位：

```
UICR REGOUT0 = 7 (默认)  →  片内选通 1.8V 反馈网络  →  VDD = 1.8V
UICR REGOUT0 = 5          →  片内选通 3.3V 反馈网络  →  VDD = 3.3V
```

> 修改 UICR 需要先擦除再写入（NVM 操作），且**写入后必须复位才生效**。通常在 bootloader 中完成一次即可。

#### 片内所有电压一览

```
锂电池 3.7V
  │
  ▼ VDDH (2.5-5.5V)
  │
  ├─ REG0 ──→ VDD = 1.8V (默认) / 可配为 3.3V
  │            ↑ 通过 UICR REGOUT0 寄存器选档
  ▼ VDD
  │
  └─ REG1 ──→ DEC4 = 1.3V (固定，不可配置，给 CPU 核心)
```

| 引脚 | 电压 | 可配置？ | 用途 |
|------|------|---------|------|
| VDDH | 2.5-5.5V | 外部输入 | 电池/USB 输入 |
| **VDD** | **1.8V 默认 / 可改 3.3V** | **是 (REGOUT0)** | MCU I/O 电平 + 外供 |
| DEC1 | 1.1V | 固定 | 核心逻辑 |
| DEC2 | 1.3V | 固定 | 射频电路 |
| **DEC4** | **1.3V** | 固定 | REG1 输出，CPU 核心供电 |
| DEC5 | 1.3V | 固定 | 射频电路 |
| DECUSB | 3.3V | 固定 | USB PHY |

> DEC1~DEC5 的电压全部由片内稳压器产生，固定不可调，外部只需接去耦电容。

#### 什么情况需要改成 3.3V？

**核心原因：VDD 同时决定了 GPIO 的输出电平。** nRF52840 的 GPIO 输出高电平 = VDD 电压。

| VDD 电压 | GPIO 输出高电平 | 后果 |
|---------|---------------|------|
| 1.8V (默认) | 1.8V | 很多 3.3V 外设的 VIH 阈值 > 1.8V，**通信失败** |
| **3.3V** | **3.3V** | 兼容绝大部分 3.3V 外设 |

**需要改 3.3V 的场景：**

| 场景 | 原因 |
|------|------|
| 外接 3.3V 传感器（加速度计、OLED 等） | I2C/SPI 信号电平必须匹配 |
| 驱动 WS2812 RGB LED | WS2812 的 VIH > 0.7×VDD，1.8V 信号驱不动 |
| 外接 SD 卡 | SD 卡标准 3.3V 信号 |
| 给外部电路从 VDD 引脚取电 | REG0 最大外供 25mA @3.3V |
| 与 nice!nano 兼容的扩展板配合 | nice!nano 生态默认 VDD = 3.3V |

**可以保持 1.8V 的场景：**

| 场景 | 原因 |
|------|------|
| 纯 MCU 运行 + BLE（无外设） | 片内射频不走 VDD |
| 所有外设都支持 1.8V 电平 | 少数传感器支持（如某些 IMU） |
| 追求极致低功耗 | 1.8V 时 REG0 效率更高（压差更大，DC-DC 更高效） |

#### nice!nano / SuperMini 的做法

nice_nano bootloader 在初始化时会检查并写入 REGOUT0 = 3.3V：

```c
// Adafruit nRF52 Bootloader 中的代码
if ((NRF_UICR->REGOUT0 & UICR_REGOUT0_VOUT_Msk) != UICR_REGOUT0_VOUT_3V3) {
    NRF_NVMC->CONFIG = NVMC_CONFIG_WEN_Wen;
    while (NRF_NVMC->READY == NVMC_READY_READY_Busy) {}
    NRF_UICR->REGOUT0 = UICR_REGOUT0_VOUT_3V3;  // 值 = 5
    NRF_NVMC->CONFIG = NVMC_CONFIG_WEN_Ren;
    NVIC_SystemReset();  // 必须复位才生效
}
```

所以如果你用 nice_nano bootloader，VDD 已经是 3.3V 了。但如果用裸芯片从零开始（无 bootloader），第一次上电 VDD = 1.8V，需要在你自己的 bootloader 或固件初始化中配置。

#### 为什么默认不直接是 3.3V？

Nordic 选择 1.8V 作为默认值是因为：

1. **安全**：VDDH 最低 2.5V 时，1.8V 输出有足够压差（0.7V > 0.3V 最小要求），3.3V 输出在 VDDH < 3.6V 时不满足压差要求
2. **通用**：1.8V 是很多 SoC 的标准 I/O 电压
3. **省电**：VDD 越低，片内数字电路功耗越低

对于键盘项目（LiPo 3.0-4.2V 供电 + 外接 3.3V 传感器/LED），改成 3.3V 是必须的。

### LDO 与 DC-DC 的启动顺序

芯片上电时**永远先用 LDO**，因为 DCDCEN 寄存器复位值 = 0。这保证了即使 PCB 没焊电感也不会砖化：

```
上电 → LDO 模式启动（不需要电感）
  │
  ▼ 固件运行
  │
  ├── 检测到 PCB 有电感 → 写 DCDCEN=1 → 切换到 DC-DC 模式（省电 ~45%）
  │
  └── PCB 没焊电感 → 不写 DCDCEN → 继续用 LDO（功耗高但正常工作）
```

**焊了电感但未启用 DC-DC 时**：电感在 DC 下等于一根导线（阻抗 ≈ 0Ω），对 LDO 工作没有任何影响。电感只有在 DC-DC 的 MHz 级开关频率下才起储能/滤波作用。

**未焊电感但启用了 DC-DC 时**：DC-DC 开关输出没有电感滤波 → 1.3V 核心电压崩溃 → 芯片死机 → 每次上电固件都会再次启用 DC-DC → **砖化**（需要 SWD 擦除救回）。

### DC-DC vs LDO 功耗实测对比

| 场景 | DC-DC | LDO | 节省比例 |
|------|-------|-----|---------|
| CPU @64MHz (CoreMark, Flash) | **3.3 mA** | 6.3 mA | **48%** |
| CPU @64MHz (CoreMark, RAM) | **2.8 mA** | 5.2 mA | **46%** |
| BLE TX @0dBm, 1Mbps | **6.4 mA** | 10.8 mA | **41%** |
| BLE TX @8dBm (最大功率) | **16.4 mA** | — | — |
| BLE RX @1Mbps | **6.26 mA** | 10.1 mA | **38%** |
| CPU + TX @0dBm 同时 | **8.1 mA** | 15.4 mA | **47%** |
| CPU + RX 同时 | **8.6 mA** | 16.2 mA | **47%** |
| CPU 能效 | **52 μA/MHz** | ~98 μA/MHz | **47%** |

**结论：DC-DC 模式在所有活跃场景下都比 LDO 省电约 40-48%，对电池供电的键盘项目是必须的。**

### DC-DC 开关纹波对 BLE 射频的影响

常见疑问：两级 DC-DC 的 PWM 开关纹波会不会干扰 2.4GHz BLE 射频？

**结论：几乎没有可测量的影响。** Nordic 的设计让 DC-DC 和射频同时运行，不需要在射频收发时关闭 DC-DC。

#### 证据：datasheet 不区分 DC-DC/LDO 下的灵敏度

BLE 接收灵敏度 **-95 dBm**（1Mbps），datasheet 中没有分别给出 DC-DC 和 LDO 两种条件下的灵敏度数值。如果 DC-DC 会导致可测量的灵敏度下降，Nordic 必须分别标注。不区分 = 差异在测量误差以内。

#### 三层隔离机制

```
                    nRF52840 内部
┌─────────────────────────────────────────────┐
│                                             │
│  DC-DC 开关节点 (~1-4 MHz)                   │
│       │                                     │
│       ▼ 外部 10μH 电感滤波                   │  ← 第一层：LC 低通滤波
│       │                                     │
│    VDD / 1.3V (REG1 输出)                    │
│       │                                     │
│    内部独立 LDO ──→ 1.1V (DEC1, 射频模拟)    │  ← 第二层：射频有独立稳压器
│    内部独立 LDO ──→ 1.3V (DEC2/5, 射频数字)  │
│       │                                     │
│    VSS_PA (专用射频地引脚)                    │  ← 第三层：专用地平面隔离
│                                             │
└─────────────────────────────────────────────┘
```

**第一层 — 频率差距 + LC 滤波**：DC-DC 开关频率约 1-4 MHz，BLE 在 2400 MHz，差了 3 个数量级。10μH 电感 + 去耦电容组成的 LC 滤波器把开关纹波压到极低。高次谐波要到达 2.4GHz 需要经过 600+ 次倍频，幅度早已衰减到噪底以下。

**第二层 — 射频有独立内部稳压器**：射频前端不是直接从 REG1 取电。DEC1（1.1V）和 DEC2/DEC5（1.3V）是射频模块自己的内部 LDO 输出，从 REG1 的 1.3V 进一步稳压，再次隔离 DC-DC 纹波。

**第三层 — 专用射频地引脚**：VSS_PA 是射频功放的独立地引脚，低阻抗直连地平面，避免 DC-DC 开关电流的地弹噪声通过共阻抗耦合到射频回路。

#### 射频功耗对比：DC-DC 让射频也省电约 50%

DC-DC 不仅不干扰射频，还因为高效降压让射频功耗大幅降低：

| 射频场景 | DC-DC (3V) | LDO (3V) | 节省 |
|---------|-----------|---------|------|
| TX @+8dBm | 14.8 mA | 32.7 mA | **55%** |
| TX @+4dBm | 9.6 mA | 21.4 mA | **55%** |
| TX @0dBm | 4.8 mA | 10.6 mA | **55%** |
| TX @-4dBm | 3.1 mA | 8.1 mA | **62%** |
| TX @-20dBm | 2.7 mA | 5.6 mA | **52%** |
| RX 1Mbps BLE | 4.6 mA | 9.9 mA | **54%** |
| RX 2Mbps BLE | 5.2 mA | 11.1 mA | **53%** |

> 射频本身消耗的功率不变，省电来自 DC-DC 高效降压（效率 ~85%，把 3.7V 降到 1.3V），比 LDO（效率 = 1.3/3.7 ≈ 35%）少浪费大量能量。

#### 对 E73 模组用户的注意事项

E73 模组内部已包含 RF 匹配网络、天线（或天线引脚）、大部分 DEC 去耦电容。模组外部需要关注的：

| 事项 | 说明 |
|------|------|
| REG1 DCC 电感 | E73 模组通常已包含，需确认模组手册 |
| REG0 DCCH 电感 | High Voltage 模式需在模组外部焊接 10μH，**尽量靠近 DCCH 引脚** |
| DCCH 电感位置 | **远离模组天线区域**，缩短开关电流回路面积 |
| 地平面 | 模组下方和周围保持完整地平面，不要被 DC-DC 走线切割 |

### 睡眠电流（不受 DC-DC/LDO 选择影响，DC-DC 自动关闭）

| 状态 | 电流 | 说明 |
|------|------|------|
| System OFF, 无 RAM | **0.40 μA** | 最低功耗 |
| System OFF, 全 RAM | 1.86 μA | |
| System ON, 无 RAM, 事件唤醒 | 0.97 μA | |
| System ON, 全 RAM + RTC | 3.16 μA | 键盘深睡眠典型值 |
| System OFF, High Voltage 5V VDDH | 0.95 μA | USB 供电时 |

### 硬件设计要点

#### DEC 引脚完整接法

| 引脚 | aQFN73 位置 | 电压 | 去耦电容 | 备注 |
|------|------------|------|---------|------|
| DEC1 | C1 | 1.1V | 100nF (0402) | 核心逻辑内部稳压器 |
| DEC2 | A18 | 1.3V | 100nF (0402) | 射频数字 |
| DEC3 | D23 | — | 100nF (0402) | 通用去耦 |
| **DEC4** | **B5** | **1.3V** | **1μF (共用)** | **必须连到 DEC6 (E24)** |
| DEC5 | N24 | 1.3V | 100nF (0402) | 射频数字 |
| **DEC6** | **E24** | **1.3V** | ↑ 和 DEC4 共用 | **必须连到 DEC4 (B5)** |
| DECUSB | — | 3.3V | 100nF (0402) | USB PHY |

> DEC4 和 DEC6 是同一条 1.3V 内部稳压器轨道从两个引脚引出。在原理图中用一个网络 `DEC4_6` 连接，共用一颗去耦电容。Nordic 参考设计和 MakerDiary nRF52840 Connect Kit 都是这么连的。

#### 必须的外部元件（Config 4 参考设计 BOM）

启用 DC-DC **必须**连接外部 LC 滤波器，否则芯片无法工作（包括无法 SWD 调试）：

| 引脚 | 元件 | 说明 |
|------|------|------|
| **DCC → L2 → (C15/C16) → L3 → VDD** | L2=10μH + L3=15nH + C15=1μF + C16=47nF | REG1 DC-DC 二级滤波（见下文详解） |
| **DCCH ↔ VDDH** | 10μH 电感 | REG0 DC-DC 必须（仅 High Voltage 模式） |
| VDD | 4.7μF MLCC | 去耦 |
| DEC4_6 | 1μF MLCC | DEC4 + DEC6 共用去耦 |

> **警告**：不要在没有连接外部电感的情况下在固件中启用 DC-DC，否则会导致设备砖化，包括无法 SWD 调试！

#### REG1 DC-DC 的两颗电感：为什么 L2 (10μH) 和 L3 (15nH) 串联？

Nordic 参考设计 Config 4 中，DCC 到 VDD 之间不是简单的一颗电感，而是二级滤波拓扑：

```
DCC (pin B3)                                              VDD nRF
    │                                                        │
    └── L2 (10μH) ──┬── L3 (15nH) ──────────────────────────┘
       DC-DC 主储能   │    高频 EMI 滤波
                     ├── C15 (1.0μF) ── GND    中频旁路
                     └── C16 (47nF)  ── GND    高频旁路
```

两颗电感的作用完全不同：

| 电感 | 值 | 封装 | 作用 | 工作频段 |
|------|-----|------|------|---------|
| **L2** | **10μH** | 0603 | DC-DC **主储能电感**，buck 转换器核心元件，开关期间存储/释放能量 | ~1-4 MHz (开关基频) |
| **L3** | **15nH** | 0402 高频电感 | **EMI 高频滤波器**，阻隔开关噪声的高次谐波到达 VDD | >100 MHz |

**为什么 L2 一颗不够？**

L2 (10μH) 对开关基频（1-4MHz）的纹波滤波效果很好，但 10μH 电感绕线多、寄生电容大，在几十 MHz 以上会到达自谐振频率，阻抗反而下降，高频谐波会"穿过去"到 VDD：

```
阻抗对比：

           L2 (10μH)          L3 (15nH)
           ─────────          ──────────
@ 1 MHz    62.8 Ω  ← 主战场   0.094 Ω  ← 几乎透明
@ 10 MHz   628 Ω              0.94 Ω
@ 100 MHz  ↓ 自谐振，阻抗崩塌  9.4 Ω    ← 开始起作用
@ 500 MHz  寄生电容主导        47 Ω     ← 明显衰减
@ 2.4 GHz  基本短路            226 Ω    ← 有效阻隔 BLE 频段噪声
```

L3 (15nH) 体积极小（0402），寄生电容极低，自谐振频率在 GHz 级，高频特性好。它和 C15/C16 组成**二级 π 滤波器**：

```
DCC（脏）                                    VDD（干净）
  │                                            │
  L2 (10μH) ── 滤掉 1-4MHz 开关基波纹波         │
  │                                            │
  ├── C15 (1μF)  ── GND   旁路中频噪声          │
  ├── C16 (47nF) ── GND   旁路高频噪声          │
  │                                            │
  L3 (15nH) ── 滤掉残余 >100MHz 高次谐波 ───────┘
```

> 这就是上一节"三层隔离"中第一层的具体实现。通过两颗不同量级的电感覆盖从 MHz 到 GHz 的完整频段，确保 VDD 上的纹波对 2.4GHz BLE 射频没有可测量的干扰。

#### 四种配置组合

| 配置 | 供电模式 | REG0 | REG1 | 外部电感 | 适用场景 |
|------|---------|------|------|---------|---------|
| 1 | Normal V, LDO | 禁用 | LDO | 无 | 最简单，原型验证 |
| 2 | Normal V, DC-DC | 禁用 | **DC-DC** | DCC↔DEC4 | 纽扣电池省电 |
| 3 | High V, LDO | LDO | LDO | 无 | LiPo 供电，不省电 |
| **4** | **High V, DC-DC** | **DC-DC** | **DC-DC** | DCCH↔VDDH + DCC↔DEC4 | **LiPo 供电，最省电（推荐）** |

### Zephyr / ZMK DeviceTree 配置

#### 硬件与 DTS 的对应关系

这是关键：**DTS 中的 `&reg0` / `&reg1` 节点直接映射到 nRF52840 硬件寄存器**，而不是软件抽象。你的 PCB 上有没有焊电感，决定了 DTS 中能不能启用对应的 DC-DC。

```
硬件 PCB                              Zephyr DTS
─────────                              ──────────
DCCH 引脚焊了 10μH 到 VDDH   ←对应→   &reg0 { status = "okay"; }
DCC  引脚焊了 10μH 到 DEC4    ←对应→   &reg1 { regulator-initial-mode = <NRF5X_REG_MODE_DCDC>; }
```

#### REG1：核心级 DC-DC（所有板子都应该启用）

在板级 `.dts` 文件中：

```dts
&reg1 {
    regulator-initial-mode = <NRF5X_REG_MODE_DCDC>;
};
```

**前提**：PCB 上 DCC 和 DEC4 之间必须连接了 10μH 电感。

这是 ZMK 生态中最普遍的配置，以下板子全部启用了此项：

| 板子 | DTS 文件 |
|------|---------|
| nice!nano | `app/module/boards/nicekeyboards/nice_nano/nice_nano.dts` |
| nrfmicro (全系列) | `app/module/boards/joric/nrfmicro/nrfmicro_nrf52840.dts` |
| Glove80 | `app/boards/moergo/glove80/glove80.dtsi` |
| Kinesis Adv360 Pro | `app/boards/kinesis/adv360pro/adv360pro.dtsi` |
| nice!60 | `app/boards/nicekeyboards/nice60/nice60_nrf52840_zmk.dts` |
| Mikoto | `app/module/boards/zhiayang/mikoto/mikoto.dts` |
| PolarityWorks CKP | `app/boards/polarityworks/common/ckp-base.dtsi` |

#### REG0：高压级 DC-DC（仅 High Voltage 模式的板子）

```dts
&reg0 {
    status = "okay";
};
```

**前提**：
1. 使用 aQFN73 封装（或含 aQFN73 的模组如 E73）
2. VDDH 引脚独立接电池/USB（不与 VDD 短接）
3. DCCH 和 VDDH 之间连接了 10μH 电感

> nice!nano 在高压模式下工作（LiPo 接 VDDH），但其 DTS 中**未启用 REG0 DC-DC**（即 REG0 用 LDO 模式）。如果你自己设计 PCB 并焊了 DCCH 电感，可以额外启用 `&reg0` 进一步省电。

#### REG0 输出电压配置

REG0 的输出电压通过 UICR 的 REGOUT0 寄存器配置，在 Zephyr 中：

```c
/* 在 bootloader 或应用初始化中写 UICR */
if ((NRF_UICR->REGOUT0 & UICR_REGOUT0_VOUT_Msk) != UICR_REGOUT0_VOUT_3V3) {
    NRF_NVMC->CONFIG = NVMC_CONFIG_WEN_Wen;
    while (NRF_NVMC->READY == NVMC_READY_READY_Busy) {}
    NRF_UICR->REGOUT0 = UICR_REGOUT0_VOUT_3V3;  // 值 = 5
    NRF_NVMC->CONFIG = NVMC_CONFIG_WEN_Ren;
    NVIC_SystemReset();  // UICR 变更需要复位生效
}
```

> nice_nano bootloader 默认将 REGOUT0 设为 3.3V。如果你用裸芯片从空白状态启动，默认是 1.8V，需要在 bootloader 中配置。

### 自己设计 PCB 的 Checklist

根据你使用模组（E73）还是裸芯片（aQFN73），硬件和 DTS 需要配套：

#### 方案 A：E73-2G4M08S1C 模组（推荐）

```
模组引脚      外部电路              DTS 配置
────────      ────────              ────────
VDDH ──────── LiPo 电池正极
DCCH ──┤10μH├── VDDH               &reg0 { status = "okay"; }
VDD  ──────── 4.7μF 到 GND
DCC  ──┤10μH├── DEC4               &reg1 { regulator-initial-mode = <NRF5X_REG_MODE_DCDC>; }
DEC4 ──────── 1μF 到 GND
GND  ──────── 电池负极
```

模组内部已包含：32MHz 主晶振、RF 匹配网络、天线（或天线引脚）。外接：32.768KHz 晶振（XL1/XL2）+ 两颗电感 + 去耦电容。

#### 方案 B：nRF52840 aQFN73 裸芯片

除了方案 A 的所有元件，还需要额外：

| 额外元件 | 说明 |
|---------|------|
| 32MHz 晶振 + 2×12pF 负载电容 | XC1/XC2 引脚 |
| 32.768KHz 晶振 | XL1/XL2 引脚 |
| RF 匹配网络 (π 型) | ANT 引脚，参考 Nordic 参考设计 |
| 天线（PCB 天线或陶瓷天线） | |
| DEC1~DEC6 去耦电容 (100nF×6) | 各电源引脚 |
| VBUS 去耦电容 (如果用 USB) | |

#### DTS 完整配置模板（keebdeck BLE 版）

```dts
/* keebdeck_ble.dts - 基于 E73 模组 + LiPo 电池 */

/* 启用 REG0 高压 DC-DC (DCCH 电感已焊) */
&reg0 {
    status = "okay";
};

/* 启用 REG1 核心 DC-DC (DCC 电感已焊) */
&reg1 {
    regulator-initial-mode = <NRF5X_REG_MODE_DCDC>;
};

/* GPIO 控制外设电源 */
/ {
    ext_power {
        compatible = "zmk,ext-power-generic";
        control-gpios = <&gpio0 13 GPIO_ACTIVE_HIGH>;  /* P0.13, LDO CE 方案 */
    };
};
```

### 常见踩坑

| 问题 | 原因 | 解决 |
|------|------|------|
| 启用 DC-DC 后芯片砖化 | PCB 没焊电感 | 必须先焊电感再改 DTS；救砖用 SWD 擦除重刷 |
| REG0 输出 1.8V 不是 3.3V | UICR REGOUT0 未配置 | 在 bootloader 中写 REGOUT0 = 5 (3.3V) |
| High Voltage 模式不工作 | VDD 和 VDDH 短接了 | 检查 PCB，High Voltage 模式要求 VDD 仅由 REG0 输出 |
| 功耗比预期高 | DTS 中忘记启用 DC-DC | 检查 `regulator-initial-mode` 是否设为 DCDC |
| QFN48 无法用 High Voltage | VDD/VDDH 内部短接 | QFN48 只能用 Normal Voltage + REG1 DC-DC |

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

---

## IMU 传感器 (QMI8658A) DTS 配置

> 参考：`zephyr/dts/bindings/sensor/qst,qmi8658a.yaml`

### DTS Binding 官方示例

```dts
#include <zephyr/dt-bindings/gpio.h>

qmi8658a@6b {
    compatible = "qst,qmi8658a";
    reg = <0x6b>;
    accel-fs = <4>;      /* ±4g */
    gyro-fs = <512>;     /* ±512 dps */
    accel-odr = <896>;   /* 896 Hz */
    gyro-odr = <896>;    /* 896 Hz */
    int-gpios = <&gpio0 10 GPIO_ACTIVE_HIGH>;
    int-pin = <2>;       /* 使用 INT2 */
};
```

### 各属性说明

| 属性 | 类型 | 必选 | 说明 |
|------|------|------|------|
| `compatible` | string | 是 | 必须为 `"qst,qmi8658a"` |
| `reg` | int | 是 | I2C 地址：`0x6a`（SA0 悬空/上拉）或 `0x6b`（SA0 接 GND） |
| `accel-fs` | int | 否 | 加速度计量程，可选 2/4/8/16 (g)，默认 4 |
| `gyro-fs` | int | 否 | 陀螺仪量程，可选 16/32/64/128/256/512/1024/2048 (dps)，默认 512 |
| `accel-odr` | int | 否 | 加速度计采样率，可选 28/56/112/224/448/896/1792/3584/7174 (Hz)，默认 896 |
| `gyro-odr` | int | 否 | 陀螺仪采样率，同上，默认 896 |
| `int-gpios` | phandle | 否 | 中断 GPIO 引脚，不填则使用轮询模式 |
| `int-pin` | int | 否 | 使用 INT1 (`1`) 或 INT2 (`2`)，默认 2 |

### keebdeck 最简配置（轮询，不接中断）

```dts
&i2c0 {
    status = "okay";

    qmi8658a@6a {
        compatible = "qst,qmi8658a";
        reg = <0x6a>;       /* SA0 悬空 = 0x6A（内部 200KΩ 上拉） */
    };
};
```

### keebdeck 带中断配置

```dts
&i2c0 {
    status = "okay";

    qmi8658a@6a {
        compatible = "qst,qmi8658a";
        reg = <0x6a>;
        accel-fs = <4>;
        gyro-fs = <512>;
        accel-odr = <224>;   /* 飞鼠 224 Hz 足够，省电 */
        gyro-odr = <224>;
        int-gpios = <&gpio0 XX GPIO_ACTIVE_HIGH>;  /* 替换 XX 为实际引脚 */
        int-pin = <2>;
    };
};
```

### Kconfig

```
CONFIG_SENSOR=y
CONFIG_QMI8658A=y
# 轮询模式（默认，不需要接 INT）:
CONFIG_QMI8658A_TRIGGER_NONE=y
# 或者中断模式（需接 INT 引脚）:
# CONFIG_QMI8658A_TRIGGER_OWN_THREAD=y
```

---

## QMI8658A + nRF52840 低功耗策略

### QMI8658A 没有 Chip EN 引脚，需要 MOSFET 切电源吗？

**不需要。** QMI8658A 通过寄存器就能进入极低功耗状态，且支持硬件 Wake-on-Motion（WoM）自动唤醒。

### QMI8658A 各功耗模式（VDD=VDDIO=1.8V）

| 模式 | CTRL7 配置 | 电流 | 说明 |
|------|-----------|------|------|
| **Power-Down** | CTRL1 sensorDisable=1, CTRL7=0x00 | **~20μA** | 最低功耗，寄存器值保留，数字接口可通信 |
| 待机（默认上电） | CTRL7=0x00 | ~50μA | 传感器关，时钟开 |
| **Wake-on-Motion** | aEN=1, aODR=3Hz | **~30μA** | 加速度计低功耗采样，运动时触发 INT |
| 仅加速度计（31.25Hz） | aEN=1 | ~55μA | 倾斜/手势检测 |
| 6 轴全速（29.375Hz） | aEN=1, gEN=1 | ~750μA | 飞鼠活跃状态 |
| 6 轴高速（896Hz） | aEN=1, gEN=1 | ~550μA | 高刷飞鼠 |

### 软件 Power-Down vs 硬件 MOSFET 切 VDD

| 因素 | 软件 Power-Down (CTRL7=0x00) | 硬件 MOSFET 切 VDD |
|------|---------------------------|-------------------|
| 静态电流 | ~20μA | **0μA**（完全断电） |
| Wake-on-Motion | **支持**（IMU 硬件检测，INT 唤醒 MCU） | **不支持**（IMU 断电无法检测运动） |
| 唤醒延迟 | 快：WoM 中断立即触发 | 慢：上电 150ms + 重新配置寄存器 |
| 寄存器状态 | **保留** | 丢失，必须全部重新初始化 |
| I2C 总线 | 正常 | 需注意：VDD 断电后 I2C 上拉可能通过 ESD 管反灌电 |
| 额外元件 | 无 | PMOS + 栅极电阻 |
| 复杂度 | 简单寄存器写入 | PCB 布局 + 总线隔离 |

**结论：对于键盘应用，软件 Power-Down (~20μA) + WoM (~30μA) 完全足够。不需要 MOSFET。**

> 20-30μA 对比 nRF52840 本身的休眠电流（System ON + RTC ~3-5μA）只多了一点，对电池寿命影响极小。一颗 110mAh 电池仅 IMU 待机就能撑 ~150 天。

### 推荐的四级功耗管理方案

```
┌─────────────────────────────────────────────────────────────┐
│ 状态 1：飞鼠活跃                                              │
│ ─────────────────                                           │
│ 加速度计 + 陀螺仪 全开 (CTRL7 = aEN|gEN = 0x03)               │
│ ODR: 112-224 Hz                                             │
│ IMU 电流: ~550-750μA                                         │
│ MCU: 运行 Madgwick 融合 + BLE HID 上报                        │
│                                                             │
│ 触发条件：检测到键盘按键 + 运动                                  │
│ 退出条件：N 秒无按键/无运动 → 进入状态 2                         │
└───────────────────────────┬─────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 状态 2：Wake-on-Motion 待机                                    │
│ ───────────────────────                                     │
│ 关闭陀螺仪 (CTRL7 gEN=0)                                     │
│ 加速度计低功耗 3Hz (CTRL7 aEN=1, CTRL2 aODR=3Hz)              │
│ 配置 WoM 阈值 + INT 中断                                      │
│ IMU 电流: ~30μA                                              │
│ MCU: 可进入 System ON idle                                    │
│                                                             │
│ 触发条件：飞鼠闲置 N 秒                                        │
│ 退出条件：WoM 中断（运动检测）→ 回到状态 1                       │
│          M 秒无运动 → 进入状态 3                                │
└───────────────────────────┬─────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 状态 3：ZMK Idle（键盘空闲）                                    │
│ ──────────────────────                                      │
│ IMU Power-Down (CTRL1 sensorDisable=1, CTRL7=0x00)          │
│ IMU 电流: ~20μA                                              │
│ ZMK: CONFIG_ZMK_IDLE_TIMEOUT (默认 30s)                      │
│ BLE: 保持连接，降低广播频率                                     │
│                                                             │
│ 触发条件：WoM 待机超时 M 秒                                    │
│ 退出条件：按键 → 回到状态 2 或 1                                │
│          ZMK sleep timeout → 进入状态 4                       │
└───────────────────────────┬─────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 状态 4：ZMK Deep Sleep                                        │
│ ──────────────────                                          │
│ IMU Power-Down (CTRL7=0x00, ~20μA)                          │
│ ZMK: CONFIG_ZMK_IDLE_SLEEP_TIMEOUT (默认 900s = 15 分钟)     │
│ nRF52840: System OFF (~1.5μA)                               │
│ BLE: 断开连接                                                │
│ 总系统电流: ~22μA                                             │
│                                                             │
│ 触发条件：ZMK 空闲超时                                         │
│ 退出条件：键盘矩阵 GPIO 中断唤醒（按任意键）                     │
└─────────────────────────────────────────────────────────────┘
```

### QMI8658A Wake-on-Motion 配置流程

```c
// 1. 关闭所有传感器
i2c_reg_write_byte(CTRL7, 0x00);  // aEN=0, gEN=0

// 2. 配置加速度计为低功耗 3Hz
i2c_reg_write_byte(CTRL2, (FS_4G << 4) | ODR_3HZ);

// 3. 设置 WoM 阈值（CAL1_L，1mg/LSB，例如 200mg）
i2c_reg_write_byte(CAL1_L, 200);  // 200mg 阈值

// 4. 配置 WoM 中断引脚（CAL1_H）
i2c_reg_write_byte(CAL1_H, INT2_PIN);  // 用 INT2

// 5. 执行 CTRL9 命令写入 WoM 设置
i2c_reg_write_byte(CTRL9, CTRL_CMD_WRITE_WOM_SETTING);
// 等待 CTRL9 命令完成...

// 6. 启用加速度计进入 WoM 模式
i2c_reg_write_byte(CTRL7, 0x01);  // aEN=1

// 现在 IMU 在 ~30μA 下运行，运动超过 200mg 时 INT2 触发
```

> **注意**：当前 Zephyr QMI8658A 驱动未实现 WoM 功能，需要自行扩展。但寄存器操作很简单，核心就是 CTRL9 命令协议 + CTRL7 控制。

### 参考项目

| 项目 | 平台 | 说明 |
|------|------|------|
| [idevloop/Air_Mouse-IMU_Gesture_HID_Controller](https://github.com/idevloop/Air_Mouse-IMU_Gesture_HID_Controller_XIAO_nRF52840) | XIAO nRF52840 + LSM6DS3TR-C | Arduino BLE 飞鼠，非 ZMK |
| [aroum/ufa](https://github.com/aroum/ufa) | nRF52840 + PAW3395/PMW3610 | ZMK 游戏鼠标固件，光学传感器 |
| [inorichi/zmk-pmw3610-driver](https://github.com/inorichi/zmk-pmw3610-driver) | ZMK + PMW3610 | 含 SPI 休眠模式的 ZMK pointing 驱动 |

**目前没有 ZMK + IMU 飞鼠的现成项目。** keebdeck 如果做出来会是第一个。

## BLE 电池电量上报 (Battery Service)

### 原理：BLE Battery Service (BAS)

BLE 标准定义了 **Battery Service (BAS)**，是 Bluetooth SIG 官方 GATT 服务，专门用于上报设备电量：

| 项目 | 值 | 说明 |
|------|-----|------|
| Service UUID | `0x180F` | Battery Service |
| Characteristic UUID | `0x2A19` | Battery Level |
| 数据格式 | `uint8` (0-100) | 百分比 |
| 支持操作 | **Read** + **Notify** | 主机可主动读取，也可订阅通知 |

工作流程：

```
键盘固件 ADC 读电压 → 转换为百分比 → bt_bas_set_battery_level(pct)
                                           │
                                           ▼
                              BLE GATT 通知 (0x180F / 0x2A19)
                                           │
                                           ▼
                              主机 OS 显示电池图标和百分比
```

**不需要额外的 UUID 或自定义描述符**，BAS 是标准协议，所有主流 OS 原生支持。

### 各操作系统支持情况

| 操作系统 | 显示位置 | 备注 |
|---------|---------|------|
| **macOS** | 系统设置 > 蓝牙、菜单栏蓝牙图标 | ⚠️ BAS 通知会唤醒 Mac（见下方已知问题） |
| **iOS / iPadOS** | 设置 > 蓝牙、电池小组件 | 自动识别 |
| **Windows 10/11** | 设置 > 蓝牙和其他设备 | 1809+ 版本支持，1903+ 更稳定 |
| **Linux** | BlueZ → UPower → GNOME/KDE 电池面板 | `upower -d` 或 `bluetoothctl info` 可查看 |
| **Android 8.1+** | 设置 > 已连接的设备、通知栏 | 自动读取 BAS |

### ZMK 已内置完整支持

ZMK 主线已经集成了 BLE 电池上报，基于 Zephyr 的 `bt_bas` 实现。

#### 关键 Kconfig 选项

| 选项 | 默认值 | 说明 |
|------|--------|------|
| `CONFIG_ZMK_BATTERY_REPORTING` | BLE 启用时自动开启 | 电池检测和上报主开关 |
| `CONFIG_ZMK_BATTERY_REPORT_INTERVAL` | 60 (秒) | 上报间隔 |
| `CONFIG_BT_BAS` | 自动开启 | Zephyr BLE Battery Service |
| `CONFIG_ZMK_BATTERY_REPORTING_FETCH_MODE` | `STATE_OF_CHARGE` | 可选 `LITHIUM_VOLTAGE`（线性电压映射） |

#### 电池驱动（二选一）

| 驱动 | compatible | 适用场景 | 额外硬件 |
|------|-----------|---------|---------|
| **nRF VDDH** | `zmk,battery-nrf-vddh` | nRF52840 直接读 VDDH | **无需额外硬件** |
| 分压器 ADC | `zmk,battery-voltage-divider` | 通用方案 | 需要电阻分压器 + ADC 引脚 |

#### DTS 配置（nRF52840 VDDH 方案，推荐）

```dts
/ {
    chosen {
        zmk,battery = &vbatt;
    };
};

&adc {
    vbatt: vbatt {
        compatible = "zmk,battery-nrf-vddh";
    };
};
```

> **E73-2G4M08S1C 模组直接可用**：nRF52840 的 VDDH 引脚直连电池正极（经 LiPo 充电电路），`zmk,battery-nrf-vddh` 驱动通过片内 SAADC 读取 VDDH 电压，无需外部分压电阻，零额外 BOM。

#### 硬件接线：为什么不需要外部分压电阻？

**nRF52840 片内自带 VDDH/5 分压器**，SAADC 可以直接选择 `VDDHDIV5` 作为 ADC 输入通道，无需任何外部元件。

```
                          nRF52840 片内
                    ┌──────────────────────────┐
                    │                          │
LiPo B+ ──────────→│ VDDH (Pin 23 on E73)     │
(3.0-4.2V)          │   │                      │
                    │   ├──→ REG0 DC/DC → VDD  │
                    │   │                      │
                    │   └──→ 内部 1/5 分压 ─────│──→ SAADC "VDDHDIV5" 通道
                    │        (片内电阻)        │     (读出值 × 5 = 电池电压)
                    │                          │
LiPo B- ──────────→│ GND (Pin 5/21/24 on E73) │
                    └──────────────────────────┘
```

**ADC 测量原理：**

| 参数 | 值 | 说明 |
|------|-----|------|
| ADC 输入 | `VDDHDIV5` | VDDH 经片内 1/5 分压 |
| 参考电压 | 0.6V (内部) | nRF52840 SAADC 内部基准 |
| 增益 | 1/2 | 有效量程 = 0.6V / 0.5 = 1.2V |
| 最大可测 VDDH | 1.2V × 5 = **6.0V** | LiPo 4.2V 完全在量程内 |
| 分辨率 | 12-bit | 4096 级，~1.5mV 分辨率 |
| 过采样 | 4× | 降低噪声 |
| 采集时间 | 40μs | 单次采样耗时极短 |

**举例**：电池 4.2V 时，ADC 输入 = 4.2V / 5 = 0.84V，远在 1.2V 量程内，精度充裕。

#### E73-2G4M08S1C 模组接线

```
E73 模组                            外部元件
───────                            ────────
Pin 23 (VDH/VDDH) ←───────────── LiPo B+ (3.0-4.2V)
Pin 25 (DCH/DCCH)  ──── 100nF ── GND    (REG0 DC/DC 输出去耦)
Pin 19 (VCC/VDD)   ──── 100nF ── GND    (VDD 去耦)
                    ──── 4.7μF ── GND    (VDD 储能)
Pin 5/21/24 (GND)  ──────────── LiPo B-
```

**电池电量检测不需要额外引脚和元件**：
- 不需要 ADC 引脚（使用片内 VDDHDIV5 通道）
- 不需要分压电阻
- 不需要 GPIO 控制电源开关
- 只要 LiPo 接到 VDDH + GND，固件就能自动读取电压

#### nice!nano 两代方案对比

| 版本 | 驱动 | 外部元件 | 占用引脚 |
|------|------|---------|---------|
| **nice!nano v2** | `zmk,battery-nrf-vddh` | **无** | **无** |
| nice!nano v1 | `zmk,battery-voltage-divider` | 806KΩ + 2MΩ 分压电阻 | P0.04 (AIN2) |

v1 的 DTS 配置（仅供参考，不推荐新设计使用）：

```dts
/* nice!nano v1 — 外部分压器方案，需要额外电阻和 ADC 引脚 */
vbatt: vbatt {
    compatible = "zmk,battery-voltage-divider";
    io-channels = <&adc 2>;           /* AIN2 = P0.04 */
    output-ohms = <2000000>;           /* 2MΩ 下臂 */
    full-ohms = <(2000000 + 806000)>;  /* 2MΩ + 806KΩ = 2.806MΩ 总阻 */
};
```

> **keebdeck 推荐使用 v2 方案**（`zmk,battery-nrf-vddh`），零外部元件，零引脚占用。
> **但前提是电源路径设计正确**，见下方分析。

#### PMOS 电源切换对 VDDHDIV5 电量测量的影响

**核心问题不是 PMOS 压降，而是 USB 接入时 VDDH 引脚看到的是什么电压。**

##### 场景分析

```
场景 A：纯电池供电（USB 未接）

    LiPo B+ (4.0V) ──→ PMOS ──→ VDDH
                        Vds≈30mV
    VDDH ≈ 3.97V
    VDDHDIV5 读数 = 3.97V / 5 = 0.794V → 软件 ×5 → 3.97V
    误差：30mV（< 1%），完全可接受 ✅

场景 B：USB 接入，简单 PMOS 切换（问题所在！）

    VBUS (5V) ──→ PMOS ──→ VDDH    ← VDDH 现在是 5V！
    LiPo B+ (3.8V) ──→ PMOS 截止    ← 电池被断开
    VDDHDIV5 读数 = 5.0V / 5 = 1.0V → 软件 ×5 → 5000mV
    固件算出电量 = 100%，但这是 USB 电压，不是电池电压！❌
```

**结论：如果 PMOS 在 USB 接入时把 VDDH 切到 VBUS，VDDHDIV5 就完全无法测量电池电量。**

##### 为什么 nice!nano v1 用外部分压器？

nice!nano v1 不是没注意到片内 VDDHDIV5，而是**它的电源路径设计决定了不能用 VDDHDIV5**：

| | nice!nano v1 | nice!nano v2 |
|---|---|---|
| **充电 IC** | LN2054Y42AMR（简单线性充电器） | **BQ24072**（TI，带 DPPM 电源路径管理） |
| **电源切换** | PMOS 简单开关 | BQ24072 内置 DPPM |
| **USB 接入时 VDDH** | 可能看到 VBUS (~5V) | **OUT 引脚始终跟踪电池电压** |
| **电池测量方案** | 外部分压器接在 B+ 上 → P0.04 | VDDHDIV5（片内） |
| **ext-power 极性** | P0.13 `GPIO_ACTIVE_LOW` | P0.13 `GPIO_ACTIVE_HIGH` |

v1 的外部分压器**直接连在电池 B+ 端子上**，绕过了 PMOS 电源开关，所以无论 USB 是否接入，P0.04 始终读到的是真实电池电压。

##### BQ24072 DPPM 为什么能让 VDDHDIV5 工作？

BQ24072 有 **Dynamic Power Path Management (DPPM)**，关键特性：

```
                    BQ24072
              ┌─────────────────┐
VBUS (5V) ──→│ IN          OUT │──→ VDDH (nRF52840)
              │                 │
              │    DPPM 控制    │
              │                 │
LiPo B+ ←──→│ BAT             │
              └─────────────────┘
```

| USB 状态 | BQ24072 OUT 输出 | VDDH 看到 | VDDHDIV5 测量 |
|---------|-----------------|----------|--------------|
| **未接** | BAT 直通 → Vbat | 3.0-4.2V | 准确 ✅ |
| **接入，充电中** | Vbat + ~0.2V | 3.2-4.4V | 偏高 ~200mV，可接受 ✅ |
| **接入，充满** | ≈ Vbat | ~4.2V | 准确 ✅ |

**BQ24072 的 OUT 引脚始终跟踪电池电压**（不像 BQ24075 会输出 VBUS 电压），所以 VDDH 始终反映电池状态，VDDHDIV5 可以正确工作。

##### 三种电源路径方案对比

| 方案 | VDDH 来源 | USB 时 VDDH | VDDHDIV5 可用？ | 电池测量方法 |
|------|----------|------------|---------------|------------|
| **DPPM 充电 IC (BQ24072)** | IC OUT 引脚 | ≈ Vbat + 0.2V | **可以** ✅ | `zmk,battery-nrf-vddh` |
| **简单 PMOS 开关** | PMOS 输出 | VBUS (~5V) | **不行** ❌ | 外部分压器接 B+ |
| **二极管 OR** | 二极管输出 | VBUS - 0.3V (~4.7V) | **不行** ❌ | 外部分压器接 B+ |

##### keebdeck 设计建议

**如果用简单 PMOS 电源切换（无 DPPM 充电 IC）：**

```
LiPo B+ ──┬──→ PMOS ──→ VDDH (供电)
           │
           └──→ 806KΩ ──┬──→ P0.xx (AIN) ──→ ADC 读取
                         │
                    2MΩ ──┤
                         │
                        GND

分压比 = 2M / (2M + 806K) = 0.713
4.2V 电池 → ADC 输入 = 2.99V
3.0V 电池 → ADC 输入 = 2.14V
```

DTS 配置：

```dts
vbatt: vbatt {
    compatible = "zmk,battery-voltage-divider";
    io-channels = <&adc X>;            /* 替换 X 为实际 AIN 通道号 */
    output-ohms = <2000000>;            /* 2MΩ 下臂 */
    full-ohms = <(2000000 + 806000)>;   /* 总阻 2.806MΩ */
};
```

> 分压电阻选择高阻值（MΩ 级）是为了最小化漏电流：4.2V / 2.806MΩ ≈ **1.5μA**，对电池寿命影响可忽略。

**如果用 BQ24072 类 DPPM 充电 IC：**

```dts
/* 不需要外部分压器，直接用 VDDHDIV5 */
vbatt: vbatt {
    compatible = "zmk,battery-nrf-vddh";
};

&reg0 {
    status = "okay";
};
```

**选择建议：**

| 场景 | 推荐方案 |
|------|---------|
| 用 BQ24072 / 类似 DPPM 充电 IC | `zmk,battery-nrf-vddh`（零外部元件） |
| 用简单 PMOS + 线性充电 IC | `zmk,battery-voltage-divider`（需 2 个电阻 + 1 个 AIN 引脚） |
| 不确定电源路径 | 保守选外部分压器，总是能正确测量 |

#### Kconfig 配置

```
# 电池上报（BLE 启用时自动开启，通常不需要手动配置）
CONFIG_ZMK_BATTERY_REPORTING=y
CONFIG_ZMK_BATTERY_REPORT_INTERVAL=60

# 如果想禁用 BLE 电量上报（但保留本地电池监测）：
# CONFIG_BT_BAS=n
```

#### 电压 → 百分比转换

ZMK 内置的锂电池电压映射（`LITHIUM_VOLTAGE` 模式）：

```c
// zmk/app/src/battery.c
static uint8_t lithium_ion_mv_to_pct(int16_t bat_mv) {
    if (bat_mv >= 4200) return 100;
    else if (bat_mv <= 3450) return 0;
    else return bat_mv * 2 / 15 - 459;  // 线性近似
}
```

| 电压 | 百分比 | 说明 |
|------|--------|------|
| ≥ 4.20V | 100% | 满电 |
| 3.85V | ~54% | |
| 3.70V | ~34% | |
| ≤ 3.45V | 0% | 需要充电 |

> 这是线性近似，实际 LiPo 放电曲线是非线性的。对于键盘应用精度足够。

### 分体键盘电量上报

ZMK 支持分体键盘两半的电量分别上报：

| 选项 | 说明 |
|------|------|
| `CONFIG_ZMK_SPLIT_BLE_CENTRAL_BATTERY_LEVEL_FETCHING=y` | 主半从副半获取电量 |
| `CONFIG_ZMK_SPLIT_BLE_CENTRAL_BATTERY_LEVEL_PROXY=y` | 主半代理副半电量给主机 |

> 注意：大多数 OS 只显示一个电池电量。要显示两半电量需要自定义工具。

### 已知问题

#### macOS 睡眠唤醒问题（最严重）

macOS 会把 BLE BAS 通知当作「设备活动」，导致 Mac 从睡眠中被唤醒。这是 macOS 的 BLE 实现问题，不是固件 bug。

**解决方案：**

| 方案 | 配置 | 代价 |
|------|------|------|
| 禁用 BAS | `CONFIG_BT_BAS=n` | macOS 上不显示电池百分比 |
| 保持默认 | 不改 | Mac 可能被键盘电量通知唤醒 |

ZMK 文档明确提到了这个问题，建议受影响的 macOS 用户使用 `CONFIG_BT_BAS=n`。

#### 百分比跳变

锂电池电压在 3.5-3.9V 区间变化很平缓，线性映射会导致：
- 100% → 80% 掉得快（4.2V→3.9V 电压下降快）
- 80% → 20% 很慢（平台期）
- 20% → 0% 突然掉没

这是所有 BLE 键盘的通病，不影响实际使用。

### 实现要点总结

对于 keebdeck 项目：

```
✅ 硬件：不需要额外硬件，nRF52840 VDDH 直接读电池电压
✅ 固件：ZMK 已内置，CONFIG_ZMK_BLE 启用时自动工作
✅ 协议：标准 BLE BAS (0x180F)，所有主流 OS 原生支持
✅ 驱动：zmk,battery-nrf-vddh，零 BOM 成本
⚠️ macOS：可能会唤醒睡眠，必要时 CONFIG_BT_BAS=n
```
