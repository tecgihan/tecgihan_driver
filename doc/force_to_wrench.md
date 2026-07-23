# API Documentation for `force_to_wrench`

## Class: `ForceToWrench`

ROS Node for converting Vector3Stamped to WrenchStamped ROS Topic.

**ROS Parameters:**

- `input_topic` (str): Topic name to subscribe (Vector3Stamped).
  Defaults to `/dma03_publisher/force` for backward compatibility.
- `output_topic` (str): Topic name to publish (WrenchStamped).
  Defaults to `/dma03_publisher/wrench` for backward compatibility.
- `frame_id` (str): If non-empty, overrides `header.frame_id` of the
  published WrenchStamped message. Useful when running multiple
  instances of this node to visualize multiple sensors mounted at
  different locations (e.g. DPA-06B with 2 sensors), since some
  publishers may stamp all of their topics with the same frame_id.
  Defaults to `''` (keep the input message's frame_id).

To run two instances simultaneously (e.g. for DPA-06B 3axis mode),
launch two nodes with unique `name` and different
`input_topic`/`output_topic`/`frame_id` parameter values.

### `__init__`()

```python
__init__(self)
```

Construct ForceToWrench. Declares the `input_topic`, `output_topic`,
and `frame_id` ROS parameters, subscribes to `input_topic`, and
creates a publisher on `output_topic`.

### `listener_callback`()

```python
listener_callback(self, msg: geometry_msgs.msg._vector3_stamped.Vector3Stamped)
```

Be called when the input ROS Topic (`input_topic`, default
`/dma03_publisher/force`) is published. Converts the incoming
`Vector3Stamped` into a `WrenchStamped` message (copying the header,
setting `wrench.force` from the vector, and zeroing `wrench.torque`),
optionally overriding `header.frame_id` if the `frame_id` parameter
is set, and publishes it on `output_topic` (default
`/dma03_publisher/wrench`).

**Args:**

- `msg` (Vector3Stamped): ROS Topic Data


### `main`()

```python
main(args=None)
```

Execute ROS Node with ForceToWrench.
