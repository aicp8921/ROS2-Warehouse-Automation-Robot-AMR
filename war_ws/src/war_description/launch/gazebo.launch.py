import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command
from launch_ros.actions import Node

def generate_launch_description():
    pkg_share = get_package_share_directory('war_description')
    pkg_gazebo_ros = get_package_share_directory('gazebo_ros')

    xacro_file = os.path.join(pkg_share, 'urdf', 'robot.urdf.xacro')

    world = os.path.join(
        get_package_share_directory("war_description"), 
        "worlds",
        "my_world.world"
        ) 

    # 1. Start Gazebo Server & Client (empty world or warehouse world)
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, 'launch', 'gazebo.launch.py')
        ),
 
    launch_arguments={
        "world": world
    }.items(),)

    # 2. Robot State Publisher (publishes /robot_description with use_sim_time)
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': Command(['xacro ', xacro_file]),
            'use_sim_time': True
        }]
    )

    # 3. Spawn the Robot Entity in Gazebo
    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=['-topic', 'robot_description', '-entity', 'war_robot', '-z', '0.05'],
        output='screen'
    )

    # 4. ros2_control Spawners
    joint_broad_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster'],
        output='screen'
    )

    diff_drive_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['diff_drive_controller'],
        output='screen'
    )

    # Sequence: Load diff_drive after joint_state_broadcaster is initialized
    delayed_diff_drive_spawner = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=joint_broad_spawner,
            on_exit=[diff_drive_spawner],
        )
    )

    return LaunchDescription([
        gazebo,
        robot_state_publisher,
        spawn_entity,
        joint_broad_spawner,
        delayed_diff_drive_spawner
    ])
