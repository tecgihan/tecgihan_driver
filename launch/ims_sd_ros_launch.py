from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            name='debug',
            default_value='false',
            description='bool'),
        DeclareLaunchArgument(
            name='timer',
            default_value='-0.01',
            description='double'),
        DeclareLaunchArgument(
            name='frequency',
            default_value='100',
            description='int'),
        DeclareLaunchArgument(
            name='acc_range',
            default_value='30',
            description='int'),
        DeclareLaunchArgument(
            name='timeout',
            default_value='1.0',
            description='double'),
        DeclareLaunchArgument(
            name='serial_no',
            default_value='',
            description='string'),
        DeclareLaunchArgument(
            name='location',
            default_value='',
            description='string'),
        DeclareLaunchArgument(
            name='frame_id',
            default_value='imu_sensor',
            description='string'),
        DeclareLaunchArgument(
            name='node_name',
            default_value='ims_sd_publisher',
            description='string'),
        Node(
            package='tecgihan_driver',
            executable='ims_sd_ros_publisher',
            name=LaunchConfiguration('node_name'),
            output='screen',
            parameters=[
                {'debug':     LaunchConfiguration('debug')},
                {'timer':     LaunchConfiguration('timer')},
                {'frequency': LaunchConfiguration('frequency')},
                {'acc_range': LaunchConfiguration('acc_range')},
                {'timeout':   LaunchConfiguration('timeout')},
                {'serial_no': LaunchConfiguration('serial_no')},
                {'location':  LaunchConfiguration('location')},
                {'frame_id':  LaunchConfiguration('frame_id')},
            ]
        )
    ])
