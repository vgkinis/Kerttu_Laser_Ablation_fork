//Declare pin functions on RedBoard
#define stp 5
#define dir 6 // LOW -> step forward, HIGH -> step in reverse

// Var from acc code
unsigned long prevStepMicros ;
unsigned long slowMicrosBetweenSteps = 4000; // microseconds
unsigned long fastMicrosBetweenSteps = 700;
unsigned long stepIntervalMicros;
unsigned long stepAdjustmentMicros;
long numAccelSteps = 200; // 100 is a half turn of a 200 step motor

// data acquisition timing
unsigned long t_loop = millis();
unsigned long t_data = millis();
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
  Serial.begin(250000);

  // Var from acc code
  stepAdjustmentMicros = (slowMicrosBetweenSteps - fastMicrosBetweenSteps) / numAccelSteps;
  stepIntervalMicros = slowMicrosBetweenSteps;
}

void loop() {
  t_loop = millis();
  
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
      prevStepMicros = micros();
    }
  }
  else{
    if ((unsigned long)(micros() - prevStepMicros) >=  stepIntervalMicros){
      prevStepMicros += stepIntervalMicros;
      singleStep();
      if (dir_forward == true){
        steps--;
        pos_steps++;
      }
      else{
        steps++;
        pos_steps--;
      }
      // If starting to stop
      if (abs(steps) <= numAccelSteps) {
        if (stepIntervalMicros < slowMicrosBetweenSteps) {
          stepIntervalMicros += stepAdjustmentMicros;
        }
      }
      // If starting to go
      else {
        if (stepIntervalMicros > fastMicrosBetweenSteps) {
          stepIntervalMicros -= stepAdjustmentMicros;
        }
      }
    }
  }
  if ((unsigned long)(t_loop - t_data) >= dt_data){
    t_data = t_loop;
    sendData();
  }
}


void singleStep() {
  digitalWrite(stp, HIGH);
  digitalWrite(stp, LOW);
}

void resetEDPins()
{
  digitalWrite(stp, LOW);
  digitalWrite(dir, LOW);
}

void sendData() {
  pos_mm = (thread_pitch*pos_steps)/steps_per_rot;
  Serial.print(t_loop);
  Serial.print(";");
  Serial.print(pos_mm);
  Serial.print(";");
  Serial.print(stepIntervalMicros);
}
