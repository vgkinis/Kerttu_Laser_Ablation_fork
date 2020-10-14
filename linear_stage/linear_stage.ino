# define stp 5
# define dir 6

float serial_read_delay = 1200;
unsigned long serial_time = millis();
unsigned long loop_time = millis();
unsigned long velocity_delay_micros;

int direction;
unsigned long steps;
unsigned long abs_pos;



void setup() {
  Serial.begin(9600);
}

void loop() {
  loop_time = millis();
  serial_read();
}


void serial_read(){
  String serial_string;
  if ((unsigned long)(loop_time - serial_time) >= serial_read_delay){
    serial_time = loop_time;
    if (Serial.available() > 0){
      serial_string = Serial.readString();
      if (serial_string.endsWith("r")) {
        categorize_cmd(serial_string);
      }
    }
  }
}


void categorize_cmd(serial_string){
  int index_r = serial_string.indexOf("r\n");
  
  if serial_string.startsWith("D"){
    set_direction(serial_string.substring(1, index_r);
  }
  else if serial_string.startsWith("V"){
    set_velocity(serial_string.substring(1, index_r);
  }
  else if serial_string.startsWith("S"){
  }
  else if serial_string.startsWith("P"){
  }
  else if serial_string.startsWith("R"){
    
  }


  
  int index_V = serial_string.indexOf("V");
  Serial.println(serial_string.substring(index_V+1, index_r));
}


void set_direction(){
  if (direction == 1){
    digitalWrite(dir, HIGH);
    Serial.println("Direction was changed to 1");
  }
  else if (direction == 0){
    digitalWrite(dir, LOW);
    Serial.println("Direction was changed to 0);
  }
}
