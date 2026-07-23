# API Documentation for `dpa06b_driver`

## Class: `DPA06BDriver`

Driver I/O class for DPA-06B amplifier.

No UART parameters (baudrate, parity, etc.) are required.

### `_close`()

```
_close(self)
```

Close the serial port.

### `_find_port_by_id`()

```
_find_port_by_id(self, vendor_id, product_id)
```

Find a serial port by a vendor ID and a product ID.

**Args:**

- `vendor_id` (int): The device vendor ID.
- `product_id` (int): The device product ID.

**Returns:**

- `Union[str, None]`:
  * str: The port device string like '/dev/ttyUSB0'.
  * None: VID or PID did not match the actual device connected.

### `_find_port_by_name`()

```
_find_port_by_name(self, product_name, serial_number=None, location=None)
```

Find a serial port by a device name and optionally by a device location.

**Args:**

- `product_name` (str): The product name of the amplifier.
- `serial_number` (str, optional): The device serial number. Defaults to None.
- `location` (str, optional): The device location like '1-2'. Defaults to None.

**Returns:**

- `Union[dict, None]`:
  * dict: {'port': str, 'product': str}
  * None: The args did not match the actual device connected.

### `_is_connected`()

```
_is_connected(self)
```

Return the serial port is connected or not.

**Returns:**

- `bool`: True if connected, False otherwise.

### `_open`()

```
_open(self, port='/dev/ttyUSB0', timeout=1.0)
```

Open a port for DPA-06B.

No baudrate or UART parameters are set.

**Args:**

- `port` (str, optional): The device port. Defaults to '/dev/ttyUSB0'.
- `timeout` (float, optional): Set a read timeout value in seconds. Defaults to 1.0.

### `_print_info`()

```
_print_info(self)
```

Print the serial port informations.

### `_recv_command`()

```
_recv_command(self, terminator=b'\n')
```

Read the serial port input buffer until the terminator.

**Args:**

- `terminator` (bytes, optional): The terminator to end reading. Defaults to b'\n'.

**Returns:**

- `str`: The received and UTF-8 decoded data.

### `_reset_input_buffer`()

```
_reset_input_buffer(self)
```

Reset the serial port input buffer.

### `_send_command`()

```
_send_command(self, command_string)
```

Send command to the serial port write buffer with the command string.

**Args:**

- `command_string` (str): The command to write.

**Returns:**

- `int`: Number of bytes written.

## Class: `DPA06BDriverForRobot`

Command I/O class for DPA-06B amplifier.

DPA-06B supports two sensor configurations selectable by sensor_mode:
    '3axis' : 3-axis sensor x 2 (default)
              - ITF: 3x3=9 values x 2 sets
                     (one set for 3-axis sensor1, one set for 3-axis sensor2)
              - FS : 6 values [ch1,ch2,ch3,ch4,ch5,ch6]
    '6axis' : 6-axis sensor x 1
              - ITF: 6x6=36 values x 1 set
              - FS : 6 values [ch1,ch2,ch3,ch4,ch5,ch6]

### `__del__`()

```
__del__(self)
```

Destructor of this class instance.

### `__init__`()

```
__init__(self, debug=False, frequency=1000, init_zero=False, timeout=1.0, serial_number=None, location=None, sensor_mode='3axis')
```

Construct DPA06BDriverForRobot class instance.

**Args:**

- `debug` (bool, optional): True is for Debug mode, False is not.
Defaults to False.
- `frequency` (int, optional): Sensing frequency.
Defaults to 1000.
- `init_zero` (bool, optional): True to initialize as Zero forces.
Defaults to False.
- `timeout` (float, optional): The max time [sec] to wait data
during read operation. Defaults to 1.0.
- `serial_number` (str, optional): The device serial number
to distinguish between multiple amplifiers.
Defaults to None.
- `location` (str, optional): The device location like '1-2'
to distinguish between multiple amplifiers.
Defaults to None.
- `sensor_mode` (str, optional): Sensor configuration mode.
'3axis': 3-axis sensor x 2 (ITF: 3x3 x 2).
'6axis': 6-axis sensor x 1 (ITF: 6x6 x 1).
Defaults to '3axis'.

### `_calculate_eng_data`()

```
_calculate_eng_data(self, ad1, ad2, ad3, fs1, fs2, fs3, ad4=None, ad5=None, ad6=None, fs4=None, fs5=None, fs6=None)
```

Calculate the engineering data from signed int data with FS values.

For '3axis' mode: call with 3 channels (ad1-3, fs1-3).
For '6axis' mode: call with 6 channels (ad1-6, fs1-6).

**Args:**

- `ad1` (int): Channel 1 integer value.
- `ad2` (int): Channel 2 integer value.
- `ad3` (int): Channel 3 integer value.
- `fs1` (int): Full Scale value for channel 1.
- `fs2` (int): Full Scale value for channel 2.
- `fs3` (int): Full Scale value for channel 3.
- `ad4` (int, optional): Channel 4 integer value. For '6axis' mode.
- `ad5` (int, optional): Channel 5 integer value. For '6axis' mode.
- `ad6` (int, optional): Channel 6 integer value. For '6axis' mode.
- `fs4` (int, optional): Full Scale value for channel 4. For '6axis' mode.
- `fs5` (int, optional): Full Scale value for channel 5. For '6axis' mode.
- `fs6` (int, optional): Full Scale value for channel 6. For '6axis' mode.

