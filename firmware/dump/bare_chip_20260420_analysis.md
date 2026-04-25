# nRF52840 裸片 Flash Dump 分析 (2026-04-20)

## 基本信息

| 项目 | 值 |
|------|-----|
| JLink | OB-Mini Plus, S/N 63728786 |
| VTref | 3.3V |
| MCU | nRF52840 (Part: 0x00052840) |
| Package | QFN48 7x7mm ("AAD0") — E73-2G4M08S1C 模组 |
| RAM | 256KB |
| Flash | 1MB |
| Device ID | FE96CCE3:ECEC7E63 |
| BLE MAC | ~DB:40:28:B2:26:BD (random type, addr type=0xFF) |
| APPROTECT | 0xFF (未保护，可读写) |
| PSELRESET | P0.18 (两个 PSELRESET 都配置为 0x12) |
| Bootloader Addr | 0xFFFFFFFF (未设置) |
| MBR Params | 0xFFFFFFFF (未设置) |

## UICR 状态

UICR 基本为空 (全 0xFF)，仅有：
- **PSELRESET[0] & [1]**: 0x00000012 (P0.18) — offset 0x200
- **FICR string** at offset 0x80: `RH88FIRS45082480` — 工厂标识

Bootloader 地址和 MBR Params 均未设置 → 芯片上没有烧录过 bootloader。

## Flash 布局

```
0x00000 - 0x00FFF  MBR (4KB)         SP=0x20000400 Reset=0x00000A81
0x01000 - 0x26FFF  SoftDevice S140 v6.1.1 (156KB)  FWID=0x00B6
0x27000 - 0x90FFF  Application (424KB)
0x91000 - 0xFCFFF  空闲 (0xFF)
0xFD000 - 0xFFFFF  NVS 存储 (12KB, magic=0xDEADC0DE)
```

总使用: 148/256 pages (592KB / 1024KB)

## 固件分析

**这不是 ZMK 固件，也不是键盘固件。**

根据固件中的字符串分析，这是一个 **BLE 摄像头/图像捕获** 相关的应用，特征：

### 关键特征
- **OV7676 摄像头传感器**: 有 `Resetting OV7676` 字符串
- **图像捕获功能**: `ImageCaptureRun`, `CaptureActive`, `CaptureFinished`, `CountdownToCapture`
- **BLE 服务**: 自定义 GATT 服务用于图像传输通知 (`cartridge_insert`, `img_capture_complete`, `img_capture_status`)
- **LZ4 压缩**: 使用 LZ4 进行图像数据压缩
- **NVS 存储**: 使用 Zephyr NVS (Non-Volatile Storage) 在 flash 末尾 (0xFD000-0xFFFFF)
- **RTT 日志**: 有 `rtt_log_backend` 支持
- **nRF SDK**: 基于 Nordic nRF5 SDK (非 Zephyr/ZMK)

### BLE 功能
- LESC 配对 (LE Secure Connections)
- GATT MTU 交换
- 数据长度更新 (DLE)
- 连接状态管理
- 安全特性读写

### 可能的项目
看起来像是一个 **Game Boy Camera BLE** 项目或类似的小型 BLE 摄像头设备固件。使用 OV7676 传感器拍照，通过 BLE 传输到手机。

## 文件列表

| 文件 | MD5 | 大小 |
|------|-----|------|
| dump_full_flash_bare_chip_20260420.bin | 63818627161d8738c52b5b9164f6a3fb | 1MB |
| dump_uicr_bare_chip_20260420.bin | 5dad9f7112b0a4cc5e376d8f4644623b | 1KB |

## 购买信息

- **淘宝店铺**: 凌创芯选 RF 射频器件
- **标称**: 全新 nRF52840 / E73-2G4M08S1C 模组
- **实际**: 二手翻新 — Flash 内含完整终端产品固件（OV7676 BLE 摄像头），NVS 有运行数据

## 备注

- 这颗芯片之前已经烧录过固件（非空白），但 UICR 中没有 bootloader 配置
- APPROTECT 未开启，可以自由读写
- 如果要刷 ZMK，需要先 erase all，再烧录 SoftDevice + Bootloader + ZMK app
