# nRF52840 低功耗项目调研 (2026-04)

基于互联网调研整理的 nRF52840 低功耗 maker 项目和商业产品，按类别分类。

## 键盘 & HID 输入设备

| 项目 | 说明 | 低功耗亮点 | 链接 |
|------|------|-----------|------|
| **nRF Desktop** | Nordic 官方 BLE 键盘/鼠标/dongle 参考设计 | 生产级功耗优化金标准 | [nordicsemi.com](https://nordicsemi.com/Products/Reference-designs/nRF-Desktop) |
| **nrfmicro** | 开源 Pro Micro 替代板，1.8k star | 专为无线键盘设计的睡眠模式 | [github](https://github.com/joric/nrfmicro) |
| **M60 Keyboard** | MakerDiary 60% BLE 键盘 PCB | BLE 5 + USB-C，支持 10 设备切换 | [makerdiary.com](https://makerdiary.com/products/m60-mechanical-keyboard-pcba) |
| **KMK Firmware** | Python (CircuitPython) 键盘固件 | 利用 CircuitPython 睡眠 API | [github](https://github.com/KMKfw/kmk_firmware) |
| **LOST60** | 蓝牙 60% 机械键盘自定义固件 | 独立 BLE 功耗管理 | [github](https://github.com/coyt/LOST60) |

## 智能手表 & 可穿戴

| 项目 | 说明 | 低功耗亮点 | 链接 |
|------|------|-----------|------|
| **InfiniTime / PineTime** | 最知名的开源智能手表 (nRF52832) | 一周续航，深度睡眠管理 | [github](https://github.com/InfiniTimeOrg/InfiniTime) |
| **K-Watch** | nRF52840 + Zephyr + MIP 显示屏 | MIP 静态显示零功耗 | [github](https://github.com/SonDinh23/K-Watch) |
| **SMA Q3 Hackable Watch** | nRF52840 运行 Espruino/Bangle.js | JavaScript 手表 OS，功耗管理出色 | [hackaday.io](https://hackaday.io/project/175577-hackable-nrf52840-smart-watch) |
| **Flexwatch** | 柔性 PCB + 墨水屏极简手表 | 墨水屏 + 柔性 PCB = 极低待机 | [osrtos.com](https://osrtos.com/projects/flexwatch/) |

## 墨水屏 / E-Paper

| 项目 | 说明 | 低功耗亮点 | 链接 |
|------|------|-----------|------|
| **T-Echo Lite (LILYGO)** | nRF52840 + SX1262 LoRa + 墨水屏 | 三重低功耗：nRF 深睡 + LoRa 睡眠 + 墨水屏零功耗静态显示 | [lilygo.cc](https://lilygo.cc/products/t-echo-lite) |
| **Papyr** | nRF52840 + 墨水屏，支持 BLE/Thread/Zigbee | 墨水屏静态显示零功耗 + 多协议 | [hackaday.io](https://hackaday.io/project/165467-papyr-nrf52840-epaper-display) |
| **Wio Tracker L1 E-ink** | nRF52840 + LoRa + GPS + 墨水屏 | 始终显示位置/消息，无额外功耗 | [seeedstudio.com](https://seeedstudio.com/Wio-Tracker-L1-E-ink-p-6456.html) |

## Mesh 网络 & 离网通信

| 项目 | 说明 | 低功耗亮点 | 链接 |
|------|------|-----------|------|
| **Meshtastic** | 开源 LoRa mesh 通信平台 | nRF52840 深睡 + LoRa 间歇发射，续航数天 | [github](https://github.com/meshtastic/firmware) |
| **SenseCAP Solar Node P1-Pro** | 太阳能 LoRa mesh 中继 | MPPT 太阳能充电 = 无限续航 | [seeedstudio.com](https://seeedstudio.com/SenseCAP-Solar-Node-P1-Pro-for-Meshcore-p-6741.html) |
| **Heltec Mesh Node T114** | nRF52840 + SX1262 + TFT + GPS | 多电源输入（USB/电池/太阳能） | [heltec.org](https://heltec.org/project/mesh-node-t114/) |

## 环境监测 & 空气质量

| 项目 | 说明 | 低功耗亮点 | 链接 |
|------|------|-----------|------|
| **Zicada Zigbee Multisensor** | 温湿度/门窗/光照，全开源 | **6μW 待机，AAA 电池 2 年+** | [hackaday.io](https://hackaday.io/project/204509-zicada-diy-zigbee-multisensor) |
| **Cellabox** | 开源 Thread mesh 空气质量监测 | Thread 低功耗 mesh + IPv6/CoAP | [github](https://github.com/cellabox/cellabox) |
| **Zigbee 温度传感器** | 管道温度测量 (NTC + Zigbee) | 预计纽扣电池 1.5 年，2000mAh 电池 10 年 | [github](https://github.com/tomasmcguinness/zigbee-nrf-flow-and-return-temperature-sensor) |
| **Glen Akins 门传感器** | 霍尔效应 + Zigbee 户外门传感器 | CR2450 纽扣电池跑了一整个夏+冬 | [bikerglen.com](https://bikerglen.com/blog/building-a-battery-powered-zigbee-gate-sensor/) |

## 资产追踪 & GPS

| 项目 | 说明 | 低功耗亮点 | 链接 |
|------|------|-----------|------|
| **RAK WisMesh Tag** | 最小 Meshtastic 追踪器 ($29) | 极致小型化 + GPS/Radio 占空比控制 | [nodakmesh.org](https://nodakmesh.org/setup/rak-wismesh-tag/) |
| **Link Smart Pet Wearable** | nRF9160 (LTE) + nRF52840 (BLE) 双芯片 | 近距离用 BLE（低功耗），远距离切蜂窝（高功耗但少用） | [nordicsemi.com](https://nordicsemi.com/Nordic-news/2021/09/Link-smart-pet-wearable-uses-nRF9160-SiP-and-nRF52840-SoC) |
| **Pet Activity Tracker** | XIAO BLE Sense + IMU + 边缘 ML | 端侧 ML 推理避免持续数据传输 | [hackster.io](https://hackster.io/mithun-das/pet-activity-tracker-using-xiao-ble-sense-edge-impulse-858d73) |

## 智能家居

| 项目 | 说明 | 低功耗亮点 | 链接 |
|------|------|-----------|------|
| **Secuyou Smart Lock Matter** | Matter-over-Thread 智能门锁 | Thread sleepy end device，电池续航数年 | [nordicsemi.com](https://nordicsemi.com/Nordic-news/2024/12/Secuyou-Smart-Lock-Matter-integrates-nRF52840) |
| **Level Lock** | BLE 无钥匙门锁，Zephyr RTOS | 生产级 Zephyr 功耗管理 | [zephyrproject.org](https://zephyrproject.org/nordics-nrf52840-soc-zephyr-rtos-enable-keyless-entry/) |

## 农业

| 项目 | 说明 | 低功耗亮点 | 链接 |
|------|------|-----------|------|
| **SoiLiNQ** | 无线土壤监测系统 | 为无人值守农业部署设计 | [nordicsemi.com](https://nordicsemi.com/Nordic-news/2024/05/SoiLiNQ-employs-the-nRF52840-SoC) |
| **Meshtastic 土壤湿度传感器** | XIAO nRF52840 + I2C 电容式土壤湿度 | 利用 Meshtastic 功耗管理 + LoRa 远距离 | [github](https://github.com/benb0jangles/Meshtastic-Capacitive-Soil-Moisture-Sensor-nRF52840-) |

## 航空

| 项目 | 说明 | 低功耗亮点 | 链接 |
|------|------|-----------|------|
| **SoftRF** | 开源 DIY 航空近场感知系统 | 信用卡大小，FCC/CE 认证，IP66 防水 | [github](https://github.com/lyusupov/SoftRF) |

## 低功耗 Top 10

| 排名 | 项目 | 亮点 |
|------|------|------|
| 1 | **Zicada Zigbee Multisensor** | 6μW 待机，AAA 电池 2 年+，完全开源 |
| 2 | **Glen Akins 门传感器** | 纽扣电池跑了一整年，详细功耗分析博客 |
| 3 | **T-Echo Lite** | 三重低功耗（nRF52840 + LoRa + 墨水屏） |
| 4 | **InfiniTime/PineTime** | 最成熟的开源手表固件，一周续航 |
| 5 | **Cellabox** | Thread mesh 空气质量网络，完全开源 |
| 6 | **K-Watch** | MIP 显示屏 + Zephyr = 静态显示零功耗 |
| 7 | **Meshtastic nRF52840** | mesh 续航数天，庞大社区 |
| 8 | **SoftRF** | 信用卡大小的航空安全设备 |
| 9 | **nRF Desktop** | Nordic 官方 HID 功耗优化参考 |
| 10 | **Zigbee 温度传感器** | 2000mAh 电池预计 10 年 |

## 与 keebdeck 的关联

- **nRF Desktop**: 功耗优化参考，值得研究其 HID 事件驱动架构
- **Pet Activity Tracker**: XIAO BLE Sense + IMU + 边缘 ML，和 keebdeck 飞鼠功能思路类似
- **nrfmicro**: ZMK 键盘生态的硬件基础
- **Zicada**: 6μW 待机的实现方式值得参考（Zigbee end device 模式）