**Returns:**

- `Tuple[float, ...]`: 3 floats for '3axis' mode, 6 floats for '6axis' mode.

### `_data_conversion`()

```
_data_conversion(self)
```

Aquire and convert sensing data with thread.

### `_get_data`()

```
_get_data(self, *eng_values)
```

Get engineering data snapshot with assigning guard.

**Args:**

- `*eng_values` (float): Engineering values to snapshot.

**Returns:**

- `Tuple[float, ...]`: Time followed by the engineering values.

### `_get_itf`()

```
_get_itf(self, index_map, label='')
```

Get an ITF matrix from the amplifier.

Reads each ITF element individually via GET_ITF_6X12_xx, since the
amplifier exposes only a single per-element ITF command, not a bulk
per-sensor / per-mode ITF command.

**Args:**

- `index_map` (list[int]): Device-side element indices (0-71) to
read, in the order they should appear in the result.
- `label` (str, optional): Human-readable label (e.g. '3axis sensor1')
used only for the summary log line. Defaults to ''.

**Returns:**

- `list[float]`: List of float ITF data, or None on failure.

### `_get_itf_from_device`()

```
_get_itf_from_device(self, item)
```

Get a single ITF coefficient from the amplifier.

**Args:**

- `item` (int): ITF element index (0-71 on the device side;
only 0-35 are actually used, see class docstring).

**Returns:**

- `float`: The ITF coefficient value, or None on failure.

### `_get_reply`()

```
_get_reply(self, command_string)
```

Send a command to the amplifier and get a reply for it.

**Args:**

- `command_string` (str): Command to send.

**Returns:**

- `str`: Reply for the command.

### `_ros_publish`()

```
_ros_publish(self)
```

Be overrided in a ROS node.

An empty function to override in a ROS node
to publish a ROS topic after the data conversion.

**Returns:**

- `bool`: False

### `_set_itf`()

```
_set_itf(self, val_list, index_map, get_func, expected_dim)
```

Set an ITF matrix to the amplifier.

Writes each ITF element individually via SET_ITF_6X12_xx_<value>,
since the amplifier exposes only a single per-element ITF command,
not a bulk per-sensor / per-mode ITF command.

**Args:**

- `val_list` (list[float]): List of float ITF values.
- `index_map` (list[int]): Device-side element indices (0-71),
in the same order as val_list.
- `get_func` (callable): Corresponding getter to verify written values.
- `expected_dim` (int): Expected number of ITF values (9 or 36).

**Returns:**

- `bool`: True on success, False on failure.

### `_set_itf_to_device`()

```
_set_itf_to_device(self, item, value)
```

Set a single ITF coefficient to the amplifier.

**Args:**

- `item` (int): ITF element index (0-71 on the device side;
only 0-35 are actually used, see class docstring).
- `value` (float): The ITF coefficient value to set.

**Returns:**

- `bool`: True on success ('SET_ITF_6X12_OK'), False otherwise.

### `_to_signedint`()

```
_to_signedint(self, value, bits=16)
```

Convert an unsigned int to a signed int.

Converts an unsigned integer to its signed integer representation
using two's complement.

**Args:**

- `value` (int): The unsigned integer to convert.
- `bits` (int, optional): The bit width to interpret the value with.
Defaults to 16.

**Returns:**

- `int`: The signed integer representation of the input value.

### `close`()

```
close(self)
```

Close the serial port.

Close the serial port
after stopping the amplifier and the data conversion process.

### `get_data`()

```
get_data(self)
```

Get engineering data for all 6 channels.

For '6axis' mode.

**Returns:**

- `Tuple[float, float, float, float, float, float, float]`:
  * float: Time of reading data from the serial port.
  * float: Value of channel 1.
  * float: Value of channel 2.
  * float: Value of channel 3.
  * float: Value of channel 4.
  * float: Value of channel 5.
  * float: Value of channel 6.

### `get_data_3axis_sensor1`()

```
get_data_3axis_sensor1(self)
```

Get engineering data for sensor 1 (ch1-3).

For '3axis' mode.

**Returns:**

- `Tuple[float, float, float, float]`:
  * float: Time of reading data from the serial port.
  * float: Value of channel 1.
  * float: Value of channel 2.
  * float: Value of channel 3.

### `get_data_3axis_sensor2`()

```
get_data_3axis_sensor2(self)
```

Get engineering data for sensor 2 (ch4-6).

For '3axis' mode.

**Returns:**

- `Tuple[float, float, float, float]`:
  * float: Time of reading data from the serial port.
  * float: Value of channel 4.
  * float: Value of channel 5.
  * float: Value of channel 6.

### `get_for_robot`()

```
get_for_robot(self)
```

Get the amplifier has functions for robot usage or not.

**Returns:**

- `Tuple[str, bool]`:
  * str:  Reply for the command.
  * bool: True if for Robot, False if not for robot.

