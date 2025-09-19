from glob import glob

import os

from setuptools import find_packages, setup

package_name = 'tecgihan_driver'

setup(
    name=package_name,
    version='0.1.2',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
            glob(os.path.join('launch', '*launch.[pxy][yma]*'))),
        (os.path.join('share', package_name, 'launch'),
            glob(os.path.join('launch', '*.rviz'))),
        (os.path.join('share', package_name, 'debian'),
            glob(os.path.join('debian', 'udev'))),
        (os.path.join('share', package_name, 'config'),
            glob(os.path.join('config', '*.yaml'))),
        (os.path.join('share', package_name, 'urdf'),
            glob(os.path.join('urdf', '*.[ux][ra]*'))),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Shigeo Wakida',
    maintainer_email='s.wakida@tecgihan.co.jp',
    description='Linux and ROS driver software for Tec Gihan sensor amplifiers for robots',
    license='BSD',
    extras_require={
        'test': ['pytest'],
    },
    entry_points={
        'console_scripts': [
            'dma03_ros_publisher = tecgihan_driver.dma03_ros_publisher:main',
            'force_to_wrench = tecgihan_driver.force_to_wrench:main',
            'set_udev_rules = tecgihan_driver.set_udev_rules:main'
        ],
    },
)
