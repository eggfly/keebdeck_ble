# KeebDeck BLE 网表 + PCB 综合检查 (2026-04-07)

基于 **最新** `Netlist_Schematic1_2026-04-07.tel`（含 DEC2/DEC3/A22 修复后版本）和 `IPC_PCB1_KeebDeck_BLE_20260405_2026-04-07.356a`，
对照 nRF52840 Product Specification v1.7 Table 145 (aQFN73 ball assignments) 逐引脚检查。

> 旧版网表已备份为 `Netlist_Schematic1_2026-04-07-old.tel`。

## 键盘矩阵说明

- BLE PCB 版本: **6R × 12C = 72 键** (ROW0-ROW5, COL0-COL11)
- 2.54mm 测试板版本: 6R × 13C = 78 键 (含 COL12，fly wire 到 P1.02)
- 原理图组件名 `KeebDeck_Keyboard_6R13C_SwapTabAndE` 沿用旧名，实际为 12 列

## 表 1：nRF52840 (U8) aQFN73 全部引脚

| Ball | GPIO/Name | 类型 | 网表网络 | 设计用途 | 状态 |
|------|-----------|------|---------|---------|------|
| A8 | P0.31 | Digital I/O | COL11 → U2.C11 | 键盘列11 | ✅ |
| A10 | P0.29 | Digital I/O | COL10 → U2.C10 | 键盘列10 | ✅ |
| A12 | P0.02 | Digital I/O | COL9 → U2.C9 | 键盘列9 | ✅ |
| A14 | P1.15 | Digital I/O | COL8 → U2.C8 | 键盘列8 | ✅ |
| A16 | P1.13 | Digital I/O | COL7 → U2.C7 | 键盘列7 | ✅ |
| A18 | DEC2 | Power | $1N286 → C24(NC) → GND | 1.3V 去耦 | ⚠️ C24 标 NC，见问题 #1 |
| A20 | P1.10 | Digital I/O | N/C | 空闲 GPIO | ✅ |
| A22 | VDD | Power | VDD_NRF_1V8 | 电源 1.8V | ✅ 已修复 |
| A23 | XC2 | Analog | XC2_32M → C17+X3.3 | 32MHz 晶振 | ✅ |
| B1 | VDD | Power | VDD_NRF_1V8 | 电源 1.8V | ✅ |
| B3 | DCC | Power | $1N155 → U7.2 | DC/DC REG1 输出 | ✅ |
| B5 | DEC4 | Power | DEC4_6_1V3 → C2+C9+L5 | 1.3V 去耦 | ✅ |
| B7 | VSS | Power | GND | 地 | ✅ |
| B9 | P0.30 | Digital I/O | N/C | 空闲 GPIO | ✅ |
| B11 | P0.28 | Digital I/O | N/C | 空闲 GPIO | ✅ |
| B13 | P0.03 | Digital I/O | IMU_INT2 → U15.9 | IMU 中断 2 | ✅ |
| B15 | P1.14 | Digital I/O | N/C | 空闲 GPIO | ✅ |
| B17 | P1.12 | Digital I/O | N/C | 空闲 GPIO | ✅ |
| B19 | P1.11 | Digital I/O | COL6 → U2.C6 | 键盘列6 | ✅ |
| B24 | XC1 | Analog | XC1_32M → C18+X3.1 | 32MHz 晶振 | ✅ |
| C1 | DEC1 | Power | DEC1 → C5 → GND | 1.1V 去耦 | ✅ |
| D2 | P0.00/XL1 | Analog | $1N132 → C6+X1.1 | 32.768kHz 晶振 | ✅ |
| D23 | DEC3 | Power | DEC3 → C23(100pF) → GND | 电源去耦 | ⚠️ C23=100pF 偏小，见问题 #2 |
| E24 | DEC6 | Power | DEC4_6_1V3 (与 B5 同网) | 1.3V 去耦 | ✅ |
| F2 | P0.01/XL2 | Analog | $1N133 → C7+X1.2 | 32.768kHz 晶振 | ✅ |
| F23 | VSS_PA | Power | GND | 射频地 | ✅ |
| G1 | P0.26 | Digital I/O | IMU_SDA → R8+U15.14 | I2C 数据 (IMU) | ✅ |
| H2 | P0.27 | Digital I/O | N/C | 空闲 GPIO | ✅ |
| H23 | ANT | RF | $1N145 → C11+L1 | 天线匹配网络 | ✅ |
| J1 | P0.04 | Digital I/O | MCU_SDA → CN5.3+R18 | I2C 数据 (外部) | ✅ |
| J24 | P0.10 | Digital I/O | COL5 → U2.C5 | 键盘列5 | ✅ |
| K2 | P0.05 | Digital I/O | MCU_SCL → CN5.4+R17 | I2C 时钟 (外部) | ✅ |
| L1 | P0.06 | Digital I/O | ROW1 → U2.R1 | 键盘行1 | ✅ |
| L24 | P0.09/NFC1 | Digital I/O | COL4 → U2.C4 | 键盘列4 (NFC 禁用) | ✅ |
| M2 | P0.07 | Digital I/O | N/C | 空闲 GPIO | ✅ |
| N1 | P0.08 | Digital I/O | ROW0 → U2.R0 | 键盘行0 | ✅ |
| N24 | DEC5 | Power | DEC5 → C13(820pF) | 1.3V 去耦 (Dxx) | ⚠️ 见问题 #3 |
| P2 | P1.08 | Digital I/O | N/C | 空闲 GPIO | ✅ |
| P23 | P1.07 | Digital I/O | N/C | 空闲 GPIO | ✅ |
| R1 | P1.09 | Digital I/O | IMU_SCL → R9+U15.13 | I2C 时钟 (IMU) | ✅ |
| R24 | P1.06 | Digital I/O | COL3 → U2.C3 | 键盘列3 | ✅ |
| T2 | P0.11 | Digital I/O | COL1 → U2.C1 | 键盘列1 | ✅ |
| T23 | P1.05 | Digital I/O | N/C | 空闲 GPIO | ✅ |
| U1 | P0.12 | Digital I/O | N/C | 空闲 GPIO | ✅ |
| U24 | P1.04 | Digital I/O | COL2 → U2.C2 | 键盘列2 | ✅ |
| V23 | P1.03 | Digital I/O | N/C | 空闲 GPIO | ✅ |
| W1 | VDD | Power | VDD_NRF_1V8 | 电源 1.8V | ✅ |
| W24 | P1.02 | Digital I/O | N/C | 空闲 GPIO (测试板版 COL12) | ✅ |
| Y2 | VDDH | Power | VDD_HV → C20+R1 | 高压电源输入 | ✅ |
| Y23 | P1.01 | Digital I/O | N/C | 空闲 GPIO | ✅ |
| AA24 | SWDCLK | Debug | SWCLK → H1.1 | SWD 调试时钟 | ✅ |
| AB2 | DCCH | Power | DCCH → U14.2 | DC/DC REG0 高压输出 | ✅ |
| AC5 | DECUSB | Power | DECUSB → C8 → GND | USB 3.3V 去耦 | ✅ |
| AC9 | P0.14 | Digital I/O | LED_RED → R20(1.5kΩ) → LED3.3 | RGB 红色 | ✅ |
| AC11 | P0.16 | Digital I/O | LED_GREEN → R22(470Ω) → LED3.1 | RGB 绿色 | ✅ |
| AC13 | P0.18/nRESET | Digital I/O | RESET → H1.5 | 复位 | ✅ |
| AC15 | P0.19 | Digital I/O | LED_BLUE → R21(470Ω) → LED3.2 | RGB 蓝色 | ✅ |
| AC17 | P0.21 | Digital I/O | N/C | 空闲 (QSPI) | ✅ |
| AC19 | P0.23 | Digital I/O | N/C | 空闲 (QSPI) | ✅ |
| AC21 | P0.25 | Digital I/O | N/C | 空闲 GPIO | ✅ |
| AC24 | SWDIO | Debug | SWDIO → H1.2 | SWD 调试数据 | ✅ |
| AD2 | VBUS | Power | VBUS → USB1+Q2+D11+... | USB 5V | ✅ |
| AD4 | D- | USB | D- → R15(22Ω) → USB_DN | USB 数据- | ✅ |
| AD6 | D+ | USB | D+ → R16(22Ω) → USB_DP | USB 数据+ | ✅ |
| AD8 | P0.13 | Digital I/O | POWER_PIN → TP4 | EXT_POWER 测试点 | ✅ |
| AD10 | P0.15 | Digital I/O | BL_PWM → R4+U1.4 | 背光 PWM | ✅ |
| AD12 | P0.17 | Digital I/O | ROW2 → U2.R2 | 键盘行2 | ✅ |
| AD14 | VDD | Power | VDD_NRF_1V8 | 电源 1.8V | ✅ |
| AD16 | P0.20 | Digital I/O | ROW3 → U2.R3 | 键盘行3 | ✅ |
| AD18 | P0.22 | Digital I/O | ROW4 → U2.R4 | 键盘行4 | ✅ |
| AD20 | P0.24 | Digital I/O | ROW5 → U2.R5 | 键盘行5 | ✅ |
| AD22 | P1.00 | Digital I/O | COL0 → U2.C0 | 键盘列0 | ✅ |
| AD23 | VDD | Power | VDD_NRF_1V8 | 电源 1.8V | ✅ |
| Die pad | VSS | Power | GND (U8.0) | 散热/地 | ✅ |

