//Declare pin functions on RedBoard
#define stp 5
#define dir 6 // LOW -> step forward, HIGH -> step in reverse

// stepper timing
//unsigned long t_acc = 0;
unsigned long t_spd = 0;
//int current_spd;
int spd = 5000; // microseconds
bool stp_finished = true;

// data acquisition timing
unsigned long t_data = 0;
int dt_data = 1000; // time interval in milliseconds

// parameters of the mechanics
int steps_per_rot = 400;
int thread_pitch = 4;

// counter, position, distance, direction
long x;
long pos_steps = 0; 
long pos_mm = 0;
long steps = 0;
bool dir_forward;



void setup() {
  pinMode(stp, OUTPUT);
  pinMode(dir, OUTPUT);
  resetEDPins(); //Set step, direction, microstep and enable pins to default states
  Serial.begin(9600);
}

void loop() {
  if ((unsigned long)(millis() - t_data) > dt_data){
    pos_mm = (thread_pitch*pos_steps)/steps_per_rot;
    Serial.print(pos_mm);
    t_data = millis();
  }
  if (steps == 0){
    if (Serial.available() > 0) {
      long distance = Serial.parseInt();
      steps = (distance * steps_per_rot)/thread_pitch; 
      if (steps > 0){
        digitalWrite(dir, LOW);
        dir_forward = true;
      }
      else{
        digitalWrite(dir, HIGH);
        dir_forward = false;
      }
    }
  }
  else{
    if ((unsigned long)(micros() - t_spd) >  spd){
      if (stp_finished == true){
          digitalWrite(stp, HIGH);
          stp_finished = false;
          }
      else{
          digitalWrite(stp, LOW);
          stp_finished = true;
          if (dir_forward == true){
            steps--;
            pos_steps++;
            }
          else{
            steps++;
            pos_steps--;
            }
          }
      t_spd = micros();
      }
    }
  }



//Reset Easy Driver pins to default states
void resetEDPins()
{
  digitalWrite(stp, LOW);
  digitalWrite(dir, LOW);
}
