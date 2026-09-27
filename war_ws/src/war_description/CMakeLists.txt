cmake_minimum_required(VERSION 3.8)
project(war_description)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(urdf REQUIRED)
find_package(xacro REQUIRED)

# Install directories to share/war_description
install(
  DIRECTORY config launch rviz urdf worlds
  DESTINATION share/${PROJECT_NAME}
)

ament_package()