**统计**: 73 球 — 55 ✅ 无误, 14 个空闲 GPIO (N/C ✅), 4 个 ⚠️ 待确认

## 表 2：全部器件连接检查

### 电源部分

| 器件 | 封装 | 值 | 连接 | 状态 |
|------|------|---|------|------|
| U1 | SOT-23-6 | AP3032 | 1:SW, 2:GND, 3:LEDK, 4:BL_PWM, 5:OV, 6:BL_VIN | ✅ 升压驱动 |
| U3 | SOT-23-5 | LDO | 1:R12, 2:GND, 3:VBAT, 4:VBUS, 5:R13 | ✅ 充电管理 |
| U7 | L0603 | 10uH | 1:$1N156→L5, 2:$1N155→U8.B3(DCC) | ✅ REG1 DC/DC 电感 |
| U14 | L0603 | 10uH | 1:VDD_NRF_1V8, 2:DCCH→U8.AB2 | ✅ REG0 DC/DC 电感 |
| Q2 | SOT-23 | MOSFET | 1:VBUS, 2:VIN_RAW, 3:VBAT | ✅ 电池/USB 切换 |
| D11 | SOD-323 | 二极管 | 1:VIN_RAW, 2:VBUS | ✅ 反向保护 |
| D7 | SOD-323 | Schottky | 1:OV, 2:SW | ✅ 升压续流 |
| SW1 | MSK12C02 | 开关 | 2:VIN_RAW, 3:VIN | ✅ 电源开关 |

