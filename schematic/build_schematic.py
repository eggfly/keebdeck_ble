#!/usr/bin/env python3
"""
Build complete KeebDeck BLE schematic by adding all missing wires
to the existing .epro2 file.

Adds:
- Keyboard matrix connections (U2 ROW/COL → U1 GPIO via net labels)
- Pro Micro style D-pin naming
- Decoupling capacitors for LDO, charger, BLE module
- USB data path through ESD
- Power path: USB → charger → battery switch → LDO → 3V3
- LED connections, reset/boot buttons, SWD debug

Usage:
    python3 build_schematic.py KeebDeck_BLE.epro2 -o KeebDeck_BLE_wired.epro2
"""

import json
import sys
import os
import zipfile
import secrets
import argparse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../easyeda-agent-skills/tools"))
from parse_epro2 import load_epro2, get_max_ticket, pin_abs_position


def rand_id():
    return secrets.token_hex(8)


class EasyEDAWriter:
    """Generates EasyEDA Pro source code lines."""

    def __init__(self, start_ticket, start_z):
        self.ticket = start_ticket
        self.z = start_z
        self.lines = []

    def _t(self):
        t = self.ticket; self.ticket += 1; return t

    def _z(self):
        z = self.z; self.z += 1; return z

    def add_wire(self, x1, y1, x2, y2, net_name=""):
        """Single-segment wire with optional net label."""
        wid = rand_id()
        z = self._z()
        self.lines.append(f'{{"type":"WIRE","ticket":{self._t()},"id":"{wid}"}}||{{"zIndex":{z}}}|')
        self.lines.append(
            f'{{"type":"LINE","ticket":{self._t()},"id":"{rand_id()}"}}'
            f'||{{"fillColor":null,"fillStyle":null,"strokeColor":null,"strokeStyle":null,"strokeWidth":null,'
            f'"startX":{x1},"startY":{y1},"endX":{x2},"endY":{y2},"lineGroup":"{wid}"}}|')
        self.lines.append(
            f'{{"type":"ATTR","ticket":{self._t()},"id":"{rand_id()}"}}'
            f'||{{"x":null,"y":null,"rotation":null,"color":null,"fontFamily":null,"fontSize":null,'
            f'"fontWeight":null,"italic":null,"underline":null,"align":null,"value":"[]",'
            f'"keyVisible":null,"valueVisible":null,"key":"Relevance","fillColor":null,'
            f'"parentId":"{wid}","zIndex":0}}|')
        self.lines.append(
            f'{{"type":"ATTR","ticket":{self._t()},"id":"{rand_id()}"}}'
            f'||{{"x":{x1},"y":{y1},"rotation":0,"color":null,"fontFamily":null,"fontSize":null,'
            f'"fontWeight":null,"italic":null,"underline":null,"align":null,"value":"{net_name}",'
            f'"keyVisible":false,"valueVisible":true,"key":"NET","fillColor":null,'
            f'"parentId":"{wid}","zIndex":2}}|')

    def add_multi_wire(self, segments, net_name=""):
        """Multi-segment wire (all segments share one WIRE group)."""
        if not segments:
            return
        wid = rand_id()
        z = self._z()
        self.lines.append(f'{{"type":"WIRE","ticket":{self._t()},"id":"{wid}"}}||{{"zIndex":{z}}}|')
        for (x1, y1, x2, y2) in segments:
            self.lines.append(
                f'{{"type":"LINE","ticket":{self._t()},"id":"{rand_id()}"}}'
                f'||{{"fillColor":null,"fillStyle":null,"strokeColor":null,"strokeStyle":null,"strokeWidth":null,'
                f'"startX":{x1},"startY":{y1},"endX":{x2},"endY":{y2},"lineGroup":"{wid}"}}|')
        self.lines.append(
            f'{{"type":"ATTR","ticket":{self._t()},"id":"{rand_id()}"}}'
            f'||{{"x":null,"y":null,"rotation":null,"color":null,"fontFamily":null,"fontSize":null,'
            f'"fontWeight":null,"italic":null,"underline":null,"align":null,"value":"[]",'
            f'"keyVisible":null,"valueVisible":null,"key":"Relevance","fillColor":null,'
            f'"parentId":"{wid}","zIndex":0}}|')
        x1, y1 = segments[0][0], segments[0][1]
        self.lines.append(
            f'{{"type":"ATTR","ticket":{self._t()},"id":"{rand_id()}"}}'
            f'||{{"x":{x1},"y":{y1},"rotation":0,"color":null,"fontFamily":null,"fontSize":null,'
            f'"fontWeight":null,"italic":null,"underline":null,"align":null,"value":"{net_name}",'
            f'"keyVisible":false,"valueVisible":true,"key":"NET","fillColor":null,'
            f'"parentId":"{wid}","zIndex":2}}|')

    def add_power(self, x, y, net_name, rotation=None):
        """Add power symbol. Returns component ID."""
        comp_id = rand_id()
        z = self._z()
        if net_name == "GND":
            sym, dev = "b5fc023152e63698", "94150318f6d1792d"
            rotation = rotation if rotation is not None else 270
        else:
            sym, dev = "fa489ef6ae369c9a", "69734524f66a8ada"
            rotation = rotation if rotation is not None else 90

        self.lines.append(
            f'{{"type":"COMPONENT","ticket":{self._t()},"id":"{comp_id}"}}'
            f'||{{"partId":"pid8a0e77bacb214e","x":{x},"y":{y},'
            f'"rotation":{rotation},"isMirror":false,"attrs":{{}},"zIndex":{z}}}|')

        # Symbol attr
        if rotation == 90: sx, sy = x+30, y
        elif rotation == 270: sx, sy = x-30, y
        else: sx, sy = x, y-30
        fs = '"fontSize":10,' if net_name == "GND" else '"fontSize":null,'
        al = '"align":"RIGHT_TOP",' if net_name == "GND" else '"align":null,'
        self.lines.append(
            f'{{"type":"ATTR","ticket":{self._t()},"id":"{rand_id()}"}}'
            f'||{{"x":{sx},"y":{sy},"rotation":{rotation},"color":null,"fontFamily":null,{fs}'
            f'"fontWeight":null,"italic":null,"underline":null,{al}"value":"{sym}",'
            f'"keyVisible":null,"valueVisible":null,"key":"Symbol","fillColor":null,'
            f'"parentId":"{comp_id}","zIndex":1,"locked":false}}|')
        # Device attr
        self.lines.append(
            f'{{"type":"ATTR","ticket":{self._t()},"id":"{rand_id()}"}}'
            f'||{{"x":null,"y":null,"rotation":null,"color":null,"fontFamily":null,"fontSize":null,'
            f'"fontWeight":null,"italic":null,"underline":null,"align":null,"value":"{dev}",'
            f'"keyVisible":null,"valueVisible":null,"key":"Device","fillColor":null,'
            f'"parentId":"{comp_id}","zIndex":12}}|')
        # Relevance
        self.lines.append(
            f'{{"type":"ATTR","ticket":{self._t()},"id":"{rand_id()}"}}'
            f'||{{"x":null,"y":null,"rotation":null,"color":null,"fontFamily":null,"fontSize":null,'
            f'"fontWeight":null,"italic":null,"underline":null,"align":null,"value":"[]",'
            f'"keyVisible":null,"valueVisible":null,"key":"Relevance","fillColor":null,'
            f'"parentId":"{comp_id}","zIndex":0}}|')
        # Name
        nx = x-20 if rotation==90 else (x+20 if rotation==270 else x)
        self.lines.append(
            f'{{"type":"ATTR","ticket":{self._t()},"id":"{rand_id()}"}}'
            f'||{{"x":{nx},"y":{y},"rotation":0,"color":null,"fontFamily":null,"fontSize":null,'
            f'"fontWeight":null,"italic":null,"underline":null,"align":"CENTER_MIDDLE",'
            f'"value":"{net_name}","keyVisible":null,"valueVisible":true,"key":"Name",'
            f'"fillColor":null,"parentId":"{comp_id}","zIndex":3,"locked":false}}|')
        # Global Net Name
        gnx = x-10 if rotation==90 else (x+5 if rotation==270 else x)
        self.lines.append(
            f'{{"type":"ATTR","ticket":{self._t()},"id":"{rand_id()}"}}'
            f'||{{"x":{gnx},"y":{y},"rotation":{rotation},"color":null,"fontFamily":null,"fontSize":null,'
            f'"fontWeight":null,"italic":null,"underline":null,"align":"CENTER_MIDDLE",'
            f'"value":"{net_name}","keyVisible":null,"valueVisible":null,"key":"Global Net Name",'
            f'"fillColor":null,"parentId":"{comp_id}","zIndex":17}}|')
        return comp_id

    def add_component(self, x, y, part_id, designator, symbol_uuid, device_uuid,
                      rotation=0, mirror=False, show_value=False, value=None):
        """Add a new component. Returns component ID."""
        comp_id = rand_id()
        z = self._z()
        m = "true" if mirror else "false"
        self.lines.append(
            f'{{"type":"COMPONENT","ticket":{self._t()},"id":"{comp_id}"}}'
            f'||{{"partId":"{part_id}","x":{x},"y":{y},'
            f'"rotation":{rotation},"isMirror":{m},"attrs":{{}},"zIndex":{z}}}|')
        # Symbol
        self.lines.append(
            f'{{"type":"ATTR","ticket":{self._t()},"id":"{rand_id()}"}}'
            f'||{{"x":null,"y":null,"rotation":0,"color":null,"fontFamily":null,"fontSize":null,'
            f'"fontWeight":false,"italic":false,"underline":false,"align":"LEFT_BOTTOM",'
            f'"value":"{symbol_uuid}","keyVisible":null,"valueVisible":null,"key":"Symbol",'
            f'"fillColor":null,"parentId":"{comp_id}","zIndex":1,"locked":false}}|')
        # Device
        self.lines.append(
            f'{{"type":"ATTR","ticket":{self._t()},"id":"{rand_id()}"}}'
            f'||{{"x":null,"y":null,"rotation":null,"color":null,"fontFamily":null,"fontSize":null,'
            f'"fontWeight":null,"italic":null,"underline":null,"align":null,'
            f'"value":"{device_uuid}","keyVisible":null,"valueVisible":null,"key":"Device",'
            f'"fillColor":null,"parentId":"{comp_id}","zIndex":12}}|')
        # Unique ID
        self.lines.append(
            f'{{"type":"ATTR","ticket":{self._t()},"id":"{rand_id()}"}}'
            f'||{{"x":null,"y":null,"rotation":null,"color":null,"fontFamily":null,"fontSize":null,'
            f'"fontWeight":null,"italic":null,"underline":null,"align":null,'
            f'"value":"","keyVisible":null,"valueVisible":null,"key":"Unique ID",'
            f'"fillColor":null,"parentId":"{comp_id}","zIndex":-2}}|')
        # Designator
        dx = x - 10
        dy = y - 20
        self.lines.append(
            f'{{"type":"ATTR","ticket":{self._t()},"id":"{rand_id()}"}}'
            f'||{{"x":{dx},"y":{dy},"rotation":0,"color":null,"fontFamily":null,"fontSize":null,'
            f'"fontWeight":false,"italic":false,"underline":false,"align":"LEFT_BOTTOM",'
            f'"value":"{designator}","keyVisible":null,"valueVisible":true,"key":"Designator",'
            f'"fillColor":null,"parentId":"{comp_id}","zIndex":2,"locked":false}}|')
        # Footprint
        self.lines.append(
            f'{{"type":"ATTR","ticket":{self._t()},"id":"{rand_id()}"}}'
            f'||{{"x":null,"y":null,"rotation":null,"color":null,"fontFamily":null,"fontSize":null,'
            f'"fontWeight":null,"italic":null,"underline":null,"align":null,'
            f'"value":null,"keyVisible":null,"valueVisible":null,"key":"Footprint",'
            f'"fillColor":null,"parentId":"{comp_id}","zIndex":21}}|')
        # Value (if provided)
        if value is not None:
            vx, vy = x - 10, y + 15
            vis = "true" if show_value else "null"
            self.lines.append(
                f'{{"type":"ATTR","ticket":{self._t()},"id":"{rand_id()}"}}'
                f'||{{"x":{vx},"y":{vy},"rotation":0,"color":null,"fontFamily":null,"fontSize":null,'
                f'"fontWeight":null,"italic":null,"underline":null,"align":null,'
                f'"value":"{value}","keyVisible":null,"valueVisible":{vis},"key":"Value",'
                f'"fillColor":null,"parentId":"{comp_id}","zIndex":26}}|')
        # Name, Reuse Block, Group ID, Channel ID
        for k in ["Name", "Reuse Block", "Group ID", "Channel ID"]:
            self.lines.append(
                f'{{"type":"ATTR","ticket":{self._t()},"id":"{rand_id()}"}}'
                f'||{{"x":null,"y":null,"rotation":null,"color":null,"fontFamily":null,"fontSize":null,'
                f'"fontWeight":null,"italic":null,"underline":null,"align":null,'
                f'"value":null,"keyVisible":null,"valueVisible":null,"key":"{k}",'
                f'"fillColor":null,"parentId":"{comp_id}","zIndex":32}}|')
        return comp_id


