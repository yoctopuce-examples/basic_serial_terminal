#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import sys
import time
import colorama
from optparse import OptionParser
from yoctopuce.yocto_api import *
from yoctopuce.yocto_serialport import *


def getch():
    if platform.system() == 'Windows':
        return msvcrt.getch()
    else:
        return sys.stdin.read(1)


def kbhit():
    if platform.system() == 'Windows':
        return msvcrt.kbhit()
    else:
        dr, dw, de = select.select([sys.stdin], [], [], 0)
        return len(dr) != 0


def handle_escpae_sequence(raw):
    """

    @type raw: str
    """
    clean = ''
    next_raw = ''
    pos = 0
    raw_len = len(raw)
    while pos < raw_len:
        cc = raw[pos]
        b = ord(cc)
        if (32 <= b < 127) or b in (9, 10):  # printable, \t, \n
            clean += cc
        elif b == 27:  # remove coded sequences
            esc_pos = pos + 1
            while esc_pos < raw_len and raw[esc_pos].lower() not in 'abcdhsujkm':
                esc_pos += 1
            if esc_pos == raw_len:
                next_raw = raw[pos:]
                break
            else:
                esc_sequence = raw[pos: esc_pos + 1]
                if esc_sequence[1:] == '[J':
                    clean += esc_sequence
                else:
                    clean += esc_sequence
                pos = esc_pos
        elif b == 8 or (b == 13 and clean and clean[-1] == ' '):  # backspace or EOL spacing
            if clean:
                clean = clean[:-1]
            else:
                clean += "\b"
        pos += 1

    return clean, next_raw


unhandled_escape_sequence = ''


def new_data_cb(serial, value):
    """

    @type value: str
    @type serial: YSerialPort
    """
    global unhandled_escape_sequence
    read_str = serial.readStr(65535)
    if read_str == '':
        return
    out_str, unhandled_escape_sequence = handle_escpae_sequence(unhandled_escape_sequence + read_str)
    sys.stdout.write(out_str)


parser = OptionParser()
parser.add_option("-d", "--debug", action="store_true",
                  help="Enable debug mode.",
                  default=False)
parser.add_option("-r", "--remoteAddr", dest="hub_url",
                  help="Uses remote IP devices (or VirtalHub), instead of local USB.",
                  default='usb')
parser.add_option("-s", "--serial", dest="serial",
                  help="Use the module that as this serial number instead of using the firt one.",
                  default='')
(opt, args) = parser.parse_args()

hub_url = opt.hub_url

errmsg = YRefParam()
if YAPI.RegisterHub(hub_url, errmsg) != YAPI.SUCCESS:
    sys.exit("init error: " + errmsg.value)

if opt.serial != '':
    serialPort = YSerialPort.FindSerialPort(opt.serial + ".serialPort")
    if not serialPort.isOnline():
        sys.exit("No Yocto-Serial " + opt.serial + " is not found on " + hub_url)
else:
    serialPort = YSerialPort.FirstSerialPort()
    if serialPort is None:
        sys.exit("No Yocto-Serial found on " + hub_url)

serialPort.set_voltageLevel(YSerialPort.VOLTAGELEVEL_TTL3V)
serialPort.set_serialMode("57600,8N1")
serialPort.set_protocol("Char")
serialPort.reset()
serialPort.registerValueCallback(new_data_cb)
sys.stdout.write(serialPort.readStr(65535))
print("Connected.")

# Setup terminal settings
colorama.init()
fd = None
old_settings = None
if platform.system() == 'Windows':
    import msvcrt
else:
    import tty
    import termios
    import select

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    new_settings = termios.tcgetattr(fd)
    new_settings[3] = (new_settings[3] & ~termios.ICANON & ~termios.ECHO)
    termios.tcsetattr(fd, termios.TCSAFLUSH, new_settings)

ctr_c_pressed = False
while True:
    try:
        if kbhit():
            c = getch()
            ctr_c_pressed = False
            keycode = ord(c)
            if keycode == 224:
                c = getch()
                keycode = ord(c)
                if keycode == 72:
                    serialPort.writeStr(colorama.ansi.Cursor.UP())
                elif keycode == 77:
                    serialPort.writeStr(colorama.ansi.Cursor.FORWARD())
                elif keycode == 80:
                    serialPort.writeStr(colorama.ansi.Cursor.DOWN())
                elif keycode == 75:
                    serialPort.writeStr(colorama.ansi.Cursor.BACK())
                else:
                    print("Keyco (%X %c)" % (keycode, c))
            else:
                serialPort.writeByte(keycode)
        YAPI.HandleEvents()
        YAPI.UpdateDeviceList()

    except KeyboardInterrupt:
        if ctr_c_pressed:
            print("Exit serial_term")
            break
        else:
            print("\nPress a second time Ctr-C to exit serial_term")
            ctr_c_pressed = True

YAPI.FreeAPI()
# restore terminal settinsg
if platform.system() != 'Windows':
    termios.tcsetattr(fd, termios.TCSAFLUSH, old_settings)
