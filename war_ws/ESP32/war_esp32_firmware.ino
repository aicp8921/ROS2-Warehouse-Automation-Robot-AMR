#include <Arduino.h>
#include <micro_ros_arduino.h>

#include <rcl/rcl.h>
#include <rcl/error_handling.h>
#include <rclc/rclc.h>
#include <rclc/executor.h>

#include <geometry_msgs/msg/twist.h>
#include <std_msgs/msg/int32.h>
#include <std_msgs/msg/int32_multi_array.h>
#include <ESP32Servo.h>

// ============================================================
// 1. PIN DEFINITIONS & SPECIFICATIONS
// ============================================================

// TB6612FNG Motor Driver Pins
#define L_IN1       18
#define L_IN2       19
#define L_ENA       21

#define R_IN1       22
#define R_IN2       23
#define R_ENB       25

#define STBY_PIN    5

// Quadrature Encoder Pins
#define L_ENC_A     32
#define L_ENC_B     33
#define R_ENC_A     26
#define R_ENC_B     27

// Conveyor Actuator & Optical Payload Sensors
#define SERVO_PIN   13
#define IR_ENTRY    14   // Front IR sensor
#define IR_EXIT     12   // Rear IR sensor

// Robot Physical Constants
#define WHEEL_TRACK  0.20   // Distance between wheels in meters (200 mm)
#define MAX_PWM      255

// ============================================================
// 2. GLOBALS & ROS ENTITIES
// ============================================================

volatile long leftCount  = 0;
volatile long rightCount = 0;

Servo conveyorServo;

// Micro-ROS Core Handles
rclc_support_t support;
rcl_allocator_t allocator;
rcl_node_t node;
rclc_executor_t executor;

// Subscribers
rcl_subscription_t cmd_vel_sub;
rcl_subscription_t conveyor_sub;
geometry_msgs__msg__Twist msg_cmd_vel;
std_msgs__msg__Int32 msg_conveyor_cmd;

// Publishers
rcl_publisher_t enc_pub;
rcl_publisher_t ir_pub;
std_msgs__msg__Int32MultiArray msg_enc;
std_msgs__msg__Int32MultiArray msg_ir;

int32_t enc_buffer[2];
int32_t ir_buffer[2];

// ============================================================
// 3. ENCODER INTERRUPTS (IRAM_ATTR for fast execution)
// ============================================================

void IRAM_ATTR leftISR() {
  if (digitalRead(L_ENC_B) == HIGH) leftCount++;
  else leftCount--;
}

void IRAM_ATTR rightISR() {
  if (digitalRead(R_ENC_B) == HIGH) rightCount--;
  else rightCount++;
}

// ============================================================
// 4. LOW-LEVEL MOTOR CONTROLLERS
// ============================================================

void setLeftMotor(int spd) {
  spd = constrain(spd, -MAX_PWM, MAX_PWM);
  if (spd > 0) {
    digitalWrite(L_IN1, LOW);
    digitalWrite(L_IN2, HIGH);
    ledcWrite(L_ENA, spd);
  } else if (spd < 0) {
    digitalWrite(L_IN1, HIGH);
    digitalWrite(L_IN2, LOW);
    ledcWrite(L_ENA, abs(spd));
  } else {
    digitalWrite(L_IN1, LOW);
    digitalWrite(L_IN2, LOW);
    ledcWrite(L_ENA, 0);
  }
}

void setRightMotor(int spd) {
  spd = constrain(spd, -MAX_PWM, MAX_PWM);
  if (spd > 0) {
    digitalWrite(R_IN1, HIGH);
    digitalWrite(R_IN2, LOW);
    ledcWrite(R_ENB, spd);
  } else if (spd < 0) {
    digitalWrite(R_IN1, LOW);
    digitalWrite(R_IN2, HIGH);
    ledcWrite(R_ENB, abs(spd));
  } else {
    digitalWrite(R_IN1, LOW);
    digitalWrite(R_IN2, LOW);
    ledcWrite(R_ENB, 0);
  }
}

// ============================================================
// 5. ROS 2 SUBSCRIPTION CALLBACKS
// ============================================================

// Receives standard linear.x and angular.z velocity commands from Nav2
void cmd_vel_callback(const void *msgin) {
  const geometry_msgs__msg__Twist *msg = (const geometry_msgs__msg__Twist *)msgin;

  float linear  = msg->linear.x;    // m/s
  float angular = msg->angular.z;   // rad/s

  // Differential drive kinematics: split linear/angular into left/right wheel speeds
  float v_l = linear - (angular * WHEEL_TRACK / 2.0);
  float v_r = linear + (angular * WHEEL_TRACK / 2.0);

  // Approximate PWM conversion (Tweak the multiplier 400.0 based on battery voltage & motor specs)
  int pwm_l = (int)(v_l * 400.0);
  int pwm_r = (int)(v_r * 400.0);

  setLeftMotor(pwm_l);
  setRightMotor(pwm_r);
}

