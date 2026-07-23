# API Documentation for `ims_sd_driver`

## Class: `IMSSDDriver`

Serial port I/O class for IMS-SD.
IMS-SD communicates via a virtual COM port.

Protocol:
- Baud rate  : 921600
- Flow ctrl  : RTS/CTS (Handshake.RequestToSend)
- Command terminator : LF (
)
- Data packet: 11 channels × 4 hex chars + LF  (45 bytes total)


### `_close`()

```python
_close(self)
```

Close the serial port.

### `_find_port_by_name`()

```python
_find_port_by_name(self, search_product_name, serial_number=None, location=None)
```

Find the IMS-SD virtual COM port by name and optionally by
serial number or location.

Discovery strategy:
1. If serial_number is given, match port.serial_number.
2. If location is given, match port.location.
3. Otherwise, return the first port whose description
contains search_product_name.
4. Fallback: return the first /dev/ttyUSB* port found.

**Args:**

- `search_product_name` (str): The product name to search for
  (e.g. 'FT230X Basic UART').
- `serial_number` (str, optional): Device serial number string.
  Defaults to None.
- `location` (str, optional): Device USB location string (e.g. '1-2').
  Defaults to None.

**Returns:**

- `dict or None`:
  - dict: {'port': str, 'product': str} on success.
  - None: if not found.


### `_is_connected`()

```python
_is_connected(self)
```

Return whether the serial port is open.

**Returns:**

- `bool`: True if connected, False otherwise.


### `_open`()

```python
_open(self, port, timeout=1.0)
```

Open the serial port.

**Args:**

- `port` (str): The device port path.
- `timeout` (float, optional): Serial read timeout [sec]. Defaults to 1.0.


### `_print_info`()

```python
_print_info(self)
```

Print serial port settings.

### `_recv_command`()

```python
_recv_command(self, terminator=b'\n')
```

Read from serial until the terminator, strip the trailing terminator.

**Args:**

- `terminator` (bytes, optional): 
  The terminator to end reading. Defaults to b'\n'.

**Returns:**

- `str`: Received line decoded as UTF-8 (without trailing terminator).


### `_reset_input_buffer`()

```python
_reset_input_buffer(self)
```

Discard any data in the serial receive buffer.

### `_send_command`()

```python
_send_command(self, command_string)
```

Write a command string to the serial port.

**Args:**

- `command_string` (str): Command text including terminating LF.

**Returns:**

- `int`: Number of bytes written, or 0 on error.


## Class: `IMSSDDriverForRobot`

Command I/O class for IMS-SD IMU amplifier.

Data channels (in order):
Acc  X/Y/Z   [G]      positions  0-11
Gyro X/Y/Z   [deg/s]  positions 12-23
Mag  X/Y/Z   [uT]     positions 24-35
Temperature  [degC]   positions 36-39
Battery SoC  [%]      positions 40-43

Engineering conversion:
Acc  [G]     = AD * accFS  / 32000   (accFS: 4/8/16/32)
Gyro [deg/s] = AD * 4000   / 32000
Mag  [uT]    = AD * 300    / 32000
Temp [degC]  = AD / 333.87 + 21
SoC  [%]     = AD (raw integer)

### `__del__`()

```python
__del__(self)
```

Destructor.

### `__init__`()

```python
__init__(self, debug=False, frequency=100, acc_range=30, timeout=1.0, port=None, serial_number=None, location=None)
```

Construct IMSSDDriverForRobot class instance.

**Args:**

- `debug` (bool, optional): True enables verbose console output.
  Defaults to False.
- `frequency` (int, optional): Sensing frequency [Hz] (100/500/1000).
  Defaults to 100.
- `acc_range` (int, optional): Accelerometer full-scale range [G]
  (4/8/16/30). Defaults to 30.
- `timeout` (float, optional): Serial read timeout [sec].
  Defaults to 1.0.
- `port` (str, optional): Explicit port path (e.g. '/dev/ttyUSB0').
  When specified, serial_number and location are ignored.
  Defaults to None (auto-detect).
- `serial_number` (str, optional): Device serial number string to
  distinguish between multiple IMS-SD units. Defaults to None.
- `location` (str, optional): Device USB location string (e.g. '1-2')
  to distinguish between multiple IMS-SD units. Defaults to None.


### `_data_conversion`()

```python
_data_conversion(self)
```

Continuously receive and parse data packets (background thread).

### `_get_reply`()

```python
_get_reply(self, command_string)
```

Send a command and return the reply.

Pauses the data conversion thread, flushes the input buffer,
sends the command, and reads reply lines until a non-data line
is received (skipping any streaming data packets that arrive
before the command reply).

**Args:**

- `command_string` (str): Command including LF terminator.

**Returns:**

- `str`: Reply line (without LF), or '' on error.


### `_parse_packet`()

```python
_parse_packet(self, line)
```

Parse a 44-character hex data packet into engineering values.

**Args:**

- `line` (str): 44-character uppercase hex string (no LF).

**Raises:**

- `ValueError`: If hex conversion fails.
- `IndexError`: If the string is too short.


### `_ros_publish`()

```python
_ros_publish(self)
```

Placeholder overridden by a ROS node after data conversion.

**Returns:**

- `bool`: False (no-op in base class).


### `close`()

```python
close(self)
```

Stop data conversion, close the serial port, and join the thread.

### `get_acc_range`()

```python
get_acc_range(self)
```

Get accelerometer range code from the amplifier.

**Returns:**

- `int or None`: Range code (1/2/3/4) on success, None on failure.


### `get_data`()

```python
get_data(self)
```

Return the latest engineering data snapshot.

**Returns:**

- `Tuple[float, list, list, list, float, float]`:
  - float: Timestamp (time.time()) of the last received packet.
  - list[float]: Acceleration [X, Y, Z] in [G].
  - list[float]: Angular velocity [X, Y, Z] in [deg/s].
  - list[float]: Magnetic field [X, Y, Z] in [uT].
  - float: Temperature [degC].
  - float: Battery state of charge [%].


### `get_for_robot`()

```python
get_for_robot(self)
```

Get whether the amplifier is in robot mode.

**Returns:**

- `Tuple[str, bool]`:
  - str: Raw reply string.
  - bool: True if robot mode is enabled.


### `get_frequency`()

```python
get_frequency(self)
```

Get current sensing frequency from the amplifier.

**Returns:**

- `int or None`: Frequency [Hz] on success, None on failure.


### `get_serial`()

```python
get_serial(self)
```

Get device serial number string.

**Returns:**

- `str or None`: Serial number on success, None on failure.


### `is_connected`()

```python
is_connected(self)
```

Return whether the serial port is open.

**Returns:**

- `bool`: True if connected, False otherwise.


### `set_acc_range`()

```python
set_acc_range(self, range_code)
```

Set accelerometer full-scale range.

**Args:**

- `range_code` (int): 1=4G, 2=8G, 3=16G, 4=30G.

**Returns:**

- `bool`: True on success, False on failure.


### `set_for_robot`()

```python
set_for_robot(self)
```

Set the amplifier to robot mode if available or to non-robot mode.

Checks the current robot-mode state via `get_for_robot()`. If the
amplifier is currently disabled (`FOR_ROBOT_0`), sends the command to
enable robot mode. Does not support disabling robot mode once set.

**Returns:**

- `str`: Reply for the command (e.g. `'FOR_ROBOT_1'`) on success, or an
  error message (`'Set for Robot: Error'`) if the amplifier could not
  be queried or the command failed.


### `set_frequency`()

```python
set_frequency(self, frequency)
```

Set sensing frequency.

**Args:**

- `frequency` (int): Frequency [Hz]: 100, 500, or 1000.

**Returns:**

- `bool`: True on success, False on failure.


### `start`()

```python
start(self)
```

Send START command and begin data conversion.

**Returns:**

- `str`: Reply from the amplifier.


### `stop`()

```python
stop(self)
```

Send STOP command and halt data conversion.

**Returns:**

- `str`: Reply from the amplifier.