### 晶振

| 器件 | 封装 | 值 | 连接 | 状态 |
|------|------|---|------|------|
| X1 | FC-135R | 32.768kHz | 1:$1N132→U8.D2, 2:$1N133→U8.F2 | ✅ |
| X3 | 2.5×2.0 | 32MHz | 1:XC1_32M→U8.B24, 3:XC2_32M→U8.A23, 2,4:GND | ✅ |
| C6 | C0402 | 12pF | $1N132 — GND | ✅ X1 负载 |
| C7 | C0402 | 12pF | $1N133 — GND | ✅ X1 负载 |
| C17 | C0402 | 12pF | XC2_32M — GND | ✅ X3 负载 |
| C18 | C0402 | 12pF | XC1_32M — GND | ✅ X3 负载 |

### 去耦电容

| 器件 | 封装 | 值 | 连接 | 状态 |
|------|------|---|------|------|
| C1 | C0402 | 4.7uF | VBAT — GND | ✅ 电池去耦 |
| C2 | C0402 | 47nF | DEC4_6_1V3 — GND | ✅ |
| C5 | C0402 | 100nF | DEC1→U8.C1 — GND | ✅ 1.1V 去耦 |
| C8 | C0402 | 4.7uF | DECUSB→U8.AC5 — GND | ✅ USB 去耦 |
| C9 | C0402 | 1uF | DEC4_6_1V3 — GND | ✅ |
| C10 | C0402 | 100nF | VDD_NRF_1V8 — GND | ✅ |
| C13 | C0402 | 820pF | DEC5→U8.N24 — GND | ⚠️ 见问题 #3 |
| C14 | C0402 | 100nF | VDD_NRF_1V8 — GND | ✅ |
| C23 | C0402 | 100pF | DEC3→U8.D23 — GND | ⚠️ 建议改 100nF |
| C24 | C0402 | NC | $1N286→U8.A18(DEC2) — GND | ⚠️ 建议贴 100nF |
| C25 | C0402 | 100nF | VDD_NRF_1V8 — GND | ✅ 新增去耦 |
| C19 | C0402 | 1uF | VDD_NRF_1V8 — GND | ✅ |
| C20 | C0402 | 4.7uF | VDD_HV — GND | ✅ |
| C21 | C0402 | 4.7uF | VDD_NRF_1V8 — GND | ✅ |
| C22 | C0402 | 4.7uF | VBUS — GND | ✅ |

