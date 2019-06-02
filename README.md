YARC: Yet Another Roomba Controller
===================================

This is a Python library that allows you to control Roomba's and Create's from iRobot using the serial connection. This requires Python 3 and the pyserial library. This can run on many devices such as Raspberry Pis and regular PCs. Tested on the Create 2, some older devices may not support all operations or sensors.

This implements the Open Interface specification by iRobot: http://www.irobot.com/~/media/MainSite/PDFs/About/STEM/Create/create_2_Open_Interface_Spec.pdf

This library implements every single opcode in the specification and provides every sensor in an easy-to-use system. All single sensors are available as attributes on a `yarc.Roomba` object along with `all_sensors` which is a `namedtuple` of all of the sensors. Other groups can be obtained with the `sensor()` method and custom groups can be acquired with `query_list()` method. Single values are returned as `int`s or `bool`s, bit fields are returned as `IntFlag` types, and collections of values are returned as `namedtuple` instances.

This can be installed from source from the Github source or through pip: `pip install yarc`.


Example
-------

```python
import yarc

# Make the Roomba object
bot = yarc.Roomba('/dev/ttyUSB0')

# Start the OI connection - must be the first call
bot.start()

# Switch to 'safe' mode
# In this mode we can completely control the robot unless it 'senses danger'
# in which case it will switch back to 'passive' mode. Danger could be
# detection of a cliff, detection of a wheel drop, or charger plugged in.
bot.safe()

# Commands
bot.drive_distance(100) # drives 100 mm forward
bot.turn_angle(45) # rotates 45 degrees in-place
... # more instructions
print(bot.battery_charge / bot.battery_capacity) # print battery charge percent
print(bot.all_sensors) # print out all sensor data

# Stop the OI connection - must be the last call
bot.stop()
```
