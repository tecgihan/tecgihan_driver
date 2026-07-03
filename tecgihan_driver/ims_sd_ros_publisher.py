import math

from builtin_interfaces.msg import Time
from rcl_interfaces.msg import SetParametersResult
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import BatteryState, Imu, MagneticField, Temperature

from tecgihan_driver.ims_sd_driver import IMSSDDriverForRobot


class IMSSDPublisher(Node):
    """ROS Publisher for IMS-SD.

    Published topics:
        ~/imu         (sensor_msgs/Imu)
            linear acceleration [m/s^2] and angular velocity [rad/s]
        ~/mag         (sensor_msgs/MagneticField)
            magnetic field [T]
        ~/temperature (sensor_msgs/Temperature)
            temperature [degC]
        ~/battery     (sensor_msgs/BatteryState)
            battery state of charge
    """

    def __init__(self):
        """Construct IMSSDPublisher."""
        super().__init__('ims_sd_publisher')

        # Declare ROS parameters
        self.declare_parameter('debug', False)
        self.declare_parameter('timer', -0.01)
        self.declare_parameter('frequency', 100)
        self.declare_parameter('acc_range', 30)
        self.declare_parameter('timeout', 1.0)
        self.declare_parameter('port', '')
        self.declare_parameter('serial_no', '')
        self.declare_parameter('location', '')
        self.declare_parameter('frame_id', 'imu_sensor')

        # Read parameters
        debug_ = self.get_parameter(
            'debug').get_parameter_value().bool_value
        timer_ = self.get_parameter(
            'timer').get_parameter_value().double_value
        frequency_ = self.get_parameter(
            'frequency').get_parameter_value().integer_value
        acc_range_ = self.get_parameter(
            'acc_range').get_parameter_value().integer_value
        timeout_ = self.get_parameter(
            'timeout').get_parameter_value().double_value
        port_ = self.get_parameter(
            'port').get_parameter_value().string_value
        serial_no_ = self.get_parameter(
            'serial_no').get_parameter_value().string_value
        location_ = self.get_parameter(
            'location').get_parameter_value().string_value
        self.frame_id = self.get_parameter(
            'frame_id').get_parameter_value().string_value

        self.get_logger().info('Param: debug     = {}'.format(debug_))
        self.get_logger().info('Param: timer     = {}'.format(timer_))
        self.get_logger().info('Param: frequency = {}'.format(frequency_))
        self.get_logger().info('Param: acc_range = {}G'.format(acc_range_))
        self.get_logger().info('Param: timeout   = {}'.format(timeout_))
        self.get_logger().info('Param: port      = {}'.format(port_))
        self.get_logger().info('Param: serial_no = {}'.format(serial_no_))
        self.get_logger().info('Param: location  = {}'.format(location_))
        self.get_logger().info('Param: frame_id  = {}'.format(self.frame_id))

        self.add_on_set_parameters_callback(self.parameter_callback)

        # Construct the driver
        self.get_logger().info('Initializing IMS-SD for Robot Driver ...')
        self.driver = IMSSDDriverForRobot(
            debug=debug_,
            frequency=frequency_,
            acc_range=acc_range_,
            timeout=timeout_,
            port=port_ if port_ != '' else None,
            serial_number=serial_no_ if serial_no_ != '' else None,
            location=location_ if location_ != '' else None)

        self.initialized = False
        if not self.driver.is_connected():
            self.get_logger().error('IMS-SD: Not connected.')
            return

        # Create publishers
        self.pub_imu = self.create_publisher(Imu, '~/imu', 10)
        self.pub_mag = self.create_publisher(MagneticField, '~/mag', 10)
        self.pub_temp = self.create_publisher(Temperature, '~/temperature', 10)
        self.pub_bat = self.create_publisher(BatteryState, '~/battery', 10)

        # Start data acquisition
        reply = self.driver.start()
        self.get_logger().info('START Reply: {}'.format(reply))

        if 0.0 < timer_:
            # Timer-driven publish
            self.get_logger().info(
                'Publish Start! Timer: {} [sec]'.format(timer_))
            self.timer = self.create_timer(timer_, self.event_callback)
        else:
            # Data-driven publish: override _ros_publish in the driver
            self.driver._ros_publish = self.event_callback
            self.get_logger().info('Data Driven Publish Start!')

        self.initialized = True

    def event_callback(self):
        """Build and publish all ROS topics from the latest sensor data.

        Returns:
            bool: True when executed.
        """
        if not rclpy.ok():
            return False

        data_time, acc, gyro, mag, temp, soc = self.driver.get_data()

        sec_ = int(data_time)
        nanosec_ = int((data_time - sec_) * 1e9)
        stamp = Time(sec=sec_, nanosec=nanosec_)

        # ---- sensor_msgs/Imu ----
        # linear_acceleration  : [G] -> [m/s²]  (1 G = 9.80665 m/s²)
        # angular_velocity     : [deg/s] -> [rad/s]
        # orientation          : not provided by IMS-SD -> orientation_covariance[0] = -1
        # linear_acceleration_covariance / angular_velocity_covariance:
        #   all zeros (default) = covariance unknown
        G = 9.80665
        imu_msg = Imu()
        imu_msg.header.stamp = stamp
        imu_msg.header.frame_id = self.frame_id
        imu_msg.linear_acceleration.x = acc[0] * G
        imu_msg.linear_acceleration.y = acc[1] * G
        imu_msg.linear_acceleration.z = acc[2] * G
        imu_msg.angular_velocity.x = math.radians(gyro[0])
        imu_msg.angular_velocity.y = math.radians(gyro[1])
        imu_msg.angular_velocity.z = math.radians(gyro[2])
        imu_msg.orientation_covariance[0] = -1.0
        self.pub_imu.publish(imu_msg)

        # ---- sensor_msgs/MagneticField ----
        # [uT] -> [T]  (1 uT = 1e-6 T)
        mag_msg = MagneticField()
        mag_msg.header.stamp = stamp
        mag_msg.header.frame_id = self.frame_id
        mag_msg.magnetic_field.x = mag[0] * 1e-6
        mag_msg.magnetic_field.y = mag[1] * 1e-6
        mag_msg.magnetic_field.z = mag[2] * 1e-6
        self.pub_mag.publish(mag_msg)

        # ---- sensor_msgs/Temperature ----
        temp_msg = Temperature()
        temp_msg.header.stamp = stamp
        temp_msg.header.frame_id = self.frame_id
        temp_msg.temperature = temp  # [degC]
        temp_msg.variance = 0.0
        self.pub_temp.publish(temp_msg)

        # ---- sensor_msgs/BatteryState ----
        # percentage: 0.0 (0 %) - 1.0 (100 %)
        bat_msg = BatteryState()
        bat_msg.header.stamp = stamp
        bat_msg.header.frame_id = self.frame_id
        bat_msg.percentage = float(soc) / 100.0
        bat_msg.power_supply_status = BatteryState.POWER_SUPPLY_STATUS_UNKNOWN
        bat_msg.present = True
        self.pub_bat.publish(bat_msg)

        return True

    def parameter_callback(self, params):
        """Handle dynamic ROS parameter changes.

        Args:
            params (list[Parameter]): Changed parameters.

        Returns:
            SetParametersResult: Always successful.
        """
        for param in params:
            self.get_logger().warn(
                'Param: {} has no reconfigure process.'.format(param.name))
        return SetParametersResult(successful=True)

    def cleanup(self):
        """Stop and clean up the node."""
        self.get_logger().info('Node Cleaning Up')
        self.driver.close()
        self.destroy_node()


def main(args=None):
    """Launch the IMS-SD ROS publisher node."""
    rclpy.init(args=args)
    publisher = IMSSDPublisher()

    if publisher.initialized:
        try:
            rclpy.spin(publisher)
        except KeyboardInterrupt:
            publisher.get_logger().info('KeyboardInterrupt Received')
        finally:
            publisher.cleanup()
            if rclpy.ok():
                rclpy.shutdown()
    else:
        publisher.get_logger().info('Not Initialized and Stop')
        publisher.cleanup()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
