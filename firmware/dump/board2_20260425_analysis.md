# nRF52840 Board2 Flash Dump 分析 (2026-04-25)

## 基本信息

| 项目 | 值 |
|------|-----|
| JLink | OB-Mini Plus, S/N 63728786 |
| VTref | 3.3V |
| MCU | nRF52840 (Part: 0x00052840) |
| Package | QFN48 7x7mm ("AAD0") — E73-2G4M08S1C 模组 |
| RAM | 256KB |
| Flash | 1MB |
| Device ID | 10622682:909A3455 |
| BLE MAC | 93:02:D7:0B / 11:96:58:1E (addr type=0xFF) |
| APPROTECT | 0xFF (未保护，可读写) |
| PSELRESET | P0.18 (两个 PSELRESET 都配置为 0x12) |
| Bootloader Addr | 0x000D5000 (有自研 IAP bootloader) |
| MBR Params | 0x000F4000 |
| FICR 标识 | 空 (全 0xFF) |

## UICR 状态

UICR 基本为空 (全 0xFF)，仅有：
- **PSELRESET[0] & [1]**: 0x00000012 (P0.18) — offset 0x200
- **Bootloader Address**: 0x000D5000 — offset 0x14
- **MBR Params**: 0x000F4000 — offset 0x18
- 无 FICR 工厂标识字符串

## Flash 布局

```
0x00000 - 0x25FFF  MBR + SoftDevice S140 (152KB)
0x26000 - 0x27FFF  空闲 (8KB)
0x28000 - 0x7BFFF  Application (336KB)
0x7D000 - 0x89FFF  Application 续/数据 (52KB)
0x8A000 - 0xD1FFF  空闲 (0xFF)
0xD2000 - 0xEDFFF  Bootloader 区域 (112KB)
0xEE000 - 0xFEFFF  空闲 (0xFF)
0xFF000 - 0xFFFFF  配置/NVS (4KB)
```

总使用: ~652KB / 1024KB

## 固件分析

**这是 Mobike (摩拜/美团) 共享单车智能锁固件。**

### 项目信息
- **项目名**: `baselock_nrf52840`
- **开发者**: `liuxiang` (bootloader), `mtdp` (主应用)
- **源码路径**:
  - Bootloader: `/Users/liuxiang/Desktop/project/mos/`
  - 主应用: `/Users/mtdp/c/baselock_nrf52840/`
- **BLE 广播名**: `##MOBIKE_xx_xxx`
- **RTOS**: FreeRTOS
- **SDK**: Nordic nRF5 SDK (非 Zephyr)

### 功能模块
- **智能锁控制**: 电机开锁/闭锁 (`frm_lock.c`, `drv_motor.c`, `drv_swdet.c`)
- **GPS 定位**: 位置上报、围栏检测
- **蜂窝通信**: SIM868 模组 (`drv_sim868.c`, `frm_gsm_thread.c`, `frm_cellular.c`)
- **BLE**: beacon 扫描 (type-A/B)、寻找其他单车、RSSI 测量
- **WiFi**: WiFi 定位辅助 (`drv_wifi.c`)
- **异常检测**: 加速度计异常移动报警 (`abnoramal moved detected`)
- **OTA**: 空中固件升级 (IAP bootloader + FOTA)
- **HTTP**: 与服务端通信 (`http.c`)
- **看门狗**: `drv_wdg.c`
- **低功耗**: 停车模式 (Park Mode)、睡眠管理

### Bootloader
自研 IAP bootloader 位于 0xD5000，由 `liuxiang` 开发:
- 路径: `/Users/liuxiang/Desktop/project/mos/app/nrf52840_bl/`
- 功能: 固件校验、IAP 升级、App 跳转
- 日志: `=====BootLoader Start===== [0x%X]`

## 与 Board1 对比

| | Board 1 (4月20日) | Board 2 (4月25日) |
|---|---|---|
| Device ID | FE96CCE3:ECEC7E63 | 10622682:909A3455 |
| 原产品 | BLE 摄像头 (OV7676) | **Mobike 共享单车智能锁** |
| Bootloader | 无 | 有 (0xD5000, 自研 IAP) |
| FICR 标识 | RH88FIRS45082480 | 空 |
| App 大小 | 424KB | ~388KB |
| 来源 | 不同产品/不同批次 | 不同产品/不同批次 |

## 文件列表

| 文件 | MD5 | 大小 |
|------|-----|------|
| dump_full_flash_board2_20260425.bin | f3568cba443a061ba28f97d2e7add6bb | 1MB |
| dump_uicr_board2_20260425.bin | (见文件) | 1KB |

## 购买信息

- **淘宝店铺**: 凌创芯选 RF 射频器件
- **标称**: 全新 nRF52840 / E73-2G4M08S1C 模组
- **实际**: 二手拆机件 — Flash 内含 Mobike 共享单车智能锁完整固件，含自研 bootloader
- **结论**: 同一卖家两颗芯片来自不同产品（BLE 摄像头 vs 共享单车锁），均为二手翻新
