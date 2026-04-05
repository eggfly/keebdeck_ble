# KeebDeck BLE

nRF52840 BLE wireless keyboard project based on ZMK firmware. This repo contains hardware design resources, firmware dumps, JLink/SWD tooling, and development documentation for building a custom BLE keyboard.

## Hardware

- **MCU**: nRF52840 (ARM Cortex-M4F, 64MHz, 1MB Flash, 256KB RAM, BLE 5.0)
- **Dev Board**: ProMicro NRF52840 compatible (SuperMini / nice!nano compatible)
- **Keyboard Matrix**: KeebDeck 6R13C (6 rows x 13 columns = 78 keys, ROW2COL)
- **Bootloader**: Adafruit UF2 (nice!nano variant)
- **Firmware**: ZMK

<img src="docs/images/ProMicro_NRF52840.png" width="400" alt="ProMicro NRF52840">

<img src="docs/images/nrf_pins.png" width="500" alt="nRF52840 Pin Map">

## nRF52840 Flash Layout

```
Address       Content                     Size
──────────────────────────────────────────────────
0x000000      MBR (Master Boot Record)    4KB
0x001000      SoftDevice S140 v6.1.1      ~148KB      BLE protocol stack
0x026000      Application (ZMK)           ~824KB      zmk.uf2 writes here
0x0F4000      UF2 Bootloader              40KB        BPROT protected
0x0FE000      Bootloader Settings         8KB
0x100000      End of Flash                Total 1MB
```

### Actual Flash Usage (from JLink dump)

```
0x000000 - 0x026000  ( 152KB)  MBR + SoftDevice        [##########]
0x026000 - 0x0F4000  ( 824KB)  App region (EMPTY)       [..........]
0x0F4000 - 0x0FE000  (  40KB)  Bootloader              [##########]
0x0FE000 - 0x100000  (   8KB)  Settings (EMPTY)        [..........]

Used: 192KB / 1024KB (18%)
```

> The dev board currently only has MBR + SoftDevice + Bootloader flashed. No application firmware (ZMK) is present in this dump.

## Chip Info (from JLink)

| Field | Value | Description |
|-------|-------|-------------|
| Part Number | `0x00052840` | nRF52840 |
| Package | `0x41414430` (AAD0) | QFN48 |
| RAM | 256KB | |
| APPROTECT | `0xFFFFFFFF` | Not locked (SWD open) |
| NFC Pins | `0xFFFFFFFE` | Disabled (used as GPIO) |
| Reset Pin | P0.18 | Hardware reset configured |
| Bootloader Addr | `0x000F4000` | Adafruit UF2 bootloader |
| BLE MAC | `570FB754 B2231661` | Unique per chip |

## Project Structure

```
keebdeck_ble/
├── README.md                   # This file
├── docs/
│   ├── hacking.md              # JLink/SWD guide, firmware operations
│   └── images/                 # Hardware photos and diagrams
├── firmware/
│   ├── bootloader/             # Bootloader hex files for flashing
│   │   ├── nice_nano_bootloader-0.6.0_s140_6.1.1.hex
│   │   └── pca10056_bootloader-0.5.0-dirty_s140_6.1.1.hex
│   └── dump/                   # Flash dumps from working board
│       ├── dump_full_flash.bin  # Full 1MB flash (JLink savebin)
│       └── CURRENT.UF2         # UF2 export from bootloader USB mode
├── jlink-scripts/              # JLink automation scripts
│   ├── common.sh               # Shared variables
│   ├── 01-chip-info.sh         # Read chip registers
│   ├── 02-dump-full-flash.sh   # Export full 1MB flash
│   ├── 03-dump-bootloader.sh   # Export bootloader region
│   ├── 04-dump-uicr.sh         # Export UICR config
│   ├── 05-flash-hex.sh         # Flash firmware (full erase)
│   ├── 06-erase-all.sh         # Full chip erase
│   ├── 07-reset.sh             # Reset chip
│   ├── 08-read-memory.sh       # Read arbitrary memory address
│   ├── 09-flash-bootloader-only.sh  # Flash bootloader without full erase
│   ├── 10-gdb-server.sh        # Start GDB debug server
│   └── 11-rtt-viewer.sh        # Real-time logging (RTT)
└── LICENSE                     # MIT License
```

## Keyboard Matrix

6 rows x 13 columns, 78 key positions with ROW2COL diode direction.

<img src="docs/images/keebdeck_matrix_debug_board.png" width="500" alt="Matrix Debug Board">

### Pin Assignment

> nice!nano Pro Micro 引脚 D11/D12/D13/D17 不存在（未引出），实际可用 18 个 GPIO。
> 来源：ZMK `arduino_pro_micro_pins.dtsi`

#### 完整 Pro Micro → nRF52840 GPIO 映射

