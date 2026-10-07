import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, GroupAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import SetRemap

def generate_launch_description():
    war_nav_dir = get_package_share_directory('war_navigation')
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')

    default_map = os.path.join(war_nav_dir, 'maps', 'warehouse_map.yaml')
    default_params = os.path.join(war_nav_dir, 'config', 'nav2_params.yaml')

    use_sim_time = LaunchConfiguration('use_sim_time')
    map_yaml = LaunchConfiguration('map')
    params_file = LaunchConfiguration('params_file')

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock'
    )
    declare_map = DeclareLaunchArgument(
        'map',
        default_value=default_map,
        description='Full path to map YAML'
    )
    declare_params = DeclareLaunchArgument(
        'params_file',
        default_value=default_params,
        description='Full path to Nav2 params'
    )

    bringup_cmd_group = GroupAction([
        SetRemap(src='/cmd_vel', dst='/diff_drive_controller/cmd_vel_unstamped'),
        SetRemap(src='cmd_vel', dst='/diff_drive_controller/cmd_vel_unstamped'),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(nav2_bringup_dir, 'launch', 'bringup_launch.py')
            ),
            launch_arguments={
                'map': map_yaml,
                'params_file': params_file,
                'use_sim_time': use_sim_time,
                'autostart': 'true'
            }.items()
        )
    ])

    rviz_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_bringup_dir, 'launch', 'rviz_launch.py')
        ),
        launch_arguments={
            'use_sim_time': use_sim_time
        }.items()
    )

    return LaunchDescription([
        declare_use_sim_time,
        declare_map,
        declare_params,
        bringup_cmd_group,
        rviz_cmd
    ])
