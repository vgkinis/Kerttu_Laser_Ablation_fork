// Digital pins 5 and 6 are used for step and direction.
# define stp 5
# define dir 6
// Digital pins 2 and 3 are Arduino Uno attachInterrupt pins and are used for the two endstops.
#define end1 2
#define end2 3

float serial_read_delay = 10;
unsigned long serial_read_time = millis();
unsigned long serial_write_time = millis();
unsigned long loop_time = millis();

int event_code = 0;

unsigned long step_time = micros();
unsigned long speed1 = 1000;
unsigned long speed_delay_micros = speed1;
int direction = 1;
long abs_pos = 0;
long steps_to_do = 0;



void setup() {
  pinMode(stp, OUTPUT);
  pinMode(dir, OUTPUT);
  Serial.begin(38400);
  reset_pins();
  attachInterrupt(digitalPinToInterrupt(end1), detect_endstop1, FALLING);
  attachInterrupt(digitalPinToInterrupt(end2), detect_endstop2, FALLING);
}

void loop() {
  loop_time = millis();
  serial_read();
  n_steps();
}

// ---------------- Serial Functions ----------------

void serial_read(){
  String serial_string;
  if ((unsigned long)(loop_time - serial_read_time) >= serial_read_delay){
    serial_read_time = loop_time;
    if (Serial.available() > 0){
      serial_string = Serial.readStringUntil('r');
      categorize_cmd(serial_string);
    }
  }
}




void categorize_cmd(String serial_string){

  if (serial_string.startsWith("R")){
    reset_steps();
  }
  else if (serial_string.startsWith("E")){
    // Set event_code
    int serial_event = serial_string.substring(1,-1).toInt();
    event_code = serial_event;
  }
  else if (serial_string.startsWith("D")){
    // Direction can't be changed while motor is moving.
    if (steps_to_do == 0){
      int serial_direction = serial_string.substring(1,-1).toInt();
      set_direction(serial_direction);
    }
  }
  else if (serial_string.startsWith("V")){
    // Set speed
    int serial_speed = serial_string.substring(1,-1).toInt();
    set_speed(serial_speed);
  }
  else if (serial_string.startsWith("S")){
    // Variable steps_to_do can't be changed while motor is moving.
    if (steps_to_do == 0) {
      long serial_steps = atol(serial_string.substring(1,-1).c_str());
      set_steps_to_do(serial_steps);
    }
  }
  else if (serial_string.startsWith("A")){
    // Set absolute position
    long serial_abs_pos = atol(serial_string.substring(1,-1).c_str());
    set_abs_pos(serial_abs_pos);
  }
  else if (serial_string.startsWith("W")){
    serial_write();
  }
}

// ---------------- Set Parameters ----------------

void set_direction(int new_direction){
  if (new_direction == 1){
    direction = new_direction;
    digitalWrite(dir, LOW);
  }
  else if (new_direction == -1){
    direction = new_direction;
    digitalWrite(dir, HIGH);
  }
}

void set_speed(int new_speed){
  speed_delay_micros = new_speed;
}

void set_steps_to_do(long new_steps){
  steps_to_do = new_steps;
}

void set_abs_pos(long new_abs_pos){
  abs_pos = new_abs_pos;
}


// ---------------- Step Functions ----------------

void n_steps() {
  if (steps_to_do > 0){
    if ((unsigned long) (micros() - step_time) >= speed_delay_micros){
      step_time = micros();
      single_step();
      steps_to_do--;
      abs_pos += direction;
    }
  }
}

void single_step() {
  digitalWrite(stp, HIGH);
  delayMicroseconds(3);
  digitalWrite(stp, LOW);
}

// ---------------- Endstop Functions ----------------

void detect_endstop1() {
  reset_steps();
  event_code = 1;
}


void detect_endstop2() {
  reset_steps();
  event_code = 2;
}

// ---------------------- Reset -----------------------

void reset_pins()
{
  digitalWrite(stp, LOW);
  digitalWrite(dir, LOW);
}


void reset_steps(){
  set_steps_to_do(0);
}


// ---------------------- Write to serial -----------------------
void serial_write(){
//  if ((unsigned long)(loop_time - serial_write_time) >= serial_write_delay){
//    serial_write_time = loop_time;
  Serial.print("s");
  Serial.print(loop_time);
  Serial.print(";");
  Serial.print(abs_pos);
  Serial.print(";");
  Serial.print(steps_to_do);
  Serial.print(";");
  Serial.print(speed_delay_micros);
  Serial.print(";");
  Serial.print(direction);
  Serial.print(";");
  Serial.print(event_code);
  Serial.print("r");
}
