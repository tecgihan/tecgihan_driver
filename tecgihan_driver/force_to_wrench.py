from geometry_msgs.msg import Vector3Stamped, WrenchStamped

import rclpy

from rclpy.node import Node


class ForceToWrench(Node):
    """ROS Node for converting Vector3Stamped to WrenchStamped ROS Topic.

    ROS Parameters:
        input_topic (str): Topic name to subscribe (Vector3Stamped).
            Defaults to '/dma03_publisher/force' for backward compatibility.
        output_topic (str): Topic name to publish (WrenchStamped).
            Defaults to '/dma03_publisher/wrench' for backward compatibility.
        frame_id (str): If non-empty, overrides 'header.frame_id' of the
            published WrenchStamped message. Useful when running multiple
            instances of this node to visualize multiple sensors mounted
            at different locations (e.g. DPA-06B with 2 sensors), since
            some publishers may stamp all of their topics with the same
            frame_id. Defaults to '' (keep the input message's frame_id).

    To run two instances simultaneously (e.g. for DPA-06B 3axis mode),
    launch two nodes with unique 'name' and different
    input_topic/output_topic/frame_id parameter values.
    """

    def __init__(self):
        """Construct ForceToWrench."""
        super().__init__('force_to_wrench_node')

        self.declare_parameter('input_topic', '/dma03_publisher/force')
        self.declare_parameter('output_topic', '/dma03_publisher/wrench')
        self.declare_parameter('frame_id', '')

        input_topic = self.get_parameter(
            'input_topic').get_parameter_value().string_value
        output_topic = self.get_parameter(
            'output_topic').get_parameter_value().string_value
        self.frame_id_override = self.get_parameter(
            'frame_id').get_parameter_value().string_value

        # Subscribe to Vector3Stamped messages
        self.subscription = self.create_subscription(
            Vector3Stamped,
            input_topic,
            self.listener_callback,
            10
        )

        # Publisher for WrenchStamped messages
        self.publisher = self.create_publisher(
            WrenchStamped,
            output_topic,
            10
        )

        self.get_logger().info(
            'Force to Wrench Node has been started. '
            'input_topic={} output_topic={} frame_id_override={}'.format(
                input_topic, output_topic,
                self.frame_id_override if self.frame_id_override else '(none)'))

    def listener_callback(self, msg: Vector3Stamped):
        """Be called when the input ROS Topic is published.

        Args:
            msg (Vector3Stamped): ROS Topic Data
        """
        # Create a WrenchStamped message and copy the vector to the force field
        wrench_msg = WrenchStamped()
        wrench_msg.header = msg.header  # Copy the header from the input message
        if self.frame_id_override:
            wrench_msg.header.frame_id = self.frame_id_override
        wrench_msg.wrench.force = msg.vector

        # Set torque to zero
        wrench_msg.wrench.torque.x = 0.0
        wrench_msg.wrench.torque.y = 0.0
        wrench_msg.wrench.torque.z = 0.0

        self.publisher.publish(wrench_msg)
        self.get_logger().debug(
            f'Published WrenchStamped: force=({msg.vector.x}, {msg.vector.y}, {msg.vector.z})')


def main(args=None):
    """Execute ROS Node with ForceToWrench."""
    rclpy.init(args=args)
    node = ForceToWrench()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
