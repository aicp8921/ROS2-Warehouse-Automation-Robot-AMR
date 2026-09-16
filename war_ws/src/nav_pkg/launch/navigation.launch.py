#!/usr/bin/env python3

import os

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    pkg_dir = get_package_share_directory(
        'navigation_pkg'
    )

    nav2_bringup_dir = get_package_share_directory(
        'nav2_bringup'
    )

    params_file = os.path.join(
        pkg_dir,
        'config',
        'nav2_params.yaml'
    )

    map_file = '/home/bbgbot3/maps/my_room_map.yaml'

    nav2_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                nav2_bringup_dir,
                'launch',
                'bringup_launch.py'
            )
        ),
        launch_arguments={
            'map': map_file,
            'params_file': params_file,
            'use_sim_time': 'False',
            'autostart': 'True',
        }.items()
    )

    return LaunchDescription([
        nav2_bringup
    ])#!/usr/bin/env python3

import os

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    pkg_dir = get_package_share_directory(
        'navigation_pkg'
    )

    nav2_bringup_dir = get_package_share_directory(
        'nav2_bringup'
    )

    params_file = os.path.join(
        pkg_dir,
        'config',
        'nav2_params.yaml'
    )

    map_file = '/home/bbgbot3/maps/my_room_map.yaml'

    nav2_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                nav2_bringup_dir,
                'launch',
                'bringup_launch.py'
            )
        ),
        launch_arguments={
            'map': map_file,
            'params_file': params_file,
            'use_sim_time': 'False',
            'autostart': 'True',
        }.items()
    )

    return LaunchDescription([
        nav2_bringup
    ])