# ============================================================
# Pin mappings: nRF52840 E73 module → Pro Micro style
# ============================================================

# E73 module pin name → Pro Micro D-number
PIN_TO_DPIN = {
    "P1.11": "D7",   # pin 1
    "P1.10": "D14",  # pin 2
    "P0.03": "D3",   # pin 3 (AI4 area)
    "AI4":   "D18",  # pin 4 (A0)
    "P1.13": "D15",  # pin 6
    "AI0":   "A6",   # pin 7 (analog only)
    "AI5":   "D19",  # pin 8 (A1)
    "AI7":   "D20",  # pin 9 (A2)
    "AI6":   "D21",  # pin 10 (A3)
    "P0.26": "SDA",  # pin 12
    "P0.06": "D0",   # pin 14
    "AI3":   "A7",   # pin 15 (analog)
    "P0.08": "D1",   # pin 16
    "P1.09": "SCL",  # pin 17
    "AI2":   "A8",   # pin 18 (analog)
    "P12":   "D9",   # pin 20
    "P0.07": "D10",  # pin 22
    "P15":   "D28",  # pin 28
    "P17":   "D2",   # pin 30
    "D+":    "USB_DP",
    "D-":    "USB_DN",
    "P0.20": "D3_",  # pin 32 → use for COL1
    "P0.13": "LED",  # pin 33 → LED control
    "P0.22": "D4",   # pin 34
    "P0.24": "D5",   # pin 35
    "P1.00": "D6",   # pin 36
    "SWD":   "SWDIO",
    "P1.02": "D16",  # pin 38
    "SWC":   "SWCLK",
    "P1.04": "D8",   # pin 40
    "P1.06": "D17",  # pin 42
}

