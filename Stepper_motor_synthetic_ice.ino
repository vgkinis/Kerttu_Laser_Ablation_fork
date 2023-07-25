# define spd 5
# define RES 2
# define spdMAX 3

void setup() {
  pinMode(spd,OUTPUT);
  pinMode(RES, INPUT);
  pinMode(spdMAX, INPUT);
  Serial.begin(9600);
}

//float speed = 0.0009 ; //define the speed run in mm/s
//float distrev = 0.1421 ; //distance per revoluion in mm/s : constant DATA
float steprev = 3200 ; //Step number per revolution : define with button on stepper motor
//unsigned int time = ((distrev*2)/(steprev*speed))*1000 ; //delay for the pulse signal in mseconds
float revpersec = 0.01;
unsigned int time=1e3/(revpersec*steprev*1); //ms.step
unsigned int quick_time = time/4;

void loop() {
  int resvalue=0; 
  resvalue = digitalRead(RES);
  //resvalue = analogRead(A0);
  //Serial.println(resvalue);

  int spdmaxvalue=0;
  spdmaxvalue = digitalRead(spdMAX);

  if(spdmaxvalue == LOW && resvalue == LOW){
    digitalWrite(spd,HIGH);
    delay(time);
    digitalWrite(spd,LOW);
   }
  else if (spdmaxvalue == HIGH && resvalue ==LOW) {
    digitalWrite(spd,HIGH);
    delayMicroseconds(quick_time);
    digitalWrite(spd,LOW);
  }
  else {
    digitalWrite(spd,LOW);
  }
}