### 射频匹配网络

| 器件 | 封装 | 值 | 连接 | 状态 |
|------|------|---|------|------|
| C11 | C0402 | 1.5pF | $1N145→U8.H23(ANT)+L1.1 — GND | ✅ |
| C12 | C0402 | 1pF | $1N146→L1.2+L4.2+U22 — GND | ✅ |
| L1 | L0402 | 3.9nH | $1N145 — $1N146 | ✅ |
| L4 | L0402 | 100nH | GND — $1N146 | ✅ |
| L5 | L0402 | 15nH | DEC4_6_1V3 — $1N156→U7 | ✅ |
| U22 | ANT-SMD | 天线 | $1N146 | ✅ |

### 升压 (背光 LED)

| 器件 | 封装 | 值 | 连接 | 状态 |
|------|------|---|------|------|
| C3 | C0603 | 10uF | BL_VIN — GND | ✅ |
| C4 | C0603 | 1uF | OV — GND | ✅ |
| L2 | L_2520 | 6.8uH | BL_VIN — SW | ✅ |
| R4 | R0603 | 4.7kΩ | GND — BL_PWM | ✅ 下拉 |
| R5 | R0603 | 0Ω | BL_VIN — VIN | ✅ 跳线 |
| R7 | R0603 | 4.7Ω | LEDK — GND | ✅ 限流感测 |
| D2-D10 | LTW-010DCG | LED | 两串并联: D2→D4→D6→D8, D3→D5→D10→D9, 阳极OV, 阴极LEDK | ✅ |

### USB

| 器件 | 封装 | 值 | 连接 | 状态 |
|------|------|---|------|------|
| USB1 | TYPE-C-16P | USB-C | A4/A9/B4/B9:VBUS, A5:CC1, B5:CC2, A6/B6:DP, A7/B7:DN, A1/A12/B1/B12/25-28:GND | ✅ |
| R2 | R0402 | 5.1kΩ | GND — USB1.A5 (CC1) | ✅ |
| R3 | R0402 | 5.1kΩ | USB1.B5 (CC2) — GND | ✅ |
| R15 | R0402 | 22Ω | USB_DN — D-(U8.AD4) | ✅ USB 串阻 |
| R16 | R0402 | 22Ω | USB_DP — D+(U8.AD6) | ✅ USB 串阻 |

### RGB LED

| 器件 | 封装 | 值 | 连接 | 状态 |
|------|------|---|------|------|
| LED3 | LED-ARRAY-SMD 4P | RGB 共阴 | pin3→R20(Red), pin2→R21(Blue), pin1→R22(Green), pin4→GND | ✅ |
| R20 | R0402 | 1.5kΩ | LED_RED(U8.AC9/P0.14) — LED3.3 | ✅ ~1mA @Vf=1.8V |
| R21 | R0402 | 470Ω | LED_BLUE(U8.AC15/P0.19) — LED3.2 | ✅ ~1mA @Vf=2.8V |
| R22 | R0402 | 470Ω | LED_GREEN(U8.AC11/P0.16) — LED3.1 | ✅ ~1mA @Vf=2.8V |

