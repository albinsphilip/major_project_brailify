
#include <Stepper.h>
#define VRX A0
#define VRY A1
#define SW 53
const int stepsPerRevolution = 2048;
const int totalSegments = 32;
const int stepsPerSegment = stepsPerRevolution / totalSegments;

int prevSteps[5] = {0, 0, 0, 0, 0}; // Track previous segments for each stepper
char stepperBuffer[5] = {'\0', '\0', '\0', '\0', '\0'}; // Stepper character buffer
int bufferIndex = 0;                                    // Index for assigning characters
String inputMessage = "";                               // Buffer for received message

// Define steppers
Stepper myStepper1(stepsPerRevolution, 8, 10, 9, 11);
Stepper myStepper2(stepsPerRevolution, 22, 24, 23, 25);
Stepper myStepper3(stepsPerRevolution, 30, 32, 31, 35);
Stepper myStepper4(stepsPerRevolution, 38, 40, 39, 41);
Stepper myStepper5(stepsPerRevolution, 46, 48, 47, 49); // New stepper

void setup() {
  Serial.begin(9600);

  // Set speed for all steppers
  myStepper1.setSpeed(10);
  myStepper2.setSpeed(10);
  myStepper3.setSpeed(10);
  myStepper4.setSpeed(10);
  myStepper5.setSpeed(10); // Set speed for new stepper

  pinMode(SW, INPUT_PULLUP);
}

void loop() {
  while (Serial.available() > 0) {
    char receivedChar = Serial.read();
    if (receivedChar == 'R') {  // 'R' means Raspberry Pi requested data
      int xValue = analogRead(VRX);
      int yValue = analogRead(VRY);
      int button = digitalRead(SW);

      // Convert analog values to -1, 0, 1
      int xPos = (xValue > 700) ? 1 : (xValue < 300) ? -1 : 0;
      int yPos = (yValue > 700) ? 1 : (yValue < 300) ? -1 : 0;

      // Send values as a comma-separated string
      Serial.print("DATA:");  
      Serial.print(xPos);
      Serial.print(",");
      Serial.print(yPos);
      Serial.print(",");
      Serial.println(button);
    }
  
    // Handle the end of the message
    else if (receivedChar == '\n') {
      processMessage(inputMessage);
      inputMessage = ""; // Clear the input buffer for the next message
    } else {
      inputMessage += receivedChar; // Append characters to message buffer
    }
  }
}

void processMessage(String message) {
  int messageLength = message.length();

  // Process the message one group of 5 characters at a time
  for (int i = 0; i < messageLength; i++) {
    stepperBuffer[bufferIndex] = message[i]; // Assign the character
    bufferIndex++;

    // If the buffer is full, process all steppers
    if (bufferIndex == 5 || i == messageLength - 1) { // End of message triggers processing too
      moveSteppers();
      bufferIndex = 0;           // Reset buffer index
      for (int j = 0; j < 5; j++) {
        stepperBuffer[j] = '\0'; // Clear stepper buffer
      }
      delay(1000);               // Optional delay after processing each group
    }
  }
}
void disableSteppers() {
  digitalWrite(8, LOW); digitalWrite(9, LOW);
  digitalWrite(10, LOW); digitalWrite(11, LOW);

  digitalWrite(22, LOW); digitalWrite(23, LOW);
  digitalWrite(24, LOW); digitalWrite(25, LOW);

  digitalWrite(30, LOW); digitalWrite(31, LOW);
  digitalWrite(32, LOW); digitalWrite(33, LOW);

  digitalWrite(38, LOW); digitalWrite(39, LOW);
  digitalWrite(40, LOW); digitalWrite(41, LOW);

  digitalWrite(46, LOW); digitalWrite(47, LOW);
  digitalWrite(48, LOW); digitalWrite(49, LOW);
}
int mapCharToSegment(char c) {
  if (c >= 'a' && c <= 'z') {
    return c - 'a' + 1; // Map lowercase a-z -> segments 1-26
  } else if (c >= 'A' && c <= 'Z') {
    return c - 'A' + 1; // Map uppercase A-Z -> segments 1-26
  } else if (c == ' ') {
    return 27;          // Space -> segment 27
  } else if (c == '.') {
    return 28;          // Period -> segment 28
  } else if (c == ',') {
    return 29;  
  }// Comma -> segment 29
    else if (c== ';'){
      return 0;
  } else if (c== '#'){
      return 31;
  }else if (c >= '0' && c <= '9') {
        return c - '0' + 1; // Map digits '0'-'9' 
    }
  else if (c== '*'){
      return 30;
  }
  else {
    return -2;          // Invalid character
  }
}

void moveSteppers() {
  int targetSteps[5] = {0};

  // Calculate steps for each stepper
  for (int i = 0; i < 5; i++) {
    char c = stepperBuffer[i];
    if (c == '\0') continue; // Skip empty slots

    int segmentNumber = mapCharToSegment(c);

    if (segmentNumber == -2) continue; // Invalid character, ignore
    int targetSegment = segmentNumber - prevSteps[i];
    if (targetSegment >16){
      targetSteps[i] = (32-targetSegment) * stepsPerSegment;
    }
    else if(targetSegment <-16){
      targetSteps[i] = -(32+targetSegment) * stepsPerSegment;
    }
    else{
      targetSteps[i] = -(targetSegment) * stepsPerSegment;
    }
    prevSteps[i] = segmentNumber; // Update previous position
  }

  // Find maximum number of steps for simultaneous motion
  int maxSteps = max(abs(targetSteps[0]), max(abs(targetSteps[1]), max(abs(targetSteps[2]), max(abs(targetSteps[3]), abs(targetSteps[4])))));

  // Move steppers simultaneously
  for (int step = 0; step < maxSteps; step++) {
    if (step < abs(targetSteps[0])) myStepper1.step(targetSteps[0] > 0 ? 1 : -1);
    if (step < abs(targetSteps[1])) myStepper2.step(targetSteps[1] > 0 ? 1 : -1);
    if (step < abs(targetSteps[2])) myStepper3.step(targetSteps[2] > 0 ? 1 : -1);
    if (step < abs(targetSteps[3])) myStepper4.step(targetSteps[3] > 0 ? 1 : -1);
    if (step < abs(targetSteps[4])) myStepper5.step(targetSteps[4] > 0 ? 1 : -1); // New stepper

    delayMicroseconds(3000); // Adjust delay for step balance
  }
  disableSteppers();
}
