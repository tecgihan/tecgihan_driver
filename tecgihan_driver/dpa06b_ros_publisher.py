import sys

from builtin_interfaces.msg import Time
from geometry_msgs.msg import Vector3Stamped, WrenchStamped
from rcl_interfaces.msg import SetParametersResult

import rclpy

from rclpy.node import Node
from rclpy.parameter import Parameter

from tecgihan_driver.dpa06b_driver import DPA06BDriverForRobot


# Built-in default ITF coefficients (identity matrix, i.e. "no correction").
# Used both as declare_parameter() defaults and, at write time, to detect
# a likely sensor_mode / param_file mismatch (see _warn_if_still_default).
DEFAULT_ITF_3AXIS_LIST = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
DEFAULT_ITF_6AXIS_LIST = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                          0.0, 1.0, 0.0, 0.0, 0.0, 0.0,
                          0.0, 0.0, 1.0, 0.0, 0.0, 0.0,
                          0.0, 0.0, 0.0, 1.0, 0.0, 0.0,
                          0.0, 0.0, 0.0, 0.0, 1.0, 0.0,
                          0.0, 0.0, 0.0, 0.0, 0.0, 1.0]


class DPA06BPublisher(Node):
    """ROS Publisher for DPA-06B amplifier.

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
    """

    def __init__(self):
        """Construct DPA06BPublisher."""
        super().__init__('dpa06b_publisher')

        # ROS Parameters
        self.declare_parameter('debug', False)
        self.declare_parameter('timer', -0.01)
        self.declare_parameter('frequency', 1000)
        self.declare_parameter('init_zero', False)
        self.declare_parameter('set_fs', False)
        self.declare_parameter('set_itf_3axis_sensor1', False)  # 3axis mode: sensor 1
        self.declare_parameter('set_itf_3axis_sensor2', False)  # 3axis mode: sensor 2
        self.declare_parameter('set_itf_6axis', False)          # 6axis mode
        self.declare_parameter('timeout', 1.0)
        self.declare_parameter('param_file', 'UL100901.yaml')
        self.declare_parameter('param_path', '')
        self.declare_parameter('sensor_mode', '3axis')  # '3axis' or '6axis'
        self.declare_parameter('fs_list', [1000, 1000, 1000, 1000, 1000, 1000])
        self.declare_parameter(
            'itf_3axis_sensor1_list', list(DEFAULT_ITF_3AXIS_LIST))
        self.declare_parameter(
            'itf_3axis_sensor2_list', list(DEFAULT_ITF_3AXIS_LIST))
        self.declare_parameter(
            'itf_6axis_list', list(DEFAULT_ITF_6AXIS_LIST))
        self.declare_parameter('serial_no', '')
        self.declare_parameter('location', '')
        # 3axis mode: separate frame per physical sensor.
        # 6axis mode: single sensor, single frame.
        self.declare_parameter('frame_id_sensor1', 'force_sensor1')
        self.declare_parameter('frame_id_sensor2', 'force_sensor2')
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
        set_itf_3axis_sensor1_ = self.get_parameter(
            'set_itf_3axis_sensor1').get_parameter_value().bool_value
        set_itf_3axis_sensor2_ = self.get_parameter(
            'set_itf_3axis_sensor2').get_parameter_value().bool_value
        set_itf_6axis_ = self.get_parameter(
            'set_itf_6axis').get_parameter_value().bool_value
        timeout_ = self.get_parameter(
            'timeout').get_parameter_value().double_value
        param_file_ = self.get_parameter(
            'param_file').get_parameter_value().string_value
        param_path_ = self.get_parameter(
            'param_path').get_parameter_value().string_value
        sensor_mode_ = self.get_parameter(
            'sensor_mode').get_parameter_value().string_value
        fs_list_ = self.get_parameter(
            'fs_list').get_parameter_value().integer_array_value
        itf_3axis_sensor1_list_ = self.get_parameter(
            'itf_3axis_sensor1_list').get_parameter_value().double_array_value
        itf_3axis_sensor2_list_ = self.get_parameter(
            'itf_3axis_sensor2_list').get_parameter_value().double_array_value
        itf_6axis_list_ = self.get_parameter(
            'itf_6axis_list').get_parameter_value().double_array_value
        serial_no_ = self.get_parameter(
            'serial_no').get_parameter_value().string_value
        location_ = self.get_parameter(
            'location').get_parameter_value().string_value

        self.frame_id = self.get_parameter(
            'frame_id').get_parameter_value().string_value
        self.frame_id_sensor1 = self.get_parameter(
            'frame_id_sensor1').get_parameter_value().string_value
        self.frame_id_sensor2 = self.get_parameter(
            'frame_id_sensor2').get_parameter_value().string_value

        self.get_logger().info('Param: debug = {}'.format(debug_))
        self.get_logger().info('Param: timer = {}'.format(timer_))
        self.get_logger().info('Param: frequency = {}'.format(frequency_))
        self.get_logger().info('Param: init_zero = {}'.format(init_zero_))
        self.get_logger().info('Param: set_fs = {}'.format(set_fs_))
        self.get_logger().info('Param: sensor_mode = {}'.format(sensor_mode_))
        self.get_logger().info('Param: set_itf_3axis_sensor1 = {}'.format(set_itf_3axis_sensor1_))
        self.get_logger().info('Param: set_itf_3axis_sensor2 = {}'.format(set_itf_3axis_sensor2_))
        self.get_logger().info('Param: set_itf_6axis = {}'.format(set_itf_6axis_))
        self.get_logger().info('Param: timeout = {}'.format(timeout_))
        self.get_logger().info('Param: param_file = {}'.format(param_file_))
        self.get_logger().info('Param: param_path = {}'.format(param_path_))
        self.get_logger().info('Param: fs_list = {}'.format(list(fs_list_)))
        self.get_logger().info(
            'Param: itf_3axis_sensor1_list = {}'.format(list(itf_3axis_sensor1_list_)))
        self.get_logger().info(
            'Param: itf_3axis_sensor2_list = {}'.format(list(itf_3axis_sensor2_list_)))
        self.get_logger().info('Param: itf_6axis_list = {}'.format(list(itf_6axis_list_)))
        self.get_logger().info('Param: serial_no = {}'.format(serial_no_))
        self.get_logger().info('Param: location = {}'.format(location_))
        self.get_logger().info('Param: frame_id = {}'.format(self.frame_id))
        self.get_logger().info(
            'Param: frame_id_sensor1 = {}'.format(self.frame_id_sensor1))
        self.get_logger().info(
            'Param: frame_id_sensor2 = {}'.format(self.frame_id_sensor2))

        self.add_on_set_parameters_callback(self.parameter_callback)

        # Construct DPA06BDriverForRobot
        self.get_logger().info('Initializing DPA-06B Driver ...')
        self.driver = DPA06BDriverForRobot(debug=debug_,
                                           frequency=frequency_,
                                           init_zero=init_zero_,
                                           timeout=timeout_,
                                           serial_number=serial_no_,
                                           location=location_,
                                           sensor_mode=sensor_mode_)
        self._sensor_mode = sensor_mode_

        # Initialize DPA-06B Driver
        self.initialized = False
        if self.driver.is_connected():
            # Set FS
            if set_fs_:
                self.get_logger().info('Setting FS ...')
                result = self.driver.set_fs(fs_list_)
                if result:
                    self.get_logger().info('FS Set: OK {}'.format(list(fs_list_)))
                else:
                    self.get_logger().error('FS Set: NG!')

            if self._sensor_mode == '3axis':
                if set_itf_6axis_:
                    self.get_logger().warn(
                        "Param: 'set_itf_6axis' is true but sensor_mode is "
                        "'3axis'; it has no effect and will be ignored.")
                # Set ITF (3axis sensor1)
                if set_itf_3axis_sensor1_:
                    self._warn_if_still_default(
                        'itf_3axis_sensor1_list', itf_3axis_sensor1_list_,
                        DEFAULT_ITF_3AXIS_LIST)
                    self.get_logger().info('Setting ITF (3axis sensor1) ...')
                    result = self.driver.set_itf_3axis_sensor1(itf_3axis_sensor1_list_)
                    if result:
                        self.get_logger().info(
                            'ITF (3axis sensor1) Set: OK {}'.format(list(itf_3axis_sensor1_list_)))
                    else:
                        self.get_logger().error('ITF (3axis sensor1) Set: NG!')
                # Set ITF (3axis sensor2)
                if set_itf_3axis_sensor2_:
                    self._warn_if_still_default(
                        'itf_3axis_sensor2_list', itf_3axis_sensor2_list_,
                        DEFAULT_ITF_3AXIS_LIST)
                    self.get_logger().info('Setting ITF (3axis sensor2) ...')
                    result = self.driver.set_itf_3axis_sensor2(itf_3axis_sensor2_list_)
                    if result:
                        self.get_logger().info(
                            'ITF (3axis sensor2) Set: OK {}'.format(list(itf_3axis_sensor2_list_)))
                    else:
                        self.get_logger().error('ITF (3axis sensor2) Set: NG!')
            else:
                if set_itf_3axis_sensor1_ or set_itf_3axis_sensor2_:
                    self.get_logger().warn(
                        "Param: 'set_itf_3axis_sensor1'/'set_itf_3axis_sensor2' "
                        "is true but sensor_mode is '6axis'; it has no effect "
                        'and will be ignored.')
                # Set ITF (6axis)
                if set_itf_6axis_:
                    self._warn_if_still_default(
                        'itf_6axis_list', itf_6axis_list_, DEFAULT_ITF_6AXIS_LIST)
                    self.get_logger().info('Setting ITF (6axis) ...')
                    result = self.driver.set_itf_6axis(itf_6axis_list_)
                    if result:
                        self.get_logger().info(
                            'ITF (6axis) Set: OK {}'.format(list(itf_6axis_list_)))
                    else:
                        self.get_logger().error('ITF (6axis) Set: NG!')

            # Start sending data
            reply = self.driver.start()
            self.get_logger().info('START Reply: {}'.format(reply))

            # Create publishers based on sensor_mode
            if self._sensor_mode == '3axis':
                # Two Vector3Stamped topics: one per sensor
                self.publisher_sensor1_ = self.create_publisher(
                    Vector3Stamped, '~/force1', 10)
                self.publisher_sensor2_ = self.create_publisher(
                    Vector3Stamped, '~/force2', 10)
                self.get_logger().info(
                    'Topics: ~/force1 (sensor1), ~/force2 (sensor2)')
            else:
                # One WrenchStamped topic for 6-axis sensor
                self.publisher_ = self.create_publisher(
                    WrenchStamped, '~/wrench', 10)
                self.get_logger().info('Topic: ~/wrench (6-axis)')

            if 0.0 < timer_:
                self.get_logger().info(
                    'Publish Start! Timer: {} [sec]'.format(timer_))
                self.timer = self.create_timer(timer_, self.event_callback)
            else:
                self.driver._ros_publish = self.event_callback
                self.get_logger().info('Data Driven Publish Start!')

            self.initialized = True

    def _warn_if_still_default(self, param_name, value_list, default_list):
        """Warn if a coefficient parameter still equals its built-in default.

        A write is about to happen (the matching set_itf_* flag is true),
        but if the parameter value still equals the built-in identity-
        matrix default, the loaded YAML file (param_file/param_path)
        most likely does not define this key for the current sensor_mode,
        so this default would be written to the amplifier by mistake
        instead of the sensor's real ITF coefficients.

        Args:
            param_name (str): ROS parameter name, used in the warning message.
            value_list (Sequence[float]): Value currently held by the parameter.
            default_list (list[float]): Built-in default value to compare against.

        Returns:
            bool: True if a warning was logged, False otherwise.
        """
        if list(value_list) == default_list:
            self.get_logger().warn(
                "Param: '{}' still matches the built-in identity-matrix "
                'default. If you intended to load custom ITF coefficients, '
                "check that '{}' is defined in your param_file/param_path "
                'YAML for the current sensor_mode ({}).'.format(
                    param_name, param_name, self._sensor_mode))
            return True
        return False

    def event_callback(self):
        """Publish ROS Topic(s).

        3axis mode: publishes ~/force1 and ~/force2 (Vector3Stamped).
        6axis mode: publishes ~/wrench (WrenchStamped).

        Returns:
            bool: True if executed.
        """
        if self._sensor_mode == '3axis':
            # Sensor 1 (ch1-3)
            data_time, eng1, eng2, eng3 = self.driver.get_data_3axis_sensor1()
            sec_ = int(data_time)
            nanosec_ = int((data_time - sec_) * 1e9)

            msg1 = Vector3Stamped()
            msg1.header.frame_id = self.frame_id_sensor1
            msg1.header.stamp = Time(sec=sec_, nanosec=nanosec_)
            msg1.vector.x = eng1
            msg1.vector.y = eng2
            msg1.vector.z = eng3
            self.publisher_sensor1_.publish(msg1)

            # Sensor 2 (ch4-6)
            data_time, eng4, eng5, eng6 = self.driver.get_data_3axis_sensor2()
            sec_ = int(data_time)
            nanosec_ = int((data_time - sec_) * 1e9)

            msg2 = Vector3Stamped()
            msg2.header.frame_id = self.frame_id_sensor2
            msg2.header.stamp = Time(sec=sec_, nanosec=nanosec_)
            msg2.vector.x = eng4
            msg2.vector.y = eng5
            msg2.vector.z = eng6
            self.publisher_sensor2_.publish(msg2)

        else:
            # 6-axis sensor
            data_time, eng1, eng2, eng3, eng4, eng5, eng6 = self.driver.get_data()
            sec_ = int(data_time)
            nanosec_ = int((data_time - sec_) * 1e9)

            msg = WrenchStamped()
            msg.header.frame_id = self.frame_id
            msg.header.stamp = Time(sec=sec_, nanosec=nanosec_)
            msg.wrench.force.x = eng1
            msg.wrench.force.y = eng2
            msg.wrench.force.z = eng3
            msg.wrench.torque.x = eng4
            msg.wrench.torque.y = eng5
            msg.wrench.torque.z = eng6
            self.publisher_.publish(msg)

        return True

    def parameter_callback(self, params):
        """Execute processes when a ROS Parameter has changed.

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
    """Execute ROS Node with DPA06BPublisher."""
    # ros2 launch配下ではstdoutがttyでなくフルバッファリングになり、
    # driver.py内のprint()ログが遅延・順序崩れして出力されるため、
    # 行バッファリングに強制して即時出力させる。
    sys.stdout.reconfigure(line_buffering=True)

    rclpy.init(args=args)
    dpa06b_publisher = DPA06BPublisher()

    if dpa06b_publisher.initialized:
        try:
            rclpy.spin(dpa06b_publisher)
        except KeyboardInterrupt:
            dpa06b_publisher.get_logger().info('KeyboardInterrupt Received')
        finally:
            dpa06b_publisher.cleanup()
            if rclpy.ok():
                rclpy.shutdown()
    else:
        dpa06b_publisher.get_logger().info('Not Initialized and Stop')
        dpa06b_publisher.cleanup()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
