# API Documentation for `dpa06b_ros_publisher`

## Class: `DPA06BPublisher`

ROS Publisher for DPA-06B amplifier.

Supports two sensor configurations via 'sensor_mode' parameter:
'3axis' : 3-axis sensor x 2
Publishes two Vector3Stamped topics:
~/force1 : sensor 1 (ch1-3)
~/force2 : sensor 2 (ch4-6)
'6axis' : 6-axis sensor x 1
Publishes one WrenchStamped topic:
~/wrench : force(x,y,z) + torque(x,y,z)

frame_id parameters:
'frame_id_sensor1' : header.frame_id for ~/force1 (3axis mode)
'frame_id_sensor2' : header.frame_id for ~/force2 (3axis mode)
'frame_id'         : header.frame_id for ~/wrench (6axis mode)

### `__init__`()

```python
__init__(self)
```

Construct DPA06BPublisher.

### `_warn_if_still_default`()

```python
_warn_if_still_default(self, param_name, value_list, default_list)
```

Warn if a coefficient parameter still equals its built-in default.

A write is about to happen (the matching set_itf_* flag is true),
but if the parameter value still equals the built-in identity-
matrix default, the loaded YAML file (param_file/param_path)
most likely does not define this key for the current sensor_mode,
so this default would be written to the amplifier by mistake
instead of the sensor's real ITF coefficients.

**Args:**

- `param_name` (str): ROS parameter name, used in the warning message.
- `value_list` (Sequence[float]): Value currently held by the parameter.
- `default_list` (list[float]): Built-in default value to compare against.

**Returns:**

- `bool`: True if a warning was logged, False otherwise.


### `cleanup`()

```python
cleanup(self)
```

Clean up when stopping the node.

### `event_callback`()

```python
event_callback(self)
```

Publish ROS Topic(s).

3axis mode: publishes ~/force1 and ~/force2 (Vector3Stamped).
6axis mode: publishes ~/wrench (WrenchStamped).

**Returns:**

- `bool`: True if executed.


### `parameter_callback`()

```python
parameter_callback(self, params)
```

Execute processes when a ROS Parameter has changed.

**Args:**

- `params` (list[Parameter]): List of ROS Parameter(s).

**Returns:**

- `SetParametersResult`: Result of setting Parameter.


### `main`()

```python
main(args=None)
```

Execute ROS Node with DPA06BPublisher.

Forces stdout to line-buffered mode before initializing the node.
Under `ros2 launch`, stdout is not a tty and defaults to full
buffering, which delays and reorders the `print()` logs emitted from
within `driver.py`. Reconfiguring to line buffering ensures those
logs are flushed immediately and in the correct order.

