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

import struct
from collections import namedtuple
from collections.abc import Sequence
from enum import Enum, EnumMeta, unique

from .enums import (
    BumpAndWheelDrops, WheelOvercurrents, Buttons,
    ChargingState, ChargingSourcesAvailable, OIMode,
    LightBumper, Statis
)

# pylint: disable=bad-whitespace

@unique
class Sensor(Enum):
    """
    Enumeration of possible sensors that can be read from the Roomba. The value of each is the
    packet-id Each value also has the following attributes:
      * `packet_id` - same as the value
      * `dataypte` - the information about how to read the data, a format string, an `Enum` class,
        or a `namedtuple` type
      * `size` - number of bytes to be read for this sensor
      * `struct_format` - the `struct.unpack` format string to be used for this sensor
    A few useful methods are available as well.
    """
    BUMPS_AND_WHEEL_DROPS       = ( 7, BumpAndWheelDrops)
    WALL                        = ( 8, '?') # deprecated, use LIGHT_BUMPER instead
    CLIFF_LEFT                  = ( 9, '?')
    CLIFF_FRONT_LEFT            = (10, '?')
    CLIFF_FRONT_RIGHT           = (11, '?')
    CLIFF_RIGHT                 = (12, '?')
    VIRTUAL_WALL                = (13, '?')
    WHEEL_OVERCURRENTS          = (14, WheelOvercurrents)
    DIRT_DETECT                 = (15, 'B')
    _UNUSED_1                   = (16, 'x') # only used with groups
    INFARED_CHARACTER_OMNI      = (17, 'B')
    INFARED_CHARACTER_LEFT      = (52, 'B')
    INFARED_CHARACTER_RIGHT     = (53, 'B')
    BUTTONS                     = (18, Buttons)
    DISTANCE                    = (19, 'h')
    ANGLE                       = (20, 'h')
    CHARGING_STATE              = (21, ChargingState)
    VOLTAGE                     = (22, 'H')
    CURRENT                     = (23, 'h')
    TEMPERATURE                 = (24, 'b')
    BATTERY_CHARGE              = (25, 'H')
    BATTERY_CAPACITY            = (26, 'H')
    WALL_SIGNAL                 = (27, 'H') # deprecated, use LIGHT_BUMP_RIGHT_SIGNAL instead
    CLIFF_SIGNAL_LEFT           = (28, 'H')
    CLIFF_SIGNAL_FRONT_LEFT     = (29, 'H')
    CLIFF_SIGNAL_FRONT_RIGHT    = (30, 'H')
    CLIFF_SIGNAL_RIGHT          = (31, 'H')
    _UNUSED_2                   = (32, 'x')  # only used with groups
    _UNUSED_3                   = (33, 'xx') # only used with groups
    CHARGING_SOURCES_AVAIL      = (34, ChargingSourcesAvailable)
    OI_MODE                     = (35, OIMode)
    SONG_NUMBER                 = (36, 'B')
    SONG_PLAYING                = (37, '?')
    NUM_STREAM_PACKETS          = (38, 'B')
    REQ_VELOCITY                = (39, 'h')
    REQ_RADIUS                  = (40, 'h')
    REQ_RIGHT_VELOCITY          = (41, 'h')
    REQ_LEFT_VELOCITY           = (42, 'h')
    LEFT_ENCODER_COUNTS         = (43, 'h')
    RIGHT_ENCODER_COUNTS        = (44, 'h')
    LIGHT_BUMPER                = (45, LightBumper)
    LIGHT_BUMP_LEFT_SIGNAL      = (46, 'H')
    LIGHT_BUMP_FRONT_LEFT_SIGNAL   = (47, 'H')
    LIGHT_BUMP_CENTER_LEFT_SIGNAL  = (48, 'H')
    LIGHT_BUMP_CENTER_RIGHT_SIGNAL = (49, 'H')
    LIGHT_BUMP_FRONT_RIGHT_SIGNAL  = (50, 'H')
    LIGHT_BUMP_RIGHT_SIGNAL     = (51, 'H')
    LEFT_MOTOR_CURRENT          = (54, 'h')
    RIGHT_MOTOR_CURRENT         = (55, 'h')
    MAIN_BRUSH_MOTOR_CURRENT    = (56, 'h')
    SIDE_BRUSH_MOTOR_CURRENT    = (57, 'h')
    STATIS                      = (58, Statis)

    # These become named tuples later on
    GROUP_7_26  = (  0, list(range( 7, 27)))
    GROUP_7_16  = (  1, list(range( 7, 17)))
    GROUP_17_20 = (  2, list(range(17, 21)))
    GROUP_21_26 = (  3, list(range(21, 27)))
    GROUP_27_34 = (  4, list(range(27, 35)))
    GROUP_35_42 = (  5, list(range(35, 43)))
    GROUP_7_42  = (  6, list(range( 7, 43)))
    ALL_SENSORS = (100, list(range( 7, 59))) # GROUP_7_58
    GROUP_43_58 = (101, list(range(43, 59)))
    GROUP_46_51 = (106, list(range(46, 52)))
    GROUP_54_58 = (107, list(range(54, 59)))

    def __new__(cls, packet_id, datatype):
        obj = object.__new__(cls)
        obj._value_ = packet_id # pylint: disable=protected-access
        obj.packet_id = packet_id
        obj.datatype = datatype
        if isinstance(obj.datatype, str):
            obj.size = struct.calcsize(obj.datatype)
            obj.struct_format = '>' + obj.datatype
        elif isinstance(obj.datatype, EnumMeta):
            obj.size = 1 # single byte
            obj.struct_format = '>B'
        # we cannot do the list-based ones until later...
        #elif isinstance(obj.datatype, list): ...
        return obj

    def __int__(self):
        return ord(self.value)

    def parse(self, raw):
        """
        Convert a raw `byte` string of data for this sensor to the appropriate value, either an
        `int`, `bool`, one of the `IntEnum` or `IntFlag` objects from `enums`, or a `namedtuple` of
        values for multiple values.
        """
        return self.convert(struct.unpack(self.struct_format, raw))

    def convert(self, data):
        """
        Convert a sequence of values from the output of `struct.unpack()` or similar to the
        appropriate value. This is the same as `parse` except the argument is a sequence and not a
        `byte` string.
        """
        if isinstance(self.datatype, str):
            if isinstance(data, Sequence) and len(data) == 1:
                data = data[0]
            return data
        if isinstance(self.datatype, EnumMeta):
            if isinstance(data, Sequence):
                if len(data) != 1:
                    raise ValueError()
                data = data[0]
            return self.datatype(data)
        if issubclass(self.datatype, tuple):
            # pylint: disable=no-member
            return self.datatype._make(Sensor.convert_list(self.sensors, data))
        raise TypeError()

    @staticmethod
    def convert_list(sensors, data):
        """
        Take a list of sensors and a list of data values and call each sensor's `convert()` method
        with the correct data. Any sensor that is just filler (i.e. has the format 'x') then it
        will be skipped.
        """
        return [s.convert(x) for s, x in
                zip((s for s in sensors if 'x' not in s.struct_format), data)]

    @staticmethod
    def summarize_group(sensors, name='Group'):
        """
        Gets a summary of the data for a group of sensors. This returns the `namedtuple` type that
        should be used to wrap the resulting data, the total size in bytes of all of the sensors
        and the format string to give to `struct.unpack()` for parsing the data.

        The `namedtuple` will default to having the class name 'Group'. The second argument can
        change this.
        """
        group = namedtuple(name, [s.name for s in sensors if s.name[0] != '_'])
        size = sum(s.size for s in sensors)
        frmt = ('>' + ''.join(s.struct_format.strip('>') for s in sensors))
        return group, size, frmt


# Calculate the size and struct format of the list-based sensors
for sensor in Sensor.__members__.values():
    if isinstance(sensor.datatype, list):
        sensor.sensors = [Sensor(i) for i in sensor.datatype] # pylint: disable=no-value-for-parameter
        sensor.datatype, sensor.size, sensor.struct_format = \
            Sensor.summarize_group(sensor.sensors,
                                   ''.join(word.capitalize() for word in sensor.name.split('_')))
del sensor # pylint: disable=undefined-loop-variable
