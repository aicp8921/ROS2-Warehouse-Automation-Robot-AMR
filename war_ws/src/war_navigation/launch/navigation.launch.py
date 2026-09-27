import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    war_nav_dir = get_package_share_directory('war_navigation')
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')

    default_map = os.path.join(war_nav_dir, 'maps', 'warehouse_map.yaml')
    default_params = os.path.join(war_nav_dir, 'config', 'nav2_params.yaml')

    map_arg = DeclareLaunchArgument('map', default_value=default_map, description='Full path to map YAML')
    params_arg = DeclareLaunchArgument('params_file', default_value=default_params, description='Full path to Nav2 params')

    nav2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(nav2_bringup_dir, 'launch', 'bringup_launch.py')),
        launch_arguments={
            'map': LaunchConfiguration('map'),
            'params_file': LaunchConfiguration('params_file'),
            'use_sim_time': 'false'
        }.items()
    )

    return LaunchDescription([
        map_arg,
        params_arg,
        nav2_launch
    ])
