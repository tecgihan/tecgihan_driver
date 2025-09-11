# API Documentation for `dma03_driver`

## Class: `DMA03Driver`

Serial port I/O class for DMA-03 for Robot amplifier.

### `_close`()

```python
_close(self)
```

Close the serial port.

### `_find_port_by_id`()

```python
_find_port_by_id(self, vendor_id, product_id)
```

Find a serial port by a vendor ID and a product ID.

**Args:**

- `vendor_id` (str): The device vendor ID
- `product_id` (str): The device product ID

**Returns:**

- `Union[str, None]`:
  - str: The port device string like '/dev/ttyUSB0'.
  - None: VID or PID did not match the actual devoce connected.


### `_find_port_by_name`()

```python
_find_port_by_name(self, product_name, serial_number=None, location=None)
```

Find a serial port by a device name and optionally by a device location.

**Args:**

- `product_name` (str): The product name of the amplifier.
- `serial_number` (str, optional): The device serial number. Defaults to None.
- `location` (str, optional): The device location like '1-2'. Defaults to None.

**Returns:**

- `Union[str, None]`:
  - str: The port device string like '/dev/ttyUSB0'.
  - None: The args did not match the actual device connected.


### `_is_connected`()

```python
_is_connected(self)
```

Return the serial port is connected or not.

**Returns:**

- `bool`: True if connected, False otherwise.


### `_open`()

```python
_open(self, port='/dev/ttyUSB0', product_name='DMA-03B', timeout=1.0)
```

Open a serial port.

**Args:**

- `port` (str, optional): The device port. Defaults to '/dev/ttyUSB0'.
- `product_name` (str, optional): Amplifier product name. Defaults to "DMA-03B".
- `timeout` (float, optional): Set a read timeout value in seconds. Defaults to 1.0.


### `_print_info`()

```python
_print_info(self)
```

Print the serial port informations.

### `_recv_command`()

```python
_recv_command(self, terminator=b'\n')
```

Read the serial port input buffer until the terminator.

**Args:**

- `terminator` (bytes, optional): 
  The terminator to end reading. Defaults to b'
  '.

**Returns:**

- `str`: The received and UTF-8 decoded data.


### `_reset_input_buffer`()

```python
_reset_input_buffer(self)
```

Reset the serial port input buffer.

### `_send_command`()

```python
_send_command(self, command_string)
```

Send command to the serial port write buffer with the command string.

**Args:**

- `command_string` (str): The command to write.

**Returns:**

- `int`: Number of bytes written.


## Class: `DMA03DriverForRobot`

Command I/O class for DMA-03 for Robot amplifier.

### `__del__`()

```python
__del__(self)
```

Destructor of this class instance.

### `__init__`()

```python
__init__(self, debug=False, frequency=1000, init_zero=False, timeout=1.0, serial_number=None, location=None)
```

Construct DMA03DriverForRobot class instance.

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


### `_calculate_eng_data`()

```python
_calculate_eng_data(self, ad1, ad2, ad3)
```

Calculate the engineering data from signed int data with FS values.

**Args:**

- `ad1` (int): Channel 1 integer value
- `ad2` (int): Channel 2 integer value
- `ad3` (int): Channel 3 integer value

**Returns:**

- `Tuple[float, float, float]`:
  - float: Channel 1 engineering data.
  - float: Channel 2 engineering data.
  - float: Channel 3 engineering data.


### `_data_conversion`()

```python
_data_conversion(self)
```

Aquire and convert sensing data with thread.

### `_get_reply`()

```python
_get_reply(self, command_string: str)
```

Send a command to the amplifier and get a reply for it.

**Args:**

- `command_string` (str): Command to send.

**Returns:**

- `str`: Reply for the command.


### `_ros_publish`()

```python
_ros_publish(self)
```

Be overrided in a ROS node.

An empty function to override in a ROS node
to publish a ROS topic after the data conversion.

**Returns:**

- `bool`: False


### `_to_signedint`()

```python
_to_signedint(self, value: int, bits=16)
```

Convert an unsigned int to a signed int.

Converts an unsigned integer to its signed integer representation
using two's complement.

**Args:**

- `value` (int): The unsigned integer to convert
- `bits` (int, optional): The bit width to interpret the value with.
  Defaults to 16.

**Returns:**

- `int`: The signed integer representation of the input value.


### `close`()

```python
close(self)
```

Close the serial port.

Close the serial port
after stopping the amplifier and the data conversion process.

### `get_data`()

```python
get_data(self)
```

Get engineering data.

**Returns:**

- `Tuple[float, float, float, float]`:
  - float: Time of reading data from the serial port.
  - float: Value of X-axis force.
  - float: Value of Y-axis force.
  - float: Value of Z-axis force.


### `get_for_robot`()

```python
get_for_robot(self)
```

Get the amplifier has functions for robot usage or not.

**Returns:**

- `Tuple[str, bool]`:
  - str:  Reply for the command.
  - bool: True if for Robot, False if not for robot.


### `get_fs`()

```python
get_fs(self)
```

Get a list of 3 int data of FS (Full Scale) from the amplifier.

**Returns:**

- `List[int]`: List of 3 int FS [X,Y,Z] data.


### `get_itf`()

```python
get_itf(self)
```

Get a list of 3x3 float data of ITF from the amplifier.

ITF means Interference coefficients.

**Returns:**

- `list float`: List of 3x3 float ITF data


### `is_connected`()

```python
is_connected(self)
```

Return the serial port is connected or not.

**Returns:**

- `bool`: True if connected, False otherwise.


### `set_for_robot`()

```python
set_for_robot(self)
```

Set the amplifier to robot mode if available or to non-robot mode.

**Returns:**

- `str`: Reply for the command or error message if failure.


### `set_frequency`()

```python
set_frequency(self, frequency: int)
```

Set sensing frequency to the amplifier.

**Args:**

- `frequency` (int): Freqency [Hz] of the amplifier sensing.

**Returns:**

- `bool`: True on success, False on failure.

**Note:**

- The set data are Stored in non-volatile memory in the amplifier.


### `set_fs`()

```python
set_fs(self, val_list: list[int])
```

Set 3 int data of FS (Full Scale) to the amplifier.

**Args:**

- `val_list` (list[int]): List of 3 float FS [X,Y,Z] data.

**Returns:**

- `bool`: True on success, False on failure.

**Note:**

- The set data are stored in non-volatile memory in the amplifier.


### `set_itf`()

```python
set_itf(self, val_list: list[float])
```

Set 3x3 float data for ITF in the amplifier.

ITF means Interference coefficients.

**Args:**

- `val_list` (list[float]): list of 3x3 float for ITF to set in the amplifier.

**Returns:**

- `bool`: True on success, False on failure.

**Note:**

- The set data are stored in non-volatile memory in the amplifier.


### `set_zero`()

```python
set_zero(self)
```

Start zero force adjustment and store them.

**Returns:**

- `str`: Reply for the command.

**Note:**

  - The adjustment takes around 2 seconds after sending the command.
  - The adjustment data are stored in non-volatile memory in the amplifier.


### `start`()

```python
start(self)
```

Send START command to the amplifire and start the data conversion.

**Returns:**

- `str`: Reply for the command.


### `stop`()

```python
stop(self)
```

Send STOP command to the amplifier and stop the data conversion.

**Returns:**

- `str`: Reply for the command.