### 状态 LED

| 器件 | 封装 | 值 | 连接 | 状态 |
|------|------|---|------|------|
| LED1 | LED0603-RD | 红 | 1:$1N227→R12, 2:VBUS | ✅ 充电指示 |
| LED2 | LED0603-WHITE | 白 | 1:$1N218→R11, 2:GND | ✅ |
| R11 | R0402 | 2kΩ | $1N218→LED2.1 — VBUS | ✅ |
| R12 | R0402 | 2kΩ | U3.1 — LED1.1 | ✅ |

### IMU (加速度计)

| 器件 | 封装 | 值 | 连接 | 状态 |
|------|------|---|------|------|
| U15 | LGA-14 | QMI8658 | SDA(14):IMU_SDA, SCL(13):IMU_SCL, INT1(4):IMU_INT1, INT2(9):IMU_INT2, VDD:5/8/10/12, GND:6/7, SDX(2):TP2, SCX(3):TP3, SA0(1):R10 | ✅ |
| R6 | R0402 | 0Ω | VDD_NRF_1V8 — VDD_IMU | ✅ 电源跳线 |
| R8 | R0402 | 5.1kΩ | IMU_SDA — VDD_IMU | ✅ I2C 上拉 |
| R9 | R0402 | 5.1kΩ | IMU_SCL — VDD_IMU | ✅ I2C 上拉 |
| R10 | R0402 | 10kΩ | IMU_S_ADDR(U15.1) — VDD_IMU | ✅ 地址=高 |
| C15 | C0402 | 100nF | VDD_IMU — GND | ✅ |
| C16 | C0402 | 100nF | VDD_IMU — GND | ✅ |
| TP1 | Test-Point | — | IMU_INT1 | ✅ |
| TP2 | Test-Point | — | IMU_SDX | ✅ |
| TP3 | Test-Point | — | IMU_SCX | ✅ |
| TP4 | Test-Point | — | POWER_PIN(U8.AD8/P0.13) | ✅ EXT_POWER 预留 |

### 外部 I2C 连接器

| 器件 | 封装 | 值 | 连接 | 状态 |
|------|------|---|------|------|
| CN5 | SM04B-SRSS | 4+2P | 1:GND, 2:I2C_VDD, 3:MCU_SDA, 4:MCU_SCL, 5:GND, 6:GND | ✅ |
| R17 | R0402 | 5.1kΩ | MCU_SCL — VDD_NRF_1V8 | ✅ I2C 上拉 |
| R18 | R0402 | 5.1kΩ | MCU_SDA — VDD_NRF_1V8 | ✅ I2C 上拉 |
| R19 | R0402 | 0Ω | I2C_VDD — VDD_NRF_1V8 | ✅ 电源跳线 |

### SWD 调试 + 电源开关 + 电池

| 器件 | 封装 | 值 | 连接 | 状态 |
|------|------|---|------|------|
| H1 | HDR-TH 5P | 排针 | 1:SWCLK, 2:SWDIO, 3:GND, 4:VDD_NRF_1V8, 5:RESET | ✅ |
| R1 | R0402 | 0Ω | VIN — VDD_HV(U8.Y2) | ✅ VDDH 跳线 |
| R13 | R0402 | 10kΩ | GND — U3.5 | ✅ |
| R14 | R0402 | 10kΩ | GND — VBUS | ✅ VBUS 检测分压 |
| CN1/CN3 | 2.5mm pad | 电池+ | VBAT | ✅ |
| CN2/CN4 | 2.5mm pad | 电池- | GND | ✅ |
| U9-U12 | SMD-1 BD4.4 | 按钮/弹片 | pin1: GND | ✅ |

### 键盘矩阵

| 器件 | 封装 | 连接 | 状态 |
|------|------|------|------|
| U2 | KeebDeck_Keyboard_6R13C_SwapTabAndE | R0-R5→ROW0-5(U8), C0-C11→COL0-11(U8) | ✅ 6R×12C |
| U13 | dome_sheet_6x13 | 机械件 | ✅ |

## 表 3：问题汇总

