# API Documentation for `ims_sd_ros_publisher`

## Class: `IMSSDPublisher`

ROS Publisher for IMS-SD.

Published topics:
~/imu         (sensor_msgs/Imu)           - linear acceleration [m/s²] and angular velocity [rad/s]
~/mag         (sensor_msgs/MagneticField)  - magnetic field [T]
~/temperature (sensor_msgs/Temperature)    - temperature [degC]
~/battery     (sensor_msgs/BatteryState)   - battery state of charge

### `__init__`()

```python
__init__(self)
```

Construct IMSSDPublisher.

### `cleanup`()

```python
cleanup(self)
```

Stop and clean up the node.

### `event_callback`()

```python
event_callback(self)
```

Build and publish all ROS topics from the latest sensor data.

**Returns:**

- `bool`: True when executed.


### `parameter_callback`()

```python
parameter_callback(self, params)
```

Handle dynamic ROS parameter changes.

**Args:**

- `params` (list[Parameter]): Changed parameters.

**Returns:**

- `SetParametersResult`: Always successful.


### `main`()

```python
main(args=None)
```

Launch the IMS-SD ROS publisher node.

