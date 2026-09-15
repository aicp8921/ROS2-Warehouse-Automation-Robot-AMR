import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
import xacro


def generate_launch_description():

    pkg_path = get_package_share_directory("robot_description")
    urdf_dir = os.path.join(pkg_path, "urdf")
    xacro_file = os.path.join(urdf_dir, "robot.urdf.xacro")

    # 1. Evaluate Xacro with search_paths set to resolve relative includes (e.g. ./properties.xacro)
    with open(xacro_file, "r") as xacro_file_handle:
        doc = xacro.parse(xacro_file_handle)
    xacro.process_doc(doc, search_paths=[urdf_dir])
    robot_description_config = doc.toxml()

    # Shared parameters across nodes
    params = {
        "robot_description": robot_description_config,
        "use_sim_time": True,
    }

    world = os.path.join(
    get_package_share_directory("robot_description"), 
    "worlds",
    "my_world.world"
    )  
      
    # 2. Standard Gazebo launch inclusion
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("gazebo_ros"),
                "launch",
                "gazebo.launch.py",
            )
        ),
    launch_arguments={
        "world": world
    }.items(),)

    # 3. Robot State Publisher
    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[params],
    )

    # 4. Spawning the robot into Gazebo
    spawn_robot = Node(
        package="gazebo_ros",
        executable="spawn_entity.py",
        arguments=[
            "-topic", "robot_description",
            "-entity", "my_first_robot",
        ],
        output="screen",
    )

    # 5. Spawning the Joint State Broadcaster
    joint_state_broadcaster = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster"],
        parameters=[{"use_sim_time": True}],
        output="screen",
    )

    # 6. Spawning the Diff Drive Controller
    diff_drive_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["diff_drive_controller"],
        parameters=[{"use_sim_time": True}],
        output="screen",
    )

    # 7. Sequential Event Handlers (Ensures Gazebo -> Spawn -> Broadcaster -> Controller)
    delay_joint_state_broadcaster = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=spawn_robot,
            on_exit=[joint_state_broadcaster],
        )
    )

    delay_diff_drive_controller = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=joint_state_broadcaster,
            on_exit=[diff_drive_controller],
        )
    )

    # 8. Teleop keyboard mapped to diff drive controller
    teleop_keyboard = Node(
        package="teleop_twist_keyboard",
        executable="teleop_twist_keyboard",
        output="screen",
        prefix="xterm -e",
        parameters=[{"use_sim_time": True}],
        remappings=[
            ("/cmd_vel", "/diff_drive_controller/cmd_vel_unstamped")
        ],
    )

    return LaunchDescription([
        gazebo,
        robot_state_publisher,
        spawn_robot,
        delay_joint_state_broadcaster,
        delay_diff_drive_controller,
        teleop_keyboard,
    ])