| # | 严重度 | 位置 | 问题 | 当前状态 | 建议 |
|---|--------|------|------|---------|------|
| 1 | ⚠️ 低 | A18 (DEC2) / C24 | C24 已连接但值标为 **NC**（不贴） | 焊盘已预留 | 贴 100nF 0402；若首板不贴也可后续补焊 |
| 2 | ⚠️ 低 | D23 (DEC3) / C23 | C23=**100pF** 偏小，DEC3 是电源去耦 | 已连接 | 建议改为 **100nF** (与 DEC1 的 C5 一致) |
| 3 | ❓ 信息 | N24 (DEC5) / C13 | C13=820pF。Datasheet: "Dxx and earlier 需要; **Fxx and later 应 N/C**" | 已连接 | 见下方芯片版本说明 |
| ~~4~~ | ✅ 已修 | A22 (VDD) | 已连接到 VDD_NRF_1V8 | — | — |

## nRF52840 订购编号与 Build Code（重要）

> **订购编号中的 build code 字段 ≠ 芯片丝印上的 build code 后缀，但它们指的是同一个硅版本。**

### 订购编号格式

```
nRF52840 - QIAA - F - R7
           ^^^^   ^   ^^
           封装    |   封装形式 (R7=Tape&Reel 7", T=Tray)
           变体    |
                   └── Build code 字段
```

| 订购编号中的字母 | 丝印标注 | FICR INFO.VARIANT | 含义 |
|-----------------|---------|-------------------|------|
| (无/省略) | — | — | **不指定 build code**，供应商发什么版本就是什么版本 |
| D | QIAA**D0** | 0x41414430 (AAD0) | 硅版本 D，**不推荐新设计** (PS v1.6 明确标注) |
| F | QIAA**F0** | 0x41414630 (AAF0) | 硅版本 F，**推荐用于新设计** |

### 当前采购情况

**已购型号: `nRF52840-QIAA-R`** — 订购编号中 **没有 build code 字段**（`-R` 直接接封装形式，省略了 `-F-` 或 `-D-`）。

这意味着供应商可能发 D0 或 F0 的芯片，取决于库存。收到货后应检查：
1. **芯片丝印**: 看最后两位是 `D0` 还是 `F0`
2. **FICR 寄存器**: 通过 JLink 读 `0x10000104` (INFO.VARIANT)

### 对 PCB 设计的影响

| 引脚 | D0 (Dxx) | F0 (Fxx) | 当前设计 | 兼容性 |
|------|----------|----------|---------|--------|
| N24 (DEC5) | 需要 820pF 去耦 | **应 N/C** | C13=820pF 已接 | ⚠️ F0 芯片上多了一个电容，但不会损坏，仅非最优 |
| A18 (DEC2) | 需要 100nF 去耦 | 需要 100nF 去耦 | C24=NC (焊盘预留) | ⚠️ D0/F0 都需要，建议贴上 |
| D23 (DEC3) | 需要去耦 | 需要去耦 | C23=100pF | ⚠️ 两者都需要，建议改 100nF |

**结论**: 当前 PCB 设计同时兼容 D0 和 F0 芯片，N24 (DEC5) 对 F0 多接了一个小电容但无害。**建议将 C24 从 NC 改为 100nF、C23 从 100pF 改为 100nF**，这样无论哪个 build code 都能正常工作。

## 备注

- **空闲 GPIO (13个)**: P1.10(A20), P0.30(B9), P0.28(B11), P1.14(B15), P1.12(B17), P0.27(H2), P0.07(M2), P1.08(P2), P1.07(P23), P1.05(T23), P0.12(U1), P1.03(V23), P1.01(Y23) — 均为正常 N/C
- **W24 (P1.02)**: 2.54 测试板版的 COL12，BLE PCB 版不使用，N/C 正常
- **QSPI 引脚 (3个)**: P0.21(AC17), P0.23(AC19), P0.25(AC21) — 未使用 QSPI，N/C 正常
- **AD8 (P0.13)**: 已连接 TP4 (POWER_PIN)，预留 EXT_POWER 控制
- **RGB LED ball 标签**: AC9=P0.14(Red), AC11=P0.16(Green), AC15=P0.19(Blue)，共阴极接 GND
