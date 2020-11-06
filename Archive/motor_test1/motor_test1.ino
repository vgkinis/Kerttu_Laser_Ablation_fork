//Declare pin functions on RedBoard
#define stp 5
#define dir 6 // LOW -> step forward, HIGH -> step in reverse

int analogPin = A2;


// counter, position, distance, direction

long steps = 0;
bool dir_forward;


void setup() {
  pinMode(stp, OUTPUT);
  pinMode(dir, OUTPUT);
  resetEDPins(); //Set step, direction, microstep and enable pins to default states
  Serial.begin(57600);
  steps = 8000;

}




void loop() {  
  if (steps > 0) {      
    singleStep();
    delayMicroseconds(1250/2);
    steps--;
    //Serial.println(analogRead(A2));
  }
}



void singleStep() {
  digitalWrite(stp, HIGH);
  delayMicroseconds(3);
  digitalWrite(stp, LOW);
}


void resetEDPins()
{
  digitalWrite(stp, LOW);
  digitalWrite(dir, LOW);
}
