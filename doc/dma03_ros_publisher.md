# API Documentation for `dma03_ros_publisher`

## Class: `DMA03Publisher`

ROS Publisher for DMA-03 for Robot amplifier.

### `__init__`()

```python
__init__(self)
```

Construct DMA03Publisher.


### `cleanup`()

```python
cleanup(self)
```

Clean up when stopping the node.

### `event_callback`()

```python
event_callback(self)
```

Publish ROS Topic.

**Returns:**

- `bool`: True if executed.


### `parameter_callback`()

```python
parameter_callback(self, params)
```

Execute processes when a ROS Pamameter has changed.

**Args:**

- `params` (list[Parameter]): List of ROS Parameter(s).

**Returns:**

- `SetParametersResult`: Result of setting Parameter.


### `main`()

```python
main(args=None)
```

Execute ROS Node with DMA03Publisher.
