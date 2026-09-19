import rclpy
from rclpy.node import Node
import time

from std_msgs.msg import Int32, Int32MultiArray
from std_srvs.srv import SetBool

class WarConveyorController(Node):
    def __init__(self):
        super().__init__('war_conveyor_controller')

        # Publisher to ESP32: 1 = Forward, -1 = Reverse, 0 = Stop
        self.cmd_pub = self.create_publisher(Int32, '/conveyor_cmd', 10)

        # Subscriber from ESP32: [entry_ir_state, exit_ir_state]
        # Active-LOW: 0 = Object Detected, 1 = Clear
        self.ir_sub = self.create_subscription(
            Int32MultiArray,
            '/conveyor_ir',
            self.ir_callback,
            10
        )

        # Service to trigger transfer:
        # data = True  -> LOAD sequence
        # data = False -> UNLOAD sequence
        self.srv = self.create_service(
            SetBool,
            '/trigger_conveyor',
            self.handle_conveyor_service
        )

        self.entry_ir = 1
        self.exit_ir = 1
        self.timeout_sec = 8.0  # Safety timeout in seconds

        self.get_logger().info('Project W.A.R. Conveyor Controller Initialized.')

    def ir_callback(self, msg: Int32MultiArray):
        if len(msg.data) >= 2:
            self.entry_ir = msg.data[0]
            self.exit_ir = msg.data[1]

    def set_conveyor_state(self, val: int):
        msg = Int32()
        msg.data = val
        self.cmd_pub.publish(msg)

    def handle_conveyor_service(self, request, response):
        load_mode = request.data
        mode_str = "LOADING" if load_mode else "UNLOADING"
        self.get_logger().info(f'Conveyor sequence triggered: {mode_str}')

        start_time = time.time()
        success = False

        if load_mode:
            # ── LOAD SEQUENCE ───────────────────────────────────────
            # Run belt forward until payload triggers entry IR sensor
            self.set_conveyor_state(1)

            while (time.time() - start_time) < self.timeout_sec:
                rclpy.spin_once(self, timeout_sec=0.05)
                # Detected payload entering the rover bed
                if self.entry_ir == 0:
                    time.sleep(0.3)  # Short roll to center the box
                    success = True
                    break

        else:
            # ── UNLOAD SEQUENCE ─────────────────────────────────────
            # Run belt forward/discharge until payload clears the exit IR
            self.set_conveyor_state(1)

            # First verify payload was present, then wait until clear
            while (time.time() - start_time) < self.timeout_sec:
                rclpy.spin_once(self, timeout_sec=0.05)
                if self.exit_ir == 1 and self.entry_ir == 1:
                    time.sleep(0.5)  # Allow package to clear onto station
                    success = True
                    break

        # Stop belt
        self.set_conveyor_state(0)

        if success:
            response.success = True
            response.message = f'{mode_str} sequence completed successfully.'
            self.get_logger().info(response.message)
        else:
            response.success = False
            response.message = f'{mode_str} timed out! Halting conveyor for safety.'
            self.get_logger().warn(response.message)

        return response

def main(args=None):
    rclpy.init(args=args)
    node = WarConveyorController()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()