// Controls the 360° Continuous Rotation Servo:
// 1 = Forward (Load), -1 = Reverse (Unload), 0 = Stop
void conveyor_callback(const void *msgin) {
  const std_msgs__msg__Int32 *msg = (const std_msgs__msg__Int32 *)msgin;
  int cmd = msg->data;

  if (cmd == 1) {
    conveyorServo.write(180); // Full speed forward
  } else if (cmd == -1) {
    conveyorServo.write(0);   // Full speed reverse
  } else {
    conveyorServo.write(90);  // 90 degrees pulse stops continuous servo
  }
}

// ============================================================
// 6. SETUP & INITIALIZATION
// ============================================================

void setup() {
  // Motor Pins
  pinMode(L_IN1, OUTPUT);
  pinMode(L_IN2, OUTPUT);
  pinMode(R_IN1, OUTPUT);
  pinMode(R_IN2, OUTPUT);
  pinMode(STBY_PIN, OUTPUT);
  digitalWrite(STBY_PIN, HIGH); // Enable TB6612 H-bridge

  // Attach PWM directly (Core 3.x API: 1kHz frequency, 8-bit resolution)
  ledcAttach(L_ENA, 1000, 8);
  ledcAttach(R_ENB, 1000, 8);

  // Encoder Inputs
  pinMode(L_ENC_A, INPUT_PULLUP);
  pinMode(L_ENC_B, INPUT_PULLUP);
  pinMode(R_ENC_A, INPUT_PULLUP);
  pinMode(R_ENC_B, INPUT_PULLUP);

  attachInterrupt(digitalPinToInterrupt(L_ENC_A), leftISR, RISING);
  attachInterrupt(digitalPinToInterrupt(R_ENC_A), rightISR, RISING);

  // Conveyor Sensors & Servo
  pinMode(IR_ENTRY, INPUT_PULLUP);
  pinMode(IR_EXIT, INPUT_PULLUP);
  conveyorServo.attach(SERVO_PIN);
  conveyorServo.write(90); // Idle / Stop

  // Micro-ROS Serial Transport Setup (115200 Baud over USB)
  set_microros_transports();
  delay(1000);

  allocator = rcl_get_default_allocator();
  rclc_support_init(&support, 0, NULL, &allocator);

  // Initialize ROS 2 Node
  rclc_node_init_default(&node, "war_base_controller", "", &support);

  // 1. Subscribe to /cmd_vel
  rclc_subscription_init_default(
    &cmd_vel_sub,
    &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(geometry_msgs, msg, Twist),
    "/cmd_vel"
  );

  // 2. Subscribe to /conveyor_cmd
  rclc_subscription_init_default(
    &conveyor_sub,
    &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int32),
    "/conveyor_cmd"
  );

  // 3. Publish /encoder_ticks
  rclc_publisher_init_default(
    &enc_pub,
    &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int32MultiArray),
    "/encoder_ticks"
  );

  // 4. Publish /conveyor_ir
  rclc_publisher_init_default(
    &ir_pub,
    &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int32MultiArray),
    "/conveyor_ir"
  );

  // Message Memory Buffers
  msg_enc.data.data = enc_buffer;
  msg_enc.data.size = 2;
  msg_enc.data.capacity = 2;

  msg_ir.data.data = ir_buffer;
  msg_ir.data.size = 2;
  msg_ir.data.capacity = 2;

  // Initialize Executor (for 2 subscribers)
  rclc_executor_init(&executor, &support.context, 2, &allocator);
  rclc_executor_add_subscription(&executor, &cmd_vel_sub, &msg_cmd_vel, &cmd_vel_callback, ON_NEW_DATA);
  rclc_executor_add_subscription(&executor, &conveyor_sub, &msg_conveyor_cmd, &conveyor_callback, ON_NEW_DATA);
}

// ============================================================
// 7. MAIN LOOP
// ============================================================

unsigned long last_pub_time = 0;

void loop() {
  // Spin executor to process /cmd_vel and /conveyor_cmd callbacks
  rclc_executor_spin_some(&executor, RCL_MS_TO_NS(10));

  // Publish telemetry at 20Hz (every 50ms)
  unsigned long now = millis();
  if (now - last_pub_time >= 50) {
    last_pub_time = now;

    // Publish Ticks: [Left, Right]
    msg_enc.data.data[0] = leftCount;
    msg_enc.data.data[1] = rightCount;
    rcl_publish(&enc_pub, &msg_enc, NULL);

    // Publish IR status: 0 = Obstacle Detected, 1 = Clear (typical Active-LOW IR modules)
    msg_ir.data.data[0] = digitalRead(IR_ENTRY);
    msg_ir.data.data[1] = digitalRead(IR_EXIT);
    rcl_publish(&ir_pub, &msg_ir, NULL);
  }
}