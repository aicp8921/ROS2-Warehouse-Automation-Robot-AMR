import rclpy
from rclpy.node import Node
import math

from std_msgs.msg import Int32MultiArray
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped, Quaternion
from tf2_ros import TransformBroadcaster

def quaternion_from_euler(roll, pitch, yaw):
    cy = math.cos(yaw * 0.5)
    sy = math.sin(yaw * 0.5)
    cp = math.cos(pitch * 0.5)
    sp = math.sin(pitch * 0.5)
    cr = math.cos(roll * 0.5)
    sr = math.sin(roll * 0.5)

    q = Quaternion()
    q.w = cr * cp * cy + sr * sp * sy
    q.x = sr * cp * cy - cr * sp * sy
    q.y = cr * sp * cy + sr * cp * sy
    q.z = cr * cp * sy - sr * sp * cy
    return q

class WarBaseController(Node):
    def __init__(self):
        super().__init__('war_base_controller')

        # Robot kinematic parameters
        self.wheel_diameter = 0.065   # 65 mm
        self.wheel_track = 0.20       # 200 mm between wheels
        self.ticks_per_rev = 560.0    # PPR

        self.dist_per_tick = (math.pi * self.wheel_diameter) / self.ticks_per_rev

        # Pose state
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0

        # Encoder tick trackers
        self.prev_left_ticks = None
        self.prev_right_ticks = None
        self.prev_time = self.get_clock().now()

        # TF and Topic Broadcasters
        self.tf_broadcaster = TransformBroadcaster(self)
        self.odom_pub = self.create_publisher(Odometry, '/odom', 10)

        # Subscriber to ESP32 Micro-ROS
        self.enc_sub = self.create_subscription(
            Int32MultiArray,
            '/encoder_ticks',
            self.encoder_callback,
            10
        )
        self.get_logger().info('Project W.A.R. Base Controller Initialized.')

    def encoder_callback(self, msg: Int32MultiArray):
        current_time = self.get_clock().now()
        dt = (current_time - self.prev_time).nanoseconds / 1e9

        left_ticks = msg.data[0]
        right_ticks = msg.data[1]

        # First run initialization
        if self.prev_left_ticks is None:
            self.prev_left_ticks = left_ticks
            self.prev_right_ticks = right_ticks
            self.prev_time = current_time
            return

        delta_left = left_ticks - self.prev_left_ticks
        delta_right = right_ticks - self.prev_right_ticks

        self.prev_left_ticks = left_ticks
        self.prev_right_ticks = right_ticks
        self.prev_time = current_time

        # Distance moved by each wheel
        d_left = delta_left * self.dist_per_tick
        d_right = delta_right * self.dist_per_tick

        # Displacement and rotation
        delta_s = (d_right + d_left) / 2.0
        delta_theta = (d_right - d_left) / self.wheel_track

        # Update pose
        self.x += delta_s * math.cos(self.theta + (delta_theta / 2.0))
        self.y += delta_s * math.sin(self.theta + (delta_theta / 2.0))
        self.theta += delta_theta

        # Normalize theta to [-pi, pi]
        self.theta = math.atan2(math.sin(self.theta), math.cos(self.theta))

        # Calculate velocities
        v = delta_s / dt if dt > 0 else 0.0
        w = delta_theta / dt if dt > 0 else 0.0

        q = quaternion_from_euler(0, 0, self.theta)

        # 1. Publish odom -> base_link TF Transform
        t = TransformStamped()
        t.header.stamp = current_time.to_msg()
        t.header.frame_id = 'odom'
        t.child_frame_id = 'base_link'

        t.transform.translation.x = self.x
        t.transform.translation.y = self.y
        t.transform.translation.z = 0.0
        t.transform.rotation = q

        self.tf_broadcaster.sendTransform(t)

        # 2. Publish /odom Topic
        odom = Odometry()
        odom.header.stamp = current_time.to_msg()
        odom.header.frame_id = 'odom'
        odom.child_frame_id = 'base_link'

        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.position.z = 0.0
        odom.pose.pose.orientation = q

        odom.twist.twist.linear.x = v
        odom.twist.twist.angular.z = w

        self.odom_pub.publish(odom)

def main(args=None):
    rclpy.init(args=args)
    node = WarBaseController()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()