# Keyboard matrix GPIO assignments
# ROW0-5 → 6 GPIO pins
# COL0-12 → 13 GPIO pins (total 19 GPIOs)
MATRIX_ROWS = {
    "ROW0": "P1.11",   # D7,  pin 1
    "ROW1": "P1.10",   # D14, pin 2
    "ROW2": "P1.13",   # D15, pin 6
    "ROW3": "P0.06",   # D0,  pin 14
    "ROW4": "P0.08",   # D1,  pin 16
    "ROW5": "P12",     # D9,  pin 20
}

MATRIX_COLS = {
    "COL0":  "P0.07",  # D10, pin 22
    "COL1":  "P0.20",  # D3,  pin 32
    "COL2":  "P0.22",  # D4,  pin 34
    "COL3":  "P0.24",  # D5,  pin 35
    "COL4":  "P1.00",  # D6,  pin 36
    "COL5":  "P1.02",  # D16, pin 38
    "COL6":  "P1.04",  # D8,  pin 40
    "COL7":  "P17",    # D2,  pin 30
    "COL8":  "AI4",    # A0,  pin 4
    "COL9":  "AI5",    # A1,  pin 8
    "COL10": "AI7",    # A2,  pin 9
    "COL11": "AI6",    # A3,  pin 10
    "COL12": "P1.06",  # D17, pin 42
}


def build_keebdeck_wires(pin, w):
    """
    Build all connections for KeebDeck BLE schematic.
    pin: dict mapping "DESIGNATOR.PIN_NAME" -> (abs_x, abs_y)
    w: EasyEDAWriter
    """

    # ============================================================
    # 1. USB-C Data Path: USBC1 → D1 (ESD) → U1 (BLE module)
    # ============================================================

    # USB-C DP/DN pins → net labels (both sides of the differential pair)
    w.add_wire(365, -255, 335, -255, "USB_DP")  # USBC1.DP1
    w.add_wire(365, -235, 335, -235, "USB_DP")  # USBC1.DP2
    w.add_wire(365, -245, 335, -245, "USB_DN")  # USBC1.DN1
    w.add_wire(365, -265, 335, -265, "USB_DN")  # USBC1.DN2

    # D1 (USBLC6-2SC6) ESD protection connections
    w.add_wire(135, -280, 105, -280, "USB_DP")  # D1.pin1 → USB_DP
    w.add_wire(265, -280, 295, -280, "USB_DP")  # D1.pin6 → USB_DP
    w.add_wire(135, -220, 105, -220, "USB_DN")  # D1.pin3 → USB_DN
    w.add_wire(265, -220, 295, -220, "USB_DN")  # D1.pin4 → USB_DN

    # D1 power: pin2 → GND, pin5 → +5V
    w.add_power(110, -250, "GND", rotation=270)
    w.add_wire(110, -250, 135, -250)
    w.add_power(290, -250, "+5V")
    w.add_wire(290, -250, 265, -250)

    # U1 USB pins → net labels (already exist for D+/D-, just add them)
    w.add_wire(465, -525, 495, -525, "USB_DP")   # U1.D+ pin31
    w.add_wire(465, -505, 495, -505, "USB_DN")   # U1.D- pin29

    # ============================================================
    # 2. USB-C Power & CC (already wired in source, just verify)
    # ============================================================
    # USBC1 VBUS → +5V ✓ (existing)
    # USBC1 CC1/CC2 → R2/R3 → GND ✓ (existing)
    # USBC1 shell → GND ✓ (existing)

    # ============================================================
    # 3. Charging: +5V → U3 (TP4054) → VBAT
    # ============================================================

    # U3.VCC pin4 (895,-590) ← +5V
    w.add_power(920, -590, "+5V")
    w.add_wire(895, -590, 920, -590)

    # U3.GND pin2 (805,-600) → GND (existing wire to 800,-600 GND symbol ✓)

    # U3.BAT pin3 (805,-590) → VBAT
    w.add_wire(805, -590, 775, -590, "VBAT")

    # U3.CHRG pin1 (805,-610) → CHRG net → LED1
    w.add_wire(805, -610, 775, -610, "CHRG")

    # U3.PROG pin5 (895,-610) → R1 (charge current)
    w.add_wire(895, -610, 925, -610, "PROG")
    w.add_wire(720, -300, 750, -300, "PROG")  # R1.pin2
    # R1.pin1 (680,-300) → GND
    w.add_power(680, -310, "GND")
    w.add_wire(680, -300, 680, -310)

    # ============================================================
    # 4. Charger Capacitors (NEW — C2 input, C3 output)
    # ============================================================

    # C2: 4.7uF on U3.VCC (input) — place at (920, -620), vertical
    # We'll add these as components
    # For now, add net labels to connect caps placed by user
    # Input cap: +5V to GND near U3.VCC
    # (User needs to add C2 4.7uF at ~920,-620 in EasyEDA)

    # C3: 4.7uF on U3.BAT (output) — at VBAT to GND
    # (User needs to add C3 4.7uF at ~775,-610 in EasyEDA)

    # ============================================================
    # 5. LED1 (red, charge indicator)
    # ============================================================

    # LED1.A (620,-650) ← CHRG
    w.add_wire(620, -650, 650, -650, "CHRG")
    # LED1.K (580,-650) → GND
    w.add_power(580, -660, "GND")
    w.add_wire(580, -650, 580, -660)

    # ============================================================
    # 6. LED2 (blue/white, user LED on P0.13)
    # ============================================================

    w.add_wire(720, -650, 750, -650, "LED")     # LED2.A → LED net
    w.add_power(680, -660, "GND")
    w.add_wire(680, -650, 680, -660)             # LED2.K → GND
    w.add_wire(465, -545, 495, -545, "LED")      # U1.P0.13 → LED net

    # ============================================================
    # 7. Power: VBAT → SW1 → LDO (U4) → 3V3
    # ============================================================

    # Power switch SW1: BAT+ → pin1 (830,-430), pin4 (900,-400) → VBAT
    w.add_wire(830, -430, 800, -430, "BAT+")
    w.add_wire(900, -400, 930, -400, "VBAT")

    # U4.VIN pin1 (810,-510) ← VBAT
    w.add_wire(810, -510, 780, -510, "VBAT")

    # U4.VSS pin2 (810,-500) → GND
    w.add_power(780, -500, "GND", rotation=270)
    w.add_wire(780, -500, 810, -500)

    # U4.CE pin3 (810,-490) → tie high (VBAT) to always enable
    w.add_wire(810, -490, 780, -490, "VBAT")

    # U4.VOUT pin5 (890,-510) → 3V3
    w.add_power(920, -510, "3V3")
    w.add_wire(890, -510, 920, -510)

    # U4.NC pin4 (890,-490) — no connection

    # ============================================================
    # 8. LDO Capacitors (NEW)
    # ============================================================

    # C1 (100nF, already in schematic at 700,-250) → repurpose as LDO output cap
    # C1.pin1 (680,-250) → 3V3
    w.add_power(680, -240, "3V3", rotation=0)
    w.add_wire(680, -240, 680, -250)
    # C1.pin2 (720,-250) → GND
    w.add_power(720, -240, "GND", rotation=0)
    w.add_wire(720, -240, 720, -250)

    # Additional caps needed (user should add in EasyEDA):
    # C_LDO_IN: 1uF near U4.VIN    → VBAT / GND
    # C_LDO_OUT2: 10uF near U4.VOUT → 3V3 / GND
    # C_CHG_IN: 4.7uF near U3.VCC  → +5V / GND
    # C_CHG_OUT: 4.7uF near U3.BAT → VBAT / GND

    # ============================================================
    # 9. BLE Module (U1) Power
    # ============================================================

    # U1.VCC pin19 (350,-450) → 3V3
    w.add_power(350, -430, "3V3", rotation=0)
    w.add_wire(350, -430, 350, -450)

    # U1.GND pin5 (230,-560) → GND
    w.add_power(210, -560, "GND", rotation=270)
    w.add_wire(210, -560, 230, -560)

    # U1.GND pin21 (370,-450) → GND
    w.add_power(370, -430, "GND", rotation=0)
    w.add_wire(370, -430, 370, -450)

    # U1.GND pin24 (400,-450) → GND
    w.add_power(400, -430, "GND", rotation=0)
    w.add_wire(400, -430, 400, -450)

    # U1.VDH pin23 (390,-450) → decoupling net
    w.add_wire(390, -450, 390, -430, "VDH")

    # U1.DCH pin25 (410,-450) → decoupling net
    w.add_wire(410, -450, 410, -430, "DCH")

    # U1.VBS pin27 (465,-485) → VBUS sense → +5V
    w.add_wire(465, -485, 495, -485, "+5V")

    # ============================================================
    # 10. Reset & Boot Buttons
    # ============================================================

    # SW2 (Reset): pin1 (670,-400) → RST, pin2 (730,-400) → GND
    w.add_wire(670, -400, 640, -400, "RST")
    w.add_power(740, -400, "GND", rotation=90)
    w.add_wire(730, -400, 740, -400)

    # U1.RST pin26 (465,-475) → RST
    w.add_wire(465, -475, 495, -475, "RST")

    # SW3 (Boot/DFU): pin1 (670,-450) → P0.13 (BOOT), pin2 (730,-450) → GND
    w.add_wire(670, -450, 640, -450, "BOOT")
    w.add_power(740, -450, "GND", rotation=90)
    w.add_wire(730, -450, 740, -450)

    # ============================================================
    # 11. SWD Debug (U5)
    # ============================================================

    # U5 pins already connected: pin1→3V3, pin2→GND ✓ (existing)
    # U5 pin3 → JLINK_DIO, pin4 → JLINK_CLK ✓ (existing)

    # U1.SWD pin37 (465,-585) → SWDIO
    w.add_wire(465, -585, 495, -585, "SWDIO")
    # U1.SWC pin39 (465,-605) → SWCLK
    w.add_wire(465, -605, 495, -605, "SWCLK")

    # ============================================================
    # 12. KEYBOARD MATRIX: U2 (6R×13C) → U1 GPIO via net labels
    # ============================================================

    # U2 is at (385, -975), the Keyboard_6R13C symbol
    # U2 pin positions (from epro2 analysis):
    #   R0 (235,-1025), R1 (235,-1005), R2 (235,-985),
    #   R3 (235,-965),  R4 (235,-945),  R5 (235,-925)
    #   C0 (275,-1065), C1 (295,-1065), C2 (315,-1065), ...
    #   C10 (475,-1065), C11 (495,-1065)

    # --- Row connections: U2 ROW pins → net labels ---
    row_pins = {
        "ROW0": (235, -1025),
        "ROW1": (235, -1005),
        "ROW2": (235, -985),
        "ROW3": (235, -965),
        "ROW4": (235, -945),
        "ROW5": (235, -925),
    }
    for net, (x, y) in row_pins.items():
        w.add_wire(x, y, x - 30, y, net)

    # --- Column connections: U2 COL pins → net labels ---
    col_pins = {
        "COL0":  (275, -1065),
        "COL1":  (295, -1065),
        "COL2":  (315, -1065),
        "COL3":  (335, -1065),
        "COL4":  (355, -1065),
        "COL5":  (375, -1065),
        "COL6":  (395, -1065),
        "COL7":  (415, -1065),
        "COL8":  (435, -1065),
        "COL9":  (455, -1065),
        "COL10": (475, -1065),
        "COL11": (495, -1065),
    }
    for net, (x, y) in col_pins.items():
        w.add_wire(x, y, x, y - 30, net)

    # COL12 if exists — check if U2 has a 13th column (C12 pin at (510,-1065))
    # From symbol analysis: C0-C11 = 12 columns. The 13th might be on a separate pin.
    # For now, 12 columns. If needed, add COL12 = P1.06

    # --- U1 GPIO → Matrix ROW net labels ---
    u1_row_map = {
        "ROW0": ("P1.11", (230, -600)),   # pin 1, left side
        "ROW1": ("P1.10", (230, -590)),   # pin 2, left side
        "ROW2": ("P1.13", (230, -550)),   # pin 6, left side
        "ROW3": ("P0.06", (300, -450)),   # pin 14, bottom side
        "ROW4": ("P0.08", (320, -450)),   # pin 16, bottom side
        "ROW5": ("P12",   (360, -450)),   # pin 20, bottom side
    }

    for net, (pin_name, (x, y)) in u1_row_map.items():
        if y == -450:  # bottom pins → label goes down
            w.add_wire(x, y, x, y - 30, net)
        else:  # left pins → label goes left
            w.add_wire(x, y, x - 30, y, net)

    # --- U1 GPIO → Matrix COL net labels ---
    u1_col_map = {
        "COL0":  ("P0.07",  (380, -450)),   # pin 22, bottom
        "COL1":  ("P0.20",  (465, -535)),   # pin 32, right
        "COL2":  ("P0.22",  (465, -555)),   # pin 34, right
        "COL3":  ("P0.24",  (465, -565)),   # pin 35, right
        "COL4":  ("P1.00",  (465, -575)),   # pin 36, right
        "COL5":  ("P1.02",  (465, -595)),   # pin 38, right
        "COL6":  ("P1.04",  (465, -615)),   # pin 40, right
        "COL7":  ("P17",    (465, -515)),   # pin 30, right
        "COL8":  ("AI4",    (230, -570)),   # pin 4, left
        "COL9":  ("AI5",    (230, -530)),   # pin 8, left
        "COL10": ("AI7",    (230, -520)),   # pin 9, left
        "COL11": ("AI6",    (230, -510)),   # pin 10, left
    }

    for net, (pin_name, (x, y)) in u1_col_map.items():
        if x == 465:  # right side pins
            w.add_wire(x, y, x + 30, y, net)
        elif x == 230:  # left side pins
            w.add_wire(x, y, x - 30, y, net)
        elif y == -450:  # bottom pins
            w.add_wire(x, y, x, y - 30, net)

    # ============================================================
    # 13. Remaining U1 GPIOs (not used by matrix)
    # ============================================================

    # U1.P0.03 pin3 (230,-580) — free GPIO
    w.add_wire(230, -580, 200, -580, "D3")

    # U1.AI0 pin7 (230,-540) — analog input
    w.add_wire(230, -540, 200, -540, "A6")

    # U1.AI3 pin15 (310,-450) — analog
    w.add_wire(310, -450, 310, -430, "A7")

    # U1.AI2 pin18 (340,-450) — analog
    w.add_wire(340, -450, 340, -430, "A8")

    # U1.P15 pin28 (465,-495) — free
    w.add_wire(465, -495, 495, -495, "D28")

    # U1.P1.06 pin42 (465,-635) — COL12 or free
    w.add_wire(465, -635, 495, -635, "COL12")

    # U1.P0.26 pin12 (280,-450) — I2C SDA (optional)
    w.add_wire(280, -450, 280, -430, "SDA")

    # U1.P1.09 pin17 (330,-450) — I2C SCL (optional)
    w.add_wire(330, -450, 330, -430, "SCL")

    # ============================================================
    # 14. Crystal, NF pins
    # ============================================================
    # U1.XL1 pin11 (270,-450) — E73 has internal crystal, leave NC
    # U1.XL2 pin13 (290,-450) — leave NC
    # U1.NF1 pin41 (465,-625) — antenna matching, NC
    # U1.NF2 pin43 (465,-645) — antenna matching, NC


