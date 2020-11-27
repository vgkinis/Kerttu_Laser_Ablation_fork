// Digital pins 5 and 6 are used for step and direction.
# define stp 5
# define dir 6
// Digital pins 2 and 3 are Arduino Uno attachInterrupt pins and are used for the two endstops.
#define end1 2
#define end2 3

float serial_read_delay = 1200;
float serial_write_delay = 1000;
unsigned long serial_read_time = millis();
unsigned long serial_write_time = millis();
unsigned long loop_time = millis();
bool system_available = true;
bool calibrating = false;
bool calib_endstop_reached = false;
long range_of_motion_stp = 0;

unsigned long step_time = micros();
unsigned long velocity1 = 1000;
unsigned long velocity_delay_micros = velocity1;
int direction = 1;
long abs_pos = 0;
long steps_to_do = 0;



void setup() {
  pinMode(stp, OUTPUT);
  pinMode(dir, OUTPUT);
  Serial.begin(9600);
  reset_pins();
  attachInterrupt(digitalPinToInterrupt(end1), detect_endstop1, RISING);
  //attachInterrupt(digitalPinToInterrupt(end2), detect_endstop2, RISING);
}

void loop() {
  loop_time = millis();
  serial_read();
  n_steps();
  serial_write();
  
  if (calib_endstop_reached == true){
    if (steps_to_do == 0){
      end_calibration();
    }
  }
}

// ---------------- Serial Functions ----------------

void serial_read(){
  String serial_string;
  if ((unsigned long)(loop_time - serial_read_time) >= serial_read_delay){
    serial_read_time = loop_time;
    if (Serial.available() > 0){
      serial_string = Serial.readString();
      if (serial_string.endsWith("r")) {
        categorize_cmd(serial_string);
      }
    }
  }
}


void serial_write(){
  if ((unsigned long)(loop_time - serial_write_time) >= serial_write_delay){
    serial_write_time = loop_time;
    Serial.print(loop_time);
    Serial.print(";");
    Serial.print(abs_pos);
    Serial.print(";");
    Serial.print(steps_to_do);
    Serial.print(";");
    Serial.print(velocity_delay_micros);
    Serial.print(";");
    Serial.print(direction);
  }
}


void categorize_cmd(String serial_string){
  int index_r = serial_string.indexOf("r\n");

  if (serial_string.startsWith("R")){
    reset_system();
  }
  else if (serial_string.startsWith("H")){
    pause_system();
  }
  else if (serial_string.startsWith("C")){
    // Can't start calibrating while motor is moving.
    if (steps_to_do == 0){
      range_of_motion_stp = atol(serial_string.substring(1, index_r).c_str());
      start_calibration();
    }
  }
  else if (serial_string.startsWith("D")){
    // Direction can't be changed while motor is moving.
    if (steps_to_do == 0){
      int serial_direction = serial_string.substring(1, index_r).toInt();
      set_direction(serial_direction);
    }
  }
  else if (serial_string.startsWith("V")){
    int serial_velocity = serial_string.substring(1, index_r).toInt();
    set_velocity(serial_velocity);
  }
  else if (serial_string.startsWith("S")){
    // Variable steps_to_do can't be changed while motor is moving.
    if (steps_to_do == 0) {
      long serial_steps = atol(serial_string.substring(1, index_r).c_str());
      set_steps_to_do(serial_steps);
    }
  }
}

// ---------------- Set Parameters ----------------

void set_direction(int new_direction){
  if (system_available == true){
    if (new_direction == 1){
      direction = new_direction;
      digitalWrite(dir, HIGH);
      //Serial.println("Direction was changed to 1");
    }
    else if (new_direction == -1){
      direction = new_direction;
      digitalWrite(dir, LOW);
      //Serial.println("Direction was changed to -1");
    }
  }
  else {
    Serial.println("System not available");
  }
}

void set_velocity(int new_velocity){
  velocity_delay_micros = new_velocity;
}

void set_steps_to_do(long new_steps){
  steps_to_do = new_steps;
}

// ---------------- Calibrate/Reset/Pause/Start ----------------

void start_calibration(){
  set_direction(1);
  set_velocity(250);
  calibrating = true;
  set_steps_to_do(range_of_motion_stp);
}

void end_calibration(){
  abs_pos = 0;
  set_velocity(velocity1);
  set_direction(1);
  calibrating = false; 
  calib_endstop_reached = false;
}

void reset_system(){
  //system_available = true;
  set_steps_to_do(0);
}

void pause_system(){
  system_available = false;
}

void start_system(){
  system_available = true;
}

// ---------------- Step Functions ----------------

void n_steps() {
  if (steps_to_do > 0){
    if ((unsigned long) (micros() - step_time) >= velocity_delay_micros){
      if (system_available == true){
        step_time = micros();
        single_step();
        steps_to_do--;
        abs_pos += direction;
      }
    }
  }
}

void single_step() {
  if (system_available == true){
    digitalWrite(stp, HIGH);
    delayMicroseconds(3);
    digitalWrite(stp, LOW);
  }
  else {
    Serial.println("System not available");
  }
}

// ---------------- Endstop Functions ----------------

void detect_endstop1() {
  reset_system();
  //if (digitalRead(end1) == LOW) {
  //  reset_system();
  //}
}


void detect_endstop2() {
  if (digitalRead(end2) == LOW) {
    if (calibrating == true && range_of_motion_stp != 0){
      set_steps_to_do(0);
      set_direction(-1);
      steps_to_do = long(range_of_motion_stp/2);
      calib_endstop_reached = true;
    }
    else {
      reset_system();
    }
  }
}

// ---------------- Reset Pins Function ----------------

void reset_pins()
{
  digitalWrite(stp, LOW);
  digitalWrite(dir, HIGH);
}
