# ROS2-Warehouse-Automation-Robot-AMR (Project W.A.R.)

[![ROS 2](https://img.shields.io/badge/ROS_2-Humble-blue.svg)](https://docs.ros.org/en/humble/)
[![Hardware](https://img.shields.io/badge/MCU-ESP32-red.svg)](https://www.espressif.com/)
[![Sensor](https://img.shields.io/badge/LiDAR-YDLIDAR-brightgreen.svg)](https://www.ydlidar.com/)
[![Status](https://img.shields.io/badge/Status-In_Development-yellow.svg)](#)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An Autonomous Mobile Robot (AMR) engineered for indoor warehouse logistics and automated material transfer. Project W.A.R. features a differential drive chassis with closed-loop ESP32 motor control, YDLIDAR-based 2D SLAM mapping, Nav2 autonomous navigation, and an integrated top-mounted conveyor mechanism for cargo handling.

> **Status:** Active development. Core base drivers, URDF kinematics, odometry publisher, and ESP32 low-level firmware have been committed and integrated.

---

## Repository Structure

```text
ROS2-Warehouse-Automation-Robot-AMR/
└── war_ws/
    ├── ESP32/
    │   └── war_esp32_firmware.ino    # ESP32 low-level motor driver, encoder logic & serial interface
    └── src/
        ├── nav_pkg/                  # Nav2 launch files, costmap configurations, and parameters
        ├── robot_description/        # URDF/Xacro models, physical dimensions, and visual meshes
        ├── war_base/                 # Base controller, odom_publisher.py, and serial communication
        └── ydlidar_ros2_driver/      # Driver node for 2D YDLIDAR sensor integration
