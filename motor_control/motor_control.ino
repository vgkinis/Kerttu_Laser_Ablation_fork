 //Declare pin functions on RedBoard
#define stp 2
#define dir 3 // LOW -> step forward, HIGH -> step in reverse

// stepper timing
unsigned long t_spd = 0;
int spd = 350; // microseconds
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
        PullDirPinLow();
        dir_forward = true;
      }
      else{
        PullDirPinHigh();
        dir_forward = false;
      }
    }
  }
  else{
    if ((unsigned long)(micros() - t_spd) > spd){
      if (stp_finished == true){
          PullStepPinHigh();
          stp_finished = false;
      }
      else{
          PullStepPinLow();
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


void PullStepPinHigh(){
  digitalWrite(stp, HIGH);
}

void PullStepPinLow(){
  digitalWrite(stp, LOW);
}

void PullDirPinHigh(){
  digitalWrite(dir, HIGH);
}

void PullDirPinLow(){
  digitalWrite(dir, LOW);
}


//Reset Easy Driver pins to default states
void resetEDPins()
{
  digitalWrite(stp, LOW);
  digitalWrite(dir, LOW);
}
