from builtin_interfaces.msg import Time
from geometry_msgs.msg import Vector3Stamped
from rcl_interfaces.msg import SetParametersResult

import rclpy

from rclpy.node import Node
from rclpy.parameter import Parameter

from tecgihan_driver.dma03_driver import DMA03DriverForRobot


class DMA03Publisher(Node):
    """ROS Publisher for DMA-03 for Robot amplifier."""

    def __init__(self):
        """Construct DMA03Publisher.

        Args:
            str: Node name.
        """
        super().__init__('dma03_publisher')

        # ROS Parameters
        self.declare_parameter('debug', False)
        self.declare_parameter('timer', -0.01)
        self.declare_parameter('frequency', 100)
        self.declare_parameter('init_zero', False)
        self.declare_parameter('set_fs', False)
        self.declare_parameter('set_itf', False)
        self.declare_parameter('timeout', 1.0)
        self.declare_parameter('param_file', 'UL100901.yaml')
        self.declare_parameter('param_path', '')
        self.declare_parameter('fs_list', [1000, 1000, 1000])
        self.declare_parameter(
            'itf_list', [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0])
        self.declare_parameter('serial_no', '')
        self.declare_parameter('location', '')
        self.declare_parameter('frame_id', 'force_sensor')

        debug_ = self.get_parameter(
            'debug').get_parameter_value().bool_value
        timer_ = self.get_parameter(
            'timer').get_parameter_value().double_value
        frequency_ = self.get_parameter(
            'frequency').get_parameter_value().integer_value
        init_zero_ = self.get_parameter(
            'init_zero').get_parameter_value().bool_value
        set_fs_ = self.get_parameter(
            'set_fs').get_parameter_value().bool_value
        set_itf_ = self.get_parameter(
            'set_itf').get_parameter_value().bool_value
        timeout_ = self.get_parameter(
            'timeout').get_parameter_value().double_value
        param_file_ = self.get_parameter(
            'param_file').get_parameter_value().string_value
        param_path_ = self.get_parameter(
            'param_path').get_parameter_value().string_value
        fs_list_ = self.get_parameter(
            'fs_list').get_parameter_value().integer_array_value
        itf_list_ = self.get_parameter(
            'itf_list').get_parameter_value().double_array_value
        serial_no_ = self.get_parameter(
            'serial_no').get_parameter_value().string_value
        location_ = self.get_parameter(
            'location').get_parameter_value().string_value

        self.frame_id = self.get_parameter(
            'frame_id').get_parameter_value().string_value

        self.get_logger().info('Param: debug = {}'.format(debug_))
        self.get_logger().info('Param: timer = {}'.format(timer_))
        self.get_logger().info('Param: frequency = {}'.format(frequency_))
        self.get_logger().info('Param: init_zero = {}'.format(init_zero_))
        self.get_logger().info('Param: set_fs = {}'.format(set_fs_))
        self.get_logger().info('Param: set_itf = {}'.format(set_itf_))
        self.get_logger().info('Param: timeout = {}'.format(timeout_))
        self.get_logger().info('Param: param_file = {}'.format(param_file_))
        self.get_logger().info('Param: param_path = {}'.format(param_path_))
        self.get_logger().info('Param: fs_list = {}'.format(list(fs_list_)))
        self.get_logger().info('Param: itf_list = {}'.format(list(itf_list_)))
        self.get_logger().info('Param: serial_no = {}'.format(serial_no_))
        self.get_logger().info('Param: location = {}'.format(location_))
        self.get_logger().info('Param: frame_id = {}'.format(self.frame_id))

        self.add_on_set_parameters_callback(self.parameter_callback)

        # Construct DMA03DriverForRobot
        self.get_logger().info('Initializing DMA-03 for Robot Driver ...')
        self.driver = DMA03DriverForRobot(debug=debug_,
                                          frequency=frequency_,
                                          init_zero=init_zero_,
                                          timeout=timeout_,
                                          serial_number=serial_no_,
                                          location=location_)

        # Initialize DMA-03 for Robot Driver
        self.initialized = False
        if self.driver.is_connected():
            # Set FS from config yaml data
            if set_fs_:
                self.get_logger().info('Setting FS ...')
                result = self.driver.set_fs(fs_list_)
                if result:
                    self.get_logger().info('FS Set: OK {}'.format(list(fs_list_)))
                else:
                    self.get_logger().error('FS Set: NG!')

            # Set ITF from config yaml data
            if set_itf_:
                self.get_logger().info('Setting ITF ...')
                result = self.driver.set_itf(itf_list_)
                if result:
                    self.get_logger().info('ITF Set: OK {}'.format(list(itf_list_)))
                else:
                    self.get_logger().error('ITF Set: NG!')

            # Start sending data from DMA-03 for Robot Amplifire
            reply = self.driver.start()
            self.get_logger().info('START Reply: {}'.format(reply))

            self.publisher_ = self.create_publisher(
                Vector3Stamped, '~/force', 10)

            if 0.0 < timer_:
                # Timer Event
                self.get_logger().info(
                    'Publish Start! Timer: {} [sec]'.format(timer_))
                self.timer = self.create_timer(timer_, self.event_callback)
            else:
                # Override: _ros_publish() by event_callback()
                self.driver._ros_publish = self.event_callback
                self.get_logger().info('Data Driven Publish Start!')

            self.initialized = True

    def event_callback(self):
        """Publish ROS Topic.

        Returns:
            bool: True if executed.
        """
        msg = Vector3Stamped()
        data_time, eng1, eng2, eng3 = self.driver.get_data()
        sec_ = int(data_time)
        nanosec_ = int((data_time - sec_)*1e9)
        msg.header.frame_id = self.frame_id
        msg.header.stamp = Time(sec=sec_, nanosec=nanosec_)
        msg.vector.x = eng1
        msg.vector.y = eng2
        msg.vector.z = eng3
        self.publisher_.publish(msg)
        return True

    def parameter_callback(self, params):
        """Execute processes when a ROS Pamameter has changed.

        Args:
            params (list[Parameter]): List of ROS Parameter(s).

        Returns:
            SetParametersResult: Result of setting Parameter.
        """
        for param in params:
            if param.name == 'init_zero' and param.type_ == Parameter.Type.BOOL:
                self.get_logger().info('Param: {} changed to: {}'.format(param.name, param.value))
                if param.value:
                    self.get_logger().info('Send ZERO command and wait seconds ...')
                    reply = self.driver.set_zero()
                    self.get_logger().info('Set ZERO: {}'.format(reply))
            else:
                self.get_logger().warn('Param: {} has no reconfigure process.'.format(param.name))
        return SetParametersResult(successful=True)

    def cleanup(self):
        """Clean up when stopping the node."""
        self.get_logger().info('Node Cleaning Up')
        self.driver.close()
        self.destroy_node()


def main(args=None):
    """Execute ROS Node with DMA03Publisher."""
    rclpy.init(args=args)
    dma03_publisher = DMA03Publisher()

    if dma03_publisher.initialized:
        try:
            rclpy.spin(dma03_publisher)
        except KeyboardInterrupt:
            dma03_publisher.get_logger().info('KeyboardInterrupt Received')
        finally:
            dma03_publisher.cleanup()
            if rclpy.ok():
                rclpy.shutdown()
    else:
        dma03_publisher.get_logger().info('Not Initialized and Stop')
        dma03_publisher.cleanup()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