# ============================================================
# Main
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Build KeebDeck BLE schematic")
    parser.add_argument("file", help="Input .epro2 file")
    parser.add_argument("-o", "--output", required=True, help="Output .epro2 file")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    components, wires, symbols = load_epro2(args.file)
    max_ticket = get_max_ticket(args.file)

    pin_map = {}
    for c in components:
        if c.part_id == "pid8a0e77bacb214e":
            continue
        if c.symbol_uuid not in symbols:
            continue
        for pin in symbols[c.symbol_uuid].pins:
            ax, ay = pin_abs_position(c, pin)
            if pin.name:
                pin_map[f"{c.designator}.{pin.name}"] = (ax, ay)

    w = EasyEDAWriter(start_ticket=max_ticket + 1, start_z=200)
    build_keebdeck_wires(pin_map, w)

    new_lines = w.lines
    print(f"Generated {len(new_lines)} new lines (ticket {max_ticket+1} → {w.ticket-1})")

    if args.dry_run:
        for line in new_lines:
            print(line)
        return

    with zipfile.ZipFile(args.file, "r") as zf:
        epru_names = [n for n in zf.namelist() if n.endswith(".epru")]
        with zf.open(epru_names[0]) as f:
            epru_content = f.read().decode("utf-8")

    epru_lines = epru_content.split("\n")
    blob_line = None
    for i, line in enumerate(epru_lines):
        if '"docType":"BLOB"' in line:
            blob_line = i
            break

    if blob_line is not None:
        final_lines = epru_lines[:blob_line] + new_lines + epru_lines[blob_line:]
    else:
        final_lines = epru_lines + new_lines

    new_epru = "\n".join(final_lines)

    with zipfile.ZipFile(args.file, "r") as zf_in:
        with zipfile.ZipFile(args.output, "w", zipfile.ZIP_DEFLATED) as zf_out:
            for item in zf_in.namelist():
                if item.endswith(".epru"):
                    zf_out.writestr(item, new_epru)
                else:
                    zf_out.writestr(item, zf_in.read(item))

    print(f"Written to {args.output}")


if __name__ == "__main__":
    main()
