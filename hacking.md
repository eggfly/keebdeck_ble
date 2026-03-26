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

### BLE 键盘各工作模式估算

假设条件：EXT_POWER 关闭（无 RGB LED/OLED），使用外部 32K 晶振（LFXO），DC-DC 模式。

| 工作模式 | 平均电流 | 计算依据 |
|----------|----------|----------|
| **深睡眠**（无 BLE 连接） | ~3-5 μA | MCU System ON + RAM + RTC + 外围漏电 |
| **空闲已连接**（BLE 保持，无按键） | ~100-200 μA | 连接间隔 75ms，每次射频 ~1.5ms，6.3mA × 1.5/75 ≈ 126 μA + 基础 3μA |
| **打字中**（BLE 低延迟） | ~2-3 mA | 连接间隔 7.5-15ms，矩阵扫描 + CPU 处理 + 射频 |
| **RGB LED 开启** | +20-100 mA | 取决于 LED 数量和亮度（WS2812 每颗静态漏电 ~1mA） |
| **OLED 显示** | +10-20 mA | SSD1306 128x32 典型 |

> ZMK 固件在无按键操作一段时间后，会自动从「打字中」→「空闲已连接」→「深睡眠」逐级降低功耗。

### 每日功耗模型

典型使用场景：每天打字 3 小时，待机连接 5 小时，深睡眠 16 小时（EXT_POWER 关闭）。

```
每日消耗 = 3h × 2.5mA + 5h × 0.15mA + 16h × 0.005mA
         = 7.50 + 0.75 + 0.08
         = 8.33 mAh/天
```

### 常见电池续航估算

| 电池型号 | 容量 | 常见用途 | 估算续航 |
|----------|------|----------|----------|
| 301220 | 60 mAh | 极小分体键盘 | ~7 天 |
| 301230 | 110 mAh | 小型分体（Corne 单手） | ~13 天 |
| 401230 | 130 mAh | nice!nano 标配 | ~16 天 |
| 502030 | 250 mAh | 中型分体键盘 | ~30 天 |
| 503035 | 500 mAh | 一体式 60% 键盘 | ~60 天 |
| 603450 | 1000 mAh | 大型一体式键盘 | ~120 天 |
| 704060 | 2000 mAh | 带触摸屏/大型设备 | ~240 天 |

> 以上估算假设 EXT_POWER 关闭（无 RGB/OLED），实际续航受使用强度、BLE 连接参数、外设功耗影响很大。如果 RGB LED 常亮（~50mA），110mAh 电池只能撑 ~2 小时。

### 影响续航的关键因素

| 因素 | 影响 | 建议 |
|------|------|------|
| **RGB LED** | 开启时功耗占 90%+ | 不用时关闭 EXT_POWER |
| **OLED 显示屏** | +10-20 mA | 设置自动熄屏超时 |
| **BLE 连接间隔** | 7.5ms (低延迟) vs 75ms (省电) | ZMK 自动切换 |
| **外部 32K 晶振** | LFXO vs LFRC：影响睡眠时校准功耗 | 必须贴外部晶振 |
| **DC-DC vs LDO** | DC-DC 效率 >80%，LDO ~50% | E73 参考设计已用 DC-DC |
| **上拉电阻漏电** | SuperMini 旧批次 R4=5.6K 漏 643μA | 确认 R4 ≥ 10M |
| **EXT_POWER LDO 关断电流** | XC6220 <1μA，ME6217 ~0.1μA | 选低 Iq 的 LDO |

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