### `get_frequency`()

```
get_frequency(self)
```

Get current sensing frequency from the amplifier.

**Returns:**

- `int or None`: Frequency [Hz] on success, None on failure.

### `get_fs`()

```
get_fs(self)
```

Get a list of 6 int data of FS (Full Scale) from the amplifier.

**Returns:**

- `List[int]`: List of 6 int FS [ch1,ch2,ch3,ch4,ch5,ch6] data.

### `get_itf_3axis_sensor1`()

```
get_itf_3axis_sensor1(self)
```

Get a list of 3x3 float ITF data for 3-axis sensor1 from the amplifier.

For '3axis' mode only.
This is the interference correction matrix for 3-axis sensor1 (ch1-3).

**Returns:**

- `list[float]`: List of 9 float ITF data for 3-axis sensor1, or None on failure.

### `get_itf_3axis_sensor2`()

```
get_itf_3axis_sensor2(self)
```

Get a list of 3x3 float ITF data for 3-axis sensor2 from the amplifier.

For '3axis' mode only.
This is the interference correction matrix for 3-axis sensor2 (ch4-6).

**Returns:**

- `list[float]`: List of 9 float ITF data for 3-axis sensor2, or None on failure.

### `get_itf_6axis`()

```
get_itf_6axis(self)
```

Get a list of 6x6 float data of ITF from the amplifier.

For '6axis' mode only.
ITF is the interference correction matrix for the 6-axis sensor.

**Returns:**

- `list[float]`: List of 36 float ITF data, or None on failure.

### `is_connected`()

```
is_connected(self)
```

Return the serial port is connected or not.

**Returns:**

- `bool`: True if connected, False otherwise.

### `set_for_robot`()

```
set_for_robot(self)
```

Set the amplifier to robot mode if available or to non-robot mode.

**Returns:**

- `str`: Reply for the command or error message if failure.

### `set_frequency`()

```
set_frequency(self, frequency)
```

Set sensing frequency to the amplifier.

**Args:**

- `frequency` (int): Frequency [Hz] of the amplifier sensing.

**Returns:**

- `bool`: True on success, False on failure.

**Note:**

- The set data are stored in non-volatile memory in the amplifier.

### `set_fs`()

```
set_fs(self, val_list)
```

Set 6 int data of FS (Full Scale) to the amplifier.

**Args:**

- `val_list` (list[int]): List of 6 int FS [ch1,ch2,ch3,ch4,ch5,ch6].

**Returns:**

- `bool`: True on success, False on failure.

**Note:**

- The set data are stored in non-volatile memory in the amplifier.

### `set_itf_3axis_sensor1`()

```
set_itf_3axis_sensor1(self, val_list)
```

Set 3x3 float ITF data for 3-axis sensor1 to the amplifier.

For '3axis' mode only.
This is the interference correction matrix for 3-axis sensor1 (ch1-3).

**Args:**

- `val_list` (list[float]): List of 9 float ITF values for 3-axis sensor1.

**Returns:**

- `bool`: True on success, False on failure.

**Note:**

- The set data are stored in non-volatile memory in the amplifier.

### `set_itf_3axis_sensor2`()

```
set_itf_3axis_sensor2(self, val_list)
```

Set 3x3 float ITF data for 3-axis sensor2 to the amplifier.

For '3axis' mode only.
This is the interference correction matrix for 3-axis sensor2 (ch4-6).

**Args:**

- `val_list` (list[float]): List of 9 float ITF values for 3-axis sensor2.

**Returns:**

- `bool`: True on success, False on failure.

**Note:**

- The set data are stored in non-volatile memory in the amplifier.

### `set_itf_6axis`()

```
set_itf_6axis(self, val_list)
```

Set 6x6 float data for ITF to the amplifier.

For '6axis' mode only.
ITF is the interference correction matrix for the 6-axis sensor.

**Args:**

- `val_list` (list[float]): List of 36 float ITF values.

**Returns:**

- `bool`: True on success, False on failure.

**Note:**

- The set data are stored in non-volatile memory in the amplifier.

### `set_zero`()

```
set_zero(self)
```

Start zero force adjustment and store them.

**Returns:**

- `str`: Reply for the command.

**Note:**

- The adjustment takes around 2 seconds after sending the command.
- The adjustment data are stored in non-volatile memory in the amplifier.

### `start`()

```
start(self)
```

Send START command to the amplifier and start the data conversion.

**Returns:**

- `str`: Reply for the command.

### `stop`()

```
stop(self)
```

Send STOP command to the amplifier and stop the data conversion.

Unlike other commands handled via _get_reply(), STOP is sent while
the data acquisition thread may still be mid-stream. _get_reply()
only skips replies whose length exactly matches a full data packet
(data_length chars), so a truncated/partial data packet received
right after STOP can slip through as if it were the STOP reply.
To avoid that, explicitly wait for a line containing STOP_OK or
STOP_NG (max 2 seconds), discarding anything else in between.

**Returns:**

- `str`: 'STOP_OK' or 'STOP_NG' on a valid reply,
'' if no reply was received within the timeout.

