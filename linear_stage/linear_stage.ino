# define stp 5
# define dir 6

float serial_read_delay = 1200;
float serial_write_delay = 1000;
unsigned long serial_read_time = millis();
unsigned long serial_write_time = millis();
unsigned long loop_time = millis();
bool system_available = True;

unsigned long step_time = micros();
unsigned long velocity_delay_micros = 1000;
int direction = 1;
long steps = 0;
long abs_pos = 0;



void setup() {
  pinMode(stp, OUTPUT);
  pinMode(dir, OUTPUT);
  Serial.begin(9600);
  reset_pins();
}

void loop() {
  loop_time = millis();
  //move_to_position();
  serial_read();
  serial_write();
  
  
}


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
    Serial.print(velocity_delay_micros);
  }
}


void categorize_cmd(String serial_string){
  int index_r = serial_string.indexOf("r\n");
  
  if (serial_string.startsWith("D")){
    int serial_direction = serial_string.substring(1, index_r).toInt();
    set_direction(serial_direction);
  }
  else if (serial_string.startsWith("V")){
    int serial_velocity = serial_string.substring(1, index_r).toInt();
    set_velocity(serial_velocity);
  }
  else if (serial_string.startsWith("S")){
    long serial_steps = atol(serial_string.substring(1, index_r).c_str());
    n_steps(serial_steps);
    set_steps(serial_steps);
  }
}


void set_direction(int serial_direction){
  if (serial_direction == 1){
    direction = serial_direction;
    digitalWrite(dir, HIGH);
    Serial.println("Direction was changed to 1");
  }
  else if (serial_direction == 0){
    direction = serial_direction;
    digitalWrite(dir, LOW);
    Serial.println("Direction was changed to 0");
  }
}

void set_velocity(int serial_velocity){
  velocity_delay_micros = serial_velocity;
}


void set_steps(long serial_steps){
  if (direction == 1){
    steps = serial_steps;
  }
  else{
    steps = -serial_steps;
  }
}


void move_to_position(){
  if (abs(steps) > 0){
    if ((unsigned long) (micros() - step_time) >= velocity_delay_micros){
      step_time = micros();
      single_step();
      if (direction == 1){
        abs_pos++;
        steps--;
      }
      else {
        abs_pos--;
        steps++;
      }
    }
  }
}


void n_steps(long n_steps) {
  for (int i=0; i<= n_steps; i++){
    single_step();
    delayMicroseconds(velocity_delay_micros);
  }
}

void single_step() {
  digitalWrite(stp, HIGH);
  delayMicroseconds(3);
  digitalWrite(stp, LOW);
}


void reset_pins()
{
  digitalWrite(stp, LOW);
  digitalWrite(dir, LOW);
}