| Pro Micro | nRF52840 GPIO | Port.Pin | 备注 |
|-----------|---------------|----------|------|
| D0 | P0.08 | gpio0 8 | RX |
| D1 | P0.06 | gpio0 6 | TX |
| D2 | P0.17 | gpio0 17 | SDA (I2C) |
| D3 | P0.20 | gpio0 20 | SCL (I2C) |
| D4 | P0.22 | gpio0 22 | A6 |
| D5 | P0.24 | gpio0 24 | |
| D6 | P1.00 | gpio1 0 | A7 |
| D7 | P0.11 | gpio0 11 | |
| D8 | P1.04 | gpio1 4 | A8 |
| D9 | P1.06 | gpio1 6 | A9 |
| D10 | P0.09 | gpio0 9 | A10 |
| ~~D11~~ | — | — | **不存在** |
| ~~D12~~ | — | — | **不存在** |
| ~~D13~~ | — | — | **不存在** |
| D14 | P1.11 | gpio1 11 | |
| D15 | P1.13 | gpio1 13 | |
| D16 | P0.10 | gpio0 10 | |
| ~~D17~~ | — | — | **不存在** |
| D18 | P1.15 | gpio1 15 | A0 |
| D19 | P0.02 | gpio0 2 | A1 |
| D20 | P0.29 | gpio0 29 | A2 |
| D21 | P0.31 | gpio0 31 | A3 |

#### 键盘矩阵分配

| 功能 | Pro Micro 引脚 | nRF52840 GPIO | 数量 |
|------|--------------|---------------|------|
| ROW0 | D0 | P0.08 | |
| ROW1 | D1 | P0.06 | |
| ROW2 | D2 | P0.17 | |
| ROW3 | D3 | P0.20 | |
| ROW4 | D4 | P0.22 | |
| ROW5 | D5 | P0.24 | |
| | | | **6 rows** |
| COL0 | D6 | P1.00 | |
| COL1 | D7 | P0.11 | |
| COL2 | D8 | P1.04 | |
| COL3 | D9 | P1.06 | |
| COL4 | D10 | P0.09 | |
| COL5 | D16 | P0.10 | ← 跳过 D11-D13 |
| COL6 | D14 | P1.11 | |
| COL7 | D15 | P1.13 | |
| COL8 | D18 | P1.15 | ← 跳过 D17 |
| COL9 | D19 | P0.02 | |
| COL10 | D20 | P0.29 | |
| COL11 | D21 | P0.31 | |
| | | | **12 cols (D6-D21, 跳过 D11-D13/D17)** |
| COL12 | Fly wire | **P1.02** | 不在 Pro Micro 排针上 |
| | | | **总计 6R × 13C = 78 keys** |

#### 引脚使用汇总

| 用途 | 引脚数 | 具体引脚 |
|------|--------|---------|
| 键盘矩阵 (6R+13C) | 19 | D0-D10, D14-D16, D18-D21, P1.02 |
| I2C (IMU 等) | 2 | P0.26 (SDA), P1.09 (SCL) — 不在 Pro Micro 排针上，PCB 直连 |
| IMU INT (可选) | 1 | P0.03 — DRDY 中断 |
| **总计已用** | **19+2~3** | 18 个 Pro Micro + 1 个飞线 + 2~3 个 E73 直连 |
| **剩余可用** | **0** | Pro Micro 引脚全部用完，I2C 用 E73 模组非排针引脚 |

> **I2C 引脚选择**：I2C 使用 P0.26 (SDA) + P1.09 (SCL)，均为 E73 模组上的非 Pro Micro 排针引脚，与键盘矩阵无冲突。外部 5.1KΩ 0402 上拉到 VDD。详见 `imu-sensor-selection.md`。

## Getting Started

### Prerequisites

- J-Link (or J-Link OB clone) for SWD access
- USB-C data cable
- macOS with Homebrew

### Install Tools

```bash
brew install --cask segger-jlink
```

### Quick Start

```bash
cd jlink-scripts

# Read chip info
./01-chip-info.sh

# Dump current firmware
./02-dump-full-flash.sh

# Flash new firmware
./05-flash-hex.sh path/to/firmware.hex
```

See [docs/hacking.md](docs/hacking.md) for the complete JLink/SWD guide including:
- Blank chip recovery
- Bootloader flashing from scratch
- Firmware extraction and comparison
- nRF52840 memory map reference

## Related Repos

- [zmk](https://github.com/zmkfirmware/zmk) - ZMK Firmware
- [Adafruit_nRF52_Bootloader](https://github.com/adafruit/Adafruit_nRF52_Bootloader) - UF2 Bootloader (recommended, v0.10.0 includes nice_nano)
- [Nice-Keyboards/Adafruit_nRF52_Bootloader](https://github.com/Nice-Keyboards/Adafruit_nRF52_Bootloader) - nice!nano fork (outdated, v0.5.1.1)

## License

MIT License - see [LICENSE](LICENSE)
