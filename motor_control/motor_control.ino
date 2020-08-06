 //Declare pin functions on RedBoard
#define stp 2
#define dir 3

int x; // counter for the stepping functions

void setup() {
  pinMode(stp, OUTPUT);
  pinMode(dir, OUTPUT);
  resetEDPins(); //Set step, direction, microstep and enable pins to default states
  Serial.begin(9600);
}
void loop() {
  if(Serial.available() > 0) {
    //char data = Serial.read();
    //char str[2];
    //str[0] = data;
    //str[1] = '\0';
    //Serial.print(str);
    int steps = Serial.parseInt();
    Serial.print(steps);
    // If usr input is -steps then in reverse
    if(steps > 0){
      StepForwardDefault(steps);
    }
    else{
      ReverseStepDefault(abs(steps));
    }
  }
}

// Move forward
void StepForwardDefault(int steps)
{
  digitalWrite(dir, LOW); //Pull direction pin low to move "forward"
  for(x= 0; x<steps; x++)  //Loop the forward stepping enough times for motion to be visible
  {
    digitalWrite(stp,HIGH); //Trigger one step forward
    delayMicroseconds(350);
    digitalWrite(stp,LOW); //Pull step pin low so it can be triggered again
    delayMicroseconds(350);
  }
}

// Move reverse
void ReverseStepDefault(int steps)
{
  digitalWrite(dir, HIGH); //Pull direction pin high to move in "reverse"
  for(x= 0; x<steps; x++)  //Loop the stepping enough times for motion to be visible
  {
    digitalWrite(stp,HIGH); //Trigger one step
    delayMicroseconds(350);
    digitalWrite(stp,LOW); //Pull step pin low so it can be triggered again
    delayMicroseconds(350);
  }
}


//Reset Easy Driver pins to default states
void resetEDPins()
{
  digitalWrite(stp, LOW);
  digitalWrite(dir, LOW);
}
