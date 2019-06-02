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
import time
import serial

from .enums import Days, Day, Drive, Buttons
from .opcode import Opcode
from .sensor import Sensor

def clamp(val, low, high):
    """Clamps a value between the low and high value."""
    return min(max(val, low), high)
def bitflags(*args):
    """Take a sequence of bool values and return an integer with those bits set."""
    cur, val = 1, 0
    for arg in args:
        if arg:
            val |= cur
        cur <<= 1
    return val
def make_sensor_property(sensor):
    """Make a property for a sensor with the given name"""
    return property(lambda self: self.sensor(sensor))

class Roomba: # pylint: disable=too-many-public-methods
    """A connection to a Roomba over a serial port."""

    # The following functions are untested:
	#  * motors and motors_pwm - my testing Create2 has none of these motors installed
	#  * digit_leds_raw - isn't supported by my testing Create2
	#  * baud - default is fastest, lets just keep it that way
    # The following functions are minimally tested:
	#  * schedule
    #  * set_day_time

    def __init__(self, port, baudrate=115200, timeout=0.045, brc=None):
        """
        Connect to the Roomba on the given port (such as /dev/ttyUSB0 on Linux or COM3 on Windows).
        This defaults to the default baudrate of Roombas (which can be changed howeevr) and has a
        timeout of 45ms which is equivilent to 3 data cycles on the Roomba (it does things in 15ms
        cycles). For some circumstances alternative timeouts are used and cannot be adjusted.

        The `wake()` method requires pulsing the BRC pin on the Roomba. For the offical Create 2
        cables (except older ones) this pin is connected to the RTS pin of the serial port. The
        default behavior is to pulse this pin.

        In other circumstances a separate signal line is used for the BRC pin. In these cases
        you can provide a `brc` function to this constructor. This function takes two arguments.
        The first will be a reference to the Roomba and the second will be False or True to cause
        the pin to be turned off and on.
        """
        if baudrate not in [19200, 115200]:
            raise ValueError('baudrate')
        self.__default_baudrate = baudrate
        self.serial = serial.Serial(port, baudrate=baudrate, timeout=timeout)
        if brc is not None:
            self._brc = brc
    def __del__(self):
        self.close()
    def close(self):
        """
        Stop the Roomba and close the serial connection. After this method is called this object is
        not usable. This will block for 60 ms.
        """
        if not self.serial.is_open:
            return
        self.power() # causes all LEDs and motors to stop and the Roomba returns to passive mode
        time.sleep(0.03)
        self.wake()
        self.stop()
        self.serial.close()
    def read_avail(self):
        """
        Read all available bytes from the serial connection's buffer. The Roomba will peroidically
        send messages about the firmware or battery status and this function can be used to read
        it. Note that any sensor attribute or method will clear this buffer automatically.
        """
        return self.serial.read(self.serial.in_waiting)

    # Getting Started Commands
    def start(self):
        """
        This command starts the OI. You must always send the Start command before sending any other
        commands to the OI.

        Available: all modes
        Changes mode to: passive, beeps if coming from "off" mode.
        """
        self.serial.write(Opcode.START)
    def reset(self, welcome_msg_bytes=6):
        """
        This command resets the robot, as if you had removed and reinserted the battery.
        Returns a string of information. The device baud rate will be reset along with exiting
        any useful mode.

        This function will likely block for 3-5 seconds. Data that the Roomba produces after
        booting up will be returned. This may just be the word 'Roomba'. Adjusting the argument
        welcome_msg_bytes to a higher number will attempt to read at least that many bytes from the
        welcome message. It seems as though if you want to get the firmware version you will need
        about 160 bytes. Going to 450 is the most you will likely ever want to get. Additional data
        can be obtained with the `read_avail()` method as well without blocking in this method. Any
        additional data will be cleared if any sensor is read from.

        Available: always
        Changes mode to: off
        """
        self.serial.reset_input_buffer()
        self.serial.write(Opcode.RESET)
        self.serial.reset_input_buffer()
        self.serial.baudrate = self.__default_baudrate

        # pylint: disable=line-too-long

        # 15 ms - reports it is being reset     b'Soft reset!\n'
        # 1 sec - actually finished going down  b'\xfe'
        # 3 sec - back up and prints welcome    b'Roomba by iRobot!\r\nstm32\r\n2015-12-18-1607-L   \r\nbattery-current-zero 254\r\n'
        # 4 sec - reports firmware version      b'\r\n2015-12-18-1607-L   \r\nr3-robot/tags/release-stm32-3.7.1:6174 CLEAN\r\n\r\nbootloader id: 3115 C200 0033 5860 \r\nassembly: 3.5-lite\r\nrevision: 8\r\nflash version: 10\r\nflash info crc passed: 1\r\n\r\nbattery-current-zero 252\r\nestimate-battery-level-from-voltage 2697 mAH 17734 mV\r\nstart-charge: 2015-12-18-1607-L   \r\nDetermining battery type.\r\n'
        # More messages show up at 5 sec, 6.4 sec, and other times
        # Starting at 5 sec a battery message is shown once per second until the bot is started

        orig_timeout = self.serial.timeout
        try:
            self.serial.timeout = 0.03
            data = self.serial.read(12)
            if data != b'Soft reset!\n':
                raise ValueError()
            self.serial.timeout = 1.5
            data = self.serial.read(1)
            if data != b'\xfe':
                raise ValueError()
            self.serial.timeout = 5
            data = self.serial.read(welcome_msg_bytes)
            self.serial.timeout = 0
            data += self.serial.read(self.serial.in_waiting)
        finally:
            self.serial.timeout = orig_timeout
        return data
    def stop(self):
        """
        This command stops the OI. All streams will stop and the robot will no longer respond to
        commands. Use this command when you are finished working with the robot.

        Available: passive, safe, full
        Changes mode to: off, beeps
        """
        self.serial.write(Opcode.STOP)
    def wake(self, sleep_time=0.015):
        """
        Wake up robot. This is useful in at least two different cases:
         * After being taken off of the charger this needs to be called once to use the Roomb again
         * After `power()` is called
         * Called at least once per 5 min while in passive mode to keep the Rooma awake

        This blocks for twice the sleep_time which defaults to 0.015 seconds. A longer value may be
        needed to wake it in certain circumstances.

        The `Roomba` constructor takes a `brc` function that is used with this function.
        """
        self._brc(False)
        time.sleep(sleep_time)
        self._brc(True)
        time.sleep(sleep_time)
    def _brc(self, state): # pylint: disable=method-hidden
        """Default BRC state change function uses the serial port's RTS and DTR pins."""
        self.serial.rts = state
        self.serial.dtr = state

    @property
    def baud(self):
        """Get the current serial port baudrate."""
        return self.serial.baudrate
    @baud.setter
    def baud(self, baudrate):
        """
        This command sets the baud rate in bits per second (bps) at which OI commands and data are
        sent. It persists until Roomba is power cycled by pressing the power button or removing the
        battery, or when the battery voltage falls below the minimum required for processor
        operation.

        This function blocks for at least 100ms.
        """
        baud_codes = {300:b'\x00', 600:b'\x01', 1200:b'\x02', 2400:b'\x03', 4800:b'\x04',
                      9600:b'\x05', 14400:b'\x06', 19200:b'\x07', 28800:b'\x08', 38400:b'\x09',
                      57600:b'\x0A', 115200:b'\x0B'}
        self.serial.write(Opcode.BAUD + baud_codes[baudrate])
        time.sleep(0.1) # required
        self.serial.baudrate = baudrate

    # Mode Commands
    def safe(self):
        """
        This command puts the OI into Safe mode, enabling user control of Roomba. It turns off all
        LEDs. If a safety condition occurs (see above) Roomba reverts automatically to Passive mode.

        Available: passive, safe, full
        Changes mode to: safe
        """
        self.serial.write(Opcode.SAFE)
    def full(self):
        """
        This command gives you complete control over Roomba by putting the OI into Full mode, and
        turning off the cliff, wheel-drop and internal charger safety features. That is, in Full
        mode, Roomba executes any command that you send it, even if the internal charger is plugged
        in, or command triggers a cliff or wheel drop condition.

        Available: passive, safe, full
        Changes mode to: full
        """
        self.serial.write(Opcode.FULL)

    # Cleaning commands
    def clean(self):
        """
        This command starts the default cleaning mode. This is the same as pressing Roomba's Clean
        button, and will pause a cleaning cycle if one is already in progress.

        Available: passive, safe, full
        Changes mode to: passive
        """
        self.serial.write(Opcode.CLEAN)
    def max(self):
        """
        This command starts the Max cleaning mode, which will clean until the battery is dead. This
        command will pause a cleaning cycle if one is already in progress.

        Available: passive, safe, full
        Changes mode to: passive
        """
        self.serial.write(Opcode.MAX)
    def spot(self):
        """
        This command starts the Spot cleaning mode. This is the same as pressing Roomba's Spot
        button, and will pause a cleaning cycle if one is already in progress.

        Available: passive, safe, full
        Changes mode to: passive
        """
        self.serial.write(Opcode.SPOT)
    def seek_dock(self):
        """
        This command directs Roomba to drive onto the dock the next time it encounters the docking
        beams. This is the same as pressing Roomba's Dock button, and will pause a cleaning cycle
        if one is already in progress.

        Available: passive, safe, full
        Changes mode to: passive
        """
        self.serial.write(Opcode.SEEK_DOCK)
    def power(self):
        """
        This command powers down Roomba. The OI can be in Passive, Safe, or Full mode to accept
        this command.

        Available: passive, safe, full
        Changes mode to: passive
        """
        self.serial.write(Opcode.POWER)
    def schedule(self, sun=None, mon=None, tue=None, wed=None, thu=None, fri=None, sat=None): # pylint: disable=too-many-arguments
        """
        This command sends Roomba a new schedule. To disable scheduled cleaning give no arguments.

        Each argument is a day of the week. You must pass a tuple of hour (0-23) and minute (0-59)
        for the time on that day to run the Roomba. Any day not give or given as None will not be
        scheduled.

        Available: passive, safe, full
        """
        days = Days.NONE
        data = b''
        for time_, day in zip((sun, mon, tue, wed, thu, fri, sat),
                              (Days.SUNDAY, Days.MONDAY, Days.TUESDAY, Days.WEDNESDAY,
                               Days.THURSDAY, Days.FRIDAY, Days.SATURDAY)):
            if time_ is not None:
                days |= day
                hour, minute = time_
                if hour < 0 or hour > 23:
                    raise ValueError('hour')
                if minute < 0 or minute > 59:
                    raise ValueError('minute')
                data += struct.pack('BB', hour, minute)
            else:
                data += b'\x00\x00'
        data = struct.pack('B', int(days)) + data
        self.serial.write(Opcode.SCHEDULE + data)
    def set_day_time(self, day_of_week, hour, minute):
        """
        This command sets Roomba's clock.

        The day of the week is a Day value or a value from 0 to 6 for Sunday through Saturday, hour
        is 0 to 23, and minute is 0 to 59.

        Available: passive, safe, full
        """
        day_of_week = Day(day_of_week)
        if hour < 0 or hour > 23:
            raise ValueError('hour')
        if minute < 0 or minute > 59:
            raise ValueError('minute')
        data = struct.pack('BBB', day_of_week, hour, minute)
        self.serial.write(Opcode.SET_DAY_TIME + data)

    # Actuator Commands
    # These are all available in safe and full modes
    # Buttons and songs are also available in passive mode
    def drive(self, velocity, radius=None):
        """
        This command controls Roomba's drive wheels. The first parameter specifies the average
        velocity of the drive wheels in millimeters per second (mm/s), with. The next paramater
        specifies the radius in millimeters at which Roomba will turn. The longer radii make Roomba
        drive straighter, while the shorter radii make Roomba turn more. The radius is measured
        from the center of the turning circle to the center of Roomba. A Drive command with a
        positive velocity and a positive radius makes Roomba drive forward while turning toward the
        left. A negative radius makes Roomba turn toward the right. If no radius is specified (or
        is None) the Roomba drives straight. If the radius is -1 it will turn in place clockwise
        and if it is 1 it will turn in place counter-clockwise. A negative velocity makes Roomba
        drive backward.

        NOTE:
        Internal and environmental restrictions may prevent Roomba from accurately carrying out
        some drive commands. For example, it may not be possible for Roomba to drive at full speed
        in an arc with a large radius of curvature.

        Roomba's speed controller can only control the velocity of the wheels in steps of about
        28.5 mm/s.

        Velocity is clamped between -500 and 500 mm/s.
        Radius is clamped between -2000 and 2000 mm.
        """
        velocity = clamp(velocity, -500, 500)
        radius = Drive.STRAIGHT if radius is None else clamp(radius, -2000, 2000)
        data = struct.pack('>hh', velocity, radius)
        self.serial.write(Opcode.DRIVE + data)
    def drive_direct(self, r_vel, l_vel):
        """
        This command lets you control the forward and backward motion of Roomba's drive wheels
        independently. The first parameter specifies the velocity of the right wheel in millimeters
        per second (mm/s). The paramater specifies the velocity of the left wheel. A positive
        velocity makes that wheel drive forward, while a negative velocity makes it drive backward.

        NOTE: Roomba's speed controller can only control the velocity of the wheels in steps of
        about 28.5 mm/s.

        Velocities are clamped between -500 and 500 mm/s.
        """
        data = struct.pack('>hh', clamp(r_vel, -500, 500), clamp(l_vel, -500, 500))
        self.serial.write(Opcode.DRIVE_DIRECT + data)
    def drive_pwm(self, r_pwm, l_pwm):
        """
        This command lets you control the raw forward and backward motion of Roomba's drive wheels
        independently. The first parameter specifies the PWM of the right wheel. The next parameter
        specifies the PWM of the left wheel. A positive PWM makes that wheel drive forward, while a
        negative PWM makes it drive backward.

        PWMs are clamped between -255 and 255 mm/s.
        """
        data = struct.pack('>hh', clamp(r_pwm, -255, 255), clamp(l_pwm, -255, 255))
        self.serial.write(Opcode.DRIVE_PWM + data)

    # Convience functions
    def drive_stop(self):
        """Stops both drive wheels."""
        self.drive_direct(0, 0)
    def drive_rotate(self, velocity):
        """Rotates in place counter clockwise (negative velocity will go clockwise)."""
        self.drive(velocity, Drive.TURN_CCW)
    def turn_angle(self, angle, velocity=100):
        """
        Attempts to rotate a specific angle (in degrees) in place overall at a given velocity (the
        default is 100 mm/s). Returns the estimated angle in degrees turned.
        """
        # pylint: disable=no-member
        _ = self.angle # clear the angle counter
        turned = 0
        if angle > 0:
            self.drive_direct(velocity, -velocity)
            while turned < angle:
                turned += self.angle
        else:
            self.drive_direct(-velocity, velocity)
            while turned > angle:
                turned += self.angle
        self.drive_direct(0, 0)
        return turned
    def drive_distance(self, distance, velocity=100):
        """
        Attempts to drive a specific distance (in mm) at a given velocity (the default is 100
        mm/s). Returns the estimated distance travelled in mm.
        """
        # pylint: disable=no-member
        _ = self.distance # clear the distance counter
        traveled = 0
        if distance > 0:
            self.drive_direct(velocity, velocity)
            while traveled < distance:
                traveled += self.distance
        else:
            self.drive_direct(-velocity, -velocity)
            while traveled > distance:
                traveled += self.distance
        self.drive_direct(0, 0)
        return traveled

    def motors(self, # pylint: disable=too-many-arguments
               side_brush=False, vacuum=False, main_brush=False,
               side_brush_cw=False, main_brush_outward=False):
        """
        This command lets you control the forward and backward motion of Roomba's main brush, side
        brush, and vacuum independently. Motor velocity cannot be controlled with this command, all
        motors will run at maximum speed when enabled. The main brush and side brush can be run in
        either direction. The vacuum only runs forward.
        """
        data = struct.pack('B', bitflags(side_brush, vacuum, main_brush,
                                         side_brush_cw, main_brush_outward))
        self.serial.write(Opcode.MOTORS + data)
    def motors_pwm(self, main_brush=0, side_brush=0, vacuum=0):
        """
        This command lets you control the speed of Roomba's main brush, side brush, and vacuum
        independently. With each data byte, you specify the duty cycle for the low side driver
        (max 128). For example, if you want to control a motor with 25% of battery voltage, choose
        a duty cycle of 128 * 25% = 32. The main brush and side brush can be run in either
        direction. The vacuum only runs forward. Positive speeds turn the motor in its default
        (cleaning) direction. Default direction for the side brush is counterclockwise. Default
        direction for the main brush/flapper is inward.

        Main Brush and Side Brush duty cycle clamped between -127 and 127
        Vacuum duty cycle clamped between 0 and 127
        """
        main_brush = clamp(main_brush, -127, 127)
        side_brush = clamp(side_brush, -127, 127)
        vacuum = clamp(vacuum, 0, 127)
        data = struct.pack('BBB', main_brush, side_brush, vacuum)
        self.serial.write(Opcode.MOTORS_PWM + data)
    def leds(self, # pylint: disable=too-many-arguments
             home=False, spot=False, check=False, debris=False,
             power_color=0, power_intensity=0):
        """
        This command controls the LEDs common to all models of Roomba 600. The power LED is
        specified by values: one for the color and the other for the intensity. All other LEDs are
        either on or off.

        Home and Spot use green LEDs
        Check Robot uses an orange LED
        Debris uses a blue LED
        Power LED Color: 0 = green, 255 = red, intermediate values are other colors
        Power LED Intensity: 0 = off, 255 = full intensity, intermediate are inbetween intensities
        """
        power_color = clamp(power_color, 0, 255)
        power_intensity = clamp(power_intensity, 0, 255)
        data = struct.pack('BBB', bitflags(debris, spot, home, check), power_color, power_intensity)
        self.serial.write(Opcode.LEDS + data)
    def scheduling_leds(self, # pylint: disable=too-many-arguments, invalid-name
                        sun=False, mon=False, tue=False, wed=False, thu=False, fri=False, sat=False,
                        colon=False, pm=False, am=False, clock=False, schedule=False):
        """
        This command controls the state of the scheduling LEDs present on the Roomba 560 and 570.
        """
        data = struct.pack('BB',
                           bitflags(sun, mon, tue, wed, thu, fri, sat),
                           bitflags(colon, pm, am, clock, schedule))
        self.serial.write(Opcode.LEDS_SCHEDULING + data)
    @staticmethod
    def digit(top=False, top_right=False, bottom_right=False, # pylint: disable=too-many-arguments
              bottom=False, bottom_left=False, top_left=False, middle=False):
        """
        Create a bit-flags for a 7-segment display digit. The result of this can be given to
        `digit_leds_raw()`.
        """
        return bitflags(top, top_right, bottom_right, bottom,
                        bottom_left, top_left, middle)
    def digit_leds_raw(self, digit3=0, digit2=0, digit1=0, digit0=0):
        """
        This command controls the four 7 segment displays on the Roomba 560 and 570.

        See manual for more information.

        You can pass the integer for the digit bits (like Roomba.digit() returns) or a typle of
        the segments to use (which will be passed to Roomba.digit()).

        NOTE: This opcode does not work on current Create 2 and Roomba 500/600 firmware versions.
        """
        if isinstance(digit3, tuple):
            digit3 = Roomba.digit(*digit3)
        if isinstance(digit2, tuple):
            digit2 = Roomba.digit(*digit2)
        if isinstance(digit1, tuple):
            digit1 = Roomba.digit(*digit1)
        if isinstance(digit0, tuple):
            digit0 = Roomba.digit(*digit0)
        data = struct.pack('BBBB', digit3, digit2, digit1, digit0)
        self.serial.write(Opcode.LEDS_DIGIT_RAW + data)
    def digit_leds_ascii(self, string):
        """
        This command controls the four 7 segment displays on the Roomba 560 and 570 using ASCII
        character codes. Because a 7 segment display is not sufficient to display alphabetic
        characters properly, all characters are an approximation, and not all ASCII codes are
        implemented.

        See manual for more information.
        """
        if len(string) > 4:
            raise ValueError('maximum length 4 string/bytes')
        if isinstance(string, str):
            string = string.encode('ascii')
        string = string.upper()
        if any(ch < 32 or ch > 126 for ch in string):
            raise ValueError('invalid characters')
        string += b' '*(4-len(string))
        self.serial.write(Opcode.LEDS_DIGIT_ASCII + string)
    def press_buttons(self, buttons=Buttons.NONE, # pylint: disable=too-many-arguments
                      clean=False, spot=False, dock=False,
                      minute=False, hour=False, day=False, schedule=False, clock=False):
        """
        This command lets you push Roomba's buttons. The buttons will automatically release after
        1/6th of a second. Available in Passive, Safe, and Full modes.
        """
        buttons |= bitflags(clean, spot, dock, minute, hour, day, schedule, clock)
        data = struct.pack('B', buttons)
        self.serial.write(Opcode.BUTTONS + data)
    @staticmethod
    def note(name):
        """
        Given a note name like A4 or D#5 converts it to the MIDI note value to be given to
        create_song. The lowest note the Roomba can play is G1 (49 Hz, MIDI 31) and the highest
        note possible is above what pianos can play. The 'pleasant' range is a single octave from
        C4 (261.63 Hz, MIDI 60) to B5 (987.77 Hz, MIDI 83).
        """
        # Find distance from A4 (440 Hz, MIDI 69)
        half_steps = {'C':-9, 'C#':-8, 'D':-7, 'D#':-6, 'E':-5, 'F':-4,
                      'F#':-3, 'G':-2, 'G#':-1, 'A':0, 'A#':1, 'B':2}
        half_steps = half_steps[name[:-1]]
        octave = int(name[-1]) - 4
        return octave*12 + half_steps + 69
    def create_song(self, song_num, notes, durations):
        """
        This command lets you specify up to four songs to the OI that you can play at a later time.
        Each song is associated with a song number. The Play command uses the song number to
        identify your song selection. Each song can contain up to sixteen notes. Each note is
        associated with a note number that uses MIDI note definitions and a duration that is
        specified in fractions of a second. Available in Passive, Safe, and Full modes.

        notes:
            The pitch of the musical note Roomba will play, according to the MIDI note numbering
            scheme. Roomba considers all musical notes outside the range of 31 – 127 as rest notes,
            and will make no sound during the duration of those notes. Between 60 and 83 are likely
            the most pleasing. If the notes are given as a list of strings then they are converted
            with the notes method.

        durations:
            The duration of a musical note, in increments of 1/64th of a second. Example: a
            half-second long musical note has a duration value of 32.

        Returns the overall duration of the saved song in seconds.
        """
        # NOTE: some Roombas/Creates actually support 16 songs...
        if song_num < 0 or song_num > 3:
            raise ValueError('song number must be 0 to 3')
        if len(notes) != len(durations):
            raise ValueError('number of notes and durations must be equal')
        if not notes or len(notes) > 16:
            raise ValueError('must be between 1 and 16 notes')
        notes = [Roomba.note(n) if isinstance(n, str) else n for n in notes]
        data = struct.pack('BB', song_num, len(notes))
        data += b''.join(struct.pack('BB', n, d) for n, d in zip(notes, durations))
        self.serial.write(Opcode.SONG + data)
        return sum(durations) / 64
    def play_song(self, song_num):
        """
        This command lets you select a song to play from the songs added to Roomba using the Song
        command. You must add one or more songs to Roomba using the Song command in order for the
        Play command to work. The song number must be from 0 to 3.
        """
        # NOTE: some Roombas/Creates actually support 16 songs...
        if song_num < 0 or song_num > 3:
            raise ValueError('song number must be 0 to 3')
        data = struct.pack('B', song_num)
        self.serial.write(Opcode.PLAY + data)

    # Input Commands
    @staticmethod
    def __get_sensor(sensor):
        if isinstance(sensor, int):
            return Sensor(sensor) # pylint: disable=no-value-for-parameter
        if isinstance(sensor, str):
            return Sensor[sensor]
        if isinstance(sensor, Sensor):
            return sensor
        raise TypeError()
    def __required_time(self, nbytes):
        return nbytes*10/self.serial.baudrate
    def sensor(self, sensor):
        """
        This command requests the OI to send a packet of sensor data bytes. There are 58 different
        sensor data packets. Each provides a value of a specific sensor or group of sensors.

        The sensor can be the packet id, the name of a sensor, or the Sensor value.
        """
        sensor = Roomba.__get_sensor(sensor)
        data = struct.pack('B', sensor.packet_id)
        self.serial.write(Opcode.SENSORS + data)
        self.serial.reset_input_buffer()
        wait = self.__required_time(sensor.size) - 0.0005
        if wait > 0:
            time.sleep(wait)
        return sensor.parse(self.serial.read(sensor.size))
    def query_list(self, *sensors):
        """
        This command lets you ask for a list of sensor packets. The result is returned once, as in
        the Sensors command. The robot returns the packets in the order you specify.

        The sensors can be the packet ids, the names of the sensors, or the Sensors values.
        """
        num = len(sensors)
        if num < 1 or num > 255:
            raise ValueError('invalid number of sensors')
        sensors = [Roomba.__get_sensor(sensor) for sensor in sensors]
        data = struct.pack(str(num+1) + 'B', num, *[sensor.packet_id for sensor in sensors])
        self.serial.write(Opcode.QUERY_LIST + data)
        self.serial.reset_input_buffer()
        datatype, size, struct_format = Sensor.summarize_group(sensors)
        wait = self.__required_time(size) - 0.001
        if wait > 0:
            time.sleep(wait)
        return datatype._make(
            Sensor.convert_list(sensors, struct.unpack(struct_format, self.serial.read(size))))
    def stream(self, callback, *sensors):
        """
        This command starts a stream of data packets. The list of packets requested is sent every
        15 ms, which is the rate Roomba uses to update data.

        The callback function will be called for each packet recieved and given a single argument
        with the collection of sensor data. That function must return True if it wishes to keep
        recieving data. To stop recieving data it can return False or another thread (not the
        callback) can call pause_stream(). If pause_stream() is called then a timeout exception
        will be raised from this function.
        """
        num = len(sensors)
        if num < 1 or num > 255:
            raise ValueError('invalid number of sensors')
        sensors = [Roomba.__get_sensor(sensor) for sensor in sensors]
        data = struct.pack(str(num+1) + 'B', num, *[sensor.packet_id for sensor in sensors])
        size = sum(s.size for s in sensors)
        if size+num+3 > 15/10*self.serial.baudrate:
            raise ValueError('requesting too much data to stream')

        # Start the stream
        self.serial.write(Opcode.STREAM + data)
        self.serial.reset_input_buffer()
        self.__stream_read(callback)
    def __stream_read(self, callback):
        # Keep reading data from the stream until the callback returns False
        try:
            orig_timeout = self.serial.timeout
            self.serial.timeout = 0.1 # first iteration needs a bit longer wait time
            while True:
                header, n_bytes = struct.unpack('BB', self.serial.read(2))
                if header != 19:
                    raise ValueError('did not recieve expected data from Roomba')
                self.serial.timeout = 0.015
                data = self.serial.read(n_bytes)
                checksum = struct.unpack('B', self.serial.read(1))[0]
                self.serial.timeout = 0.03
                #print(time.perf_counter()) # comes about every 16ms
                if (header + n_bytes + checksum + sum(x for x in data)) & 0xFF != 0:
                    raise ValueError('did not recieve expected data from Roomba')
                pos, sensors, out = 0, [], []
                while pos < n_bytes:
                    packet_id = data[pos]
                    pos += 1
                    sensor = Sensor(packet_id) # pylint: disable=no-value-for-parameter
                    sensors.append(sensor)
                    out.append(sensor.parse(data[pos:pos+sensor.size]))
                    pos += sensor.size
                out = Sensor.convert_list(sensors, out)
                if not callback(out):
                    break
        finally:
            self.pause_stream()
            self.serial.timeout = orig_timeout
    def pause_stream(self):
        """
        This command lets you stop the stream without clearing the list of requested packets.

        Do not call this from the callback function that is processing streaming data. The only
        place it can be called from is another thread in which case the thread reading the
        streaming data will have a timeout exception.
        """
        self.serial.write(Opcode.STREAM_PAUSE_RESUME + b'\x00')
    def resume_stream_raw(self, callback):
        """
        This command lets you start the stream using the list of packets last requested. Like
        stream this will block until the callback returns False or the stream is paused.
        """
        self.serial.write(Opcode.STREAM_PAUSE_RESUME + b'\x01')
        self.__stream_read(callback)

    # Add all sensors (except unused and groups) as named properties for easy access
    Roomba = vars()
    for _sensor in Sensor.__members__.values():
        if _sensor.name.startswith('_') or _sensor.name.startswith('GROUP'):
            continue
        property_name = _sensor.name.lower()
        assert property_name not in Roomba # pylint: disable=undefined-variable
        Roomba[property_name] = make_sensor_property(_sensor)
    del _sensor, property_name, Roomba # pylint: disable=undefined-loop-variable
