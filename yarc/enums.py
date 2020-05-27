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

try:
    from enum import IntFlag, IntEnum, unique
except ImportError:
    from aenum import IntFlag, IntEnum, unique

__all__ = [
    'Days', 'Day', 'Drive',
    'BumpAndWheelDrops', 'WheelOvercurrents', 'Buttons',
    'ChargingState', 'ChargingSourcesAvailable', 'OIMode',
    'LightBumper', 'Statis'
]

# pylint: disable=bad-whitespace

##### Command Enums/Flags #####

@unique
class Days(IntFlag):
    """Bit-flags for days of the week."""
    NONE = 0
    SUNDAY    = 0x01
    MONDAY    = 0x02
    TUESDAY   = 0x04
    WEDNESDAY = 0x08
    THURSDAY  = 0x10
    FRIDAY    = 0x20
    SATURDAY  = 0x40

@unique
class Day(IntEnum):
    """Enumeration for days of the week."""
    SUNDAY    = 0
    MONDAY    = 1
    TUESDAY   = 2
    WEDNESDAY = 3
    THURSDAY  = 4
    FRIDAY    = 5
    SATURDAY  = 6

@unique
class Drive(IntEnum):
    """Special value for the Roomba drive operation."""
    STRAIGHT     = -32768 #0x8000
    STRAIGHT_ALT = 0x7FFF
    TURN_CW      = -1
    TURN_CCW     = 1


##### Sensor Value Enums/Flags #####

@unique
class BumpAndWheelDrops(IntFlag):
    """Bit-flags for which bump and/or wheel drop sensors are triggered."""
    NONE = 0
    BUMP_RIGHT       = 0x01
    BUMP_LEFT        = 0x02
    WHEEL_DROP_RIGHT = 0x04
    WHEEL_DROP_LEFT  = 0x08

@unique
class WheelOvercurrents(IntFlag):
    """Bit-flags for which motors are triggering their overcurrent sensors."""
    NONE = 0
    SIDE_BRUSH  = 0x01
    _VACUUM     = 0x02 # reserved, not available
    MAIN_BRUSH  = 0x04
    RIGHT_WHEEL = 0x08
    LEFT_WHEEL  = 0x10

@unique
class Buttons(IntFlag):
    """
    Bit-flags for which buttons are currently pressed.

    The day, hour, minute, clock, and scheduling buttons only exist on some models. Other models
    will always give 0.
    """
    NONE = 0
    CLEAN    = 0x01
    SPOT     = 0x02
    DOCK     = 0x04
    MINUTE   = 0x08
    HOUR     = 0x10
    DAY      = 0x20
    SCHEDULE = 0x40
    CLOCK    = 0x80

@unique
class ChargingState(IntEnum):
    """Enumeration of the current charging state."""
    NOT_CHARGING = 0
    RCONDITIONING_CHARING = 1
    FULL_CHARGING = 2
    TRICKLE_CHARGING = 3
    WAITING = 4
    CHARGING_FAULT_CONDITION = 5

@unique
class ChargingSourcesAvailable(IntFlag):
    """Bit-flags for which charging sources are available."""
    NONE = 0
    INTERNEL_CHARGER = 0x01
    HOME_BASE = 0x02

@unique
class OIMode(IntEnum):
    """Enumeration of the current OI mode."""
    OFF = 0 # can not actually be reported
    PASSIVE = 1
    SAFE = 2
    FULL = 3

@unique
class LightBumper(IntFlag):
    """Bit-flags for which light bumper sensors are currently triggered."""
    NONE = 0
    LIGHT_BUMPER_LEFT         = 0x01
    LIGHT_BUMPER_FRONT_LEFT   = 0x02
    LIGHT_BUMPER_CENTER_LEFT  = 0x04
    LIGHT_BUMPER_CENTER_RIGHT = 0x08
    LIGHT_BUMPER_FRONT_RIGHT  = 0x10
    LIGHT_BUMPER_RIGHT        = 0x20

@unique
class Statis(IntFlag):
    """
    The statis caster sensor bit-flags. STATIS_TOGGLING is set when the robot is making forward
    progress and 0 when it is not. It always returns 0 when the robot is turning, driving backward,
    or not driving. If the stasis wheel is too dirty to be read, STATIS_DISABLED is set. If this
    happens, remove the stasis wheel and clean it with a damp cloth, then dry it thoroughly before
    reinstalling the wheel.
    """
    NONE = 0
    STATIS_TOGGLING = 0x01
    STATIS_DISABLED = 0x02
