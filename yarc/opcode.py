"""
This file is part of YARC (https://github.com/coderforlife/yarc).
Copyright (c) 2019 Jeffrey Bush.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, version 3.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

from enum import Enum, unique

# pylint: disable=bad-whitespace

@unique
class Opcode(bytes, Enum):
    """
    Enumeration of Roomba Opcodes. These are treated as `bytes` so that they can be easily sent to
    the Roomba over a serial connection. The values can also be easily converted to ints.
    """
    # Getting Started Commands
    START        = b'\x80'
    RESET        = b'\x07'
    STOP         = b'\xAD'
    BAUD         = b'\x81' # B
    # Mode Commands
    SAFE         = b'\x83'
    SAFE_ALT     = b'\x82'
    FULL         = b'\x84'
    # Cleaning Commands
    CLEAN        = b'\x87'
    MAX          = b'\x88'
    SPOT         = b'\x86'
    SEEK_DOCK    = b'\x8F'
    POWER        = b'\x85'
    SCHEDULE     = b'\xA7' # B*15
    SET_DAY_TIME = b'\xA8' # B*3
    # Actuator Commands
    DRIVE        = b'\x89' # h*2
    DRIVE_DIRECT = b'\x91' # h*2
    DRIVE_PWM    = b'\x92' # h*2
    MOTORS       = b'\x8A' # B
    MOTORS_PWM   = b'\x90' # b*3
    LEDS         = b'\x8B' # B*3
    LEDS_SCHEDULING  = b'\xA2' # B*2
    LEDS_DIGIT_RAW   = b'\xA3' # B*4
    LEDS_DIGIT_ASCII = b'\xA4' # B*4
    BUTTONS      = b'\xA5' # B*4
    SONG         = b'\x8C' # B + B + B*N
    PLAY         = b'\x8D' # B
    # Input Commands
    SENSORS      = b'\x8E' # B
    QUERY_LIST   = b'\x95' # B + B*N
    STREAM       = b'\x94' # B + B*N
    STREAM_PAUSE_RESUME = b'\x96' # B
    def __bytes__(self):
        return self.value
    def __int__(self):
        return ord(self.value)
