 //Declare pin functions on RedBoard
#define stp 2
#define dir 3 // LOW -> step forward, HIGH -> step in reverse
long x; // counter for the stepping functions
unsigned long time_now = 0;
int spd = 350;
int steps_per_rot = 400;
int thread_pitch = 4;
long pos = 0; 
long steps = 0;
bool stp_finished = true;
bool dir_forward;

void setup() {
  pinMode(stp, OUTPUT);
  pinMode(dir, OUTPUT);
  resetEDPins(); //Set step, direction, microstep and enable pins to default states
  Serial.begin(9600);
}

void loop() {
  if (steps == 0){
    if (Serial.available() > 0) {
      long distance = Serial.parseInt();
      Serial.print(steps);
      steps = (distance/thread_pitch) * steps_per_rot;
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
    if ((unsigned long)(micros() - time_now) > spd){
      //Serial.print(micros()-time_now);
      if (stp_finished == true){
          PullStepPinHigh();
          stp_finished = false;
      }
      else{
          PullStepPinLow();
          stp_finished = true;
          if (dir_forward == true){
            steps--;
            pos++;
          }
          else{
            steps++;
            pos--;
          }
      }
      time_now = micros();
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
