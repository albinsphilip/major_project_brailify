#include <Stepper.h>

const int stepsPerRevolution = 2048;
const int totalSegments = 32;
const int stepsPerSegment = stepsPerRevolution / totalSegments;

int prevSteps[4] = {0, 0, 0, 0}; // Tracks the previous segment for each stepper
char stepperBuffer[4] = {'\0', '\0', '\0', '\0'}; // Stepper character buffer
int bufferIndex = 0;                              // Index for assigning characters
String inputMessage = "";                         // Buffer for the received message

// Define steppers
Stepper myStepper1(stepsPerRevolution, 8, 10, 9, 11);
Stepper myStepper2(stepsPerRevolution, 22, 24, 23, 25);
Stepper myStepper3(stepsPerRevolution, 30, 32, 31, 33);
Stepper myStepper4(stepsPerRevolution, 38, 40, 39, 41);

void setup() {
  Serial.begin(9600);

  // Set speed for all steppers
  myStepper1.setSpeed(10);
  myStepper2.setSpeed(10);
  myStepper3.setSpeed(10);
  myStepper4.setSpeed(10);
}

void loop() {
  while (Serial.available() > 0) {
    char receivedChar = Serial.read();

    // Handle the end of the message
    if (receivedChar == '\n') {
      Serial.print("Full message received: ");
      Serial.println(inputMessage);

      processMessage(inputMessage);
      inputMessage = ""; // Clear the input buffer for the next message
    } else {
      inputMessage += receivedChar; // Append characters to message buffer
    }
  }
 
 }

void processMessage(String message) {
  int messageLength = message.length();

  // Process the message one group of 4 characters at a time
  for (int i = 0; i < messageLength; i++) {
    stepperBuffer[bufferIndex] = message[i]; // Assign the character
    bufferIndex++;

    // If the buffer is full, process all steppers
    if (bufferIndex == 4 || i == messageLength - 1) { // End of message triggers processing too
      moveSteppers();
      bufferIndex = 0;           // Reset buffer index
      for (int j = 0; j < 4; j++) {
        stepperBuffer[j] = '\0'; // Clear stepper buffer
      }
      delay(1000);               // Optional delay after processing each group
    }
  }
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
  } else {
    return -1;          // Invalid character
  }
}

void moveSteppers() {
  int targetSteps[4] = {0};

  // Calculate steps for each stepper
  for (int i = 0; i < 4; i++) {
    char c = stepperBuffer[i];
    if (c == '\0') continue; // Skip empty slots

    int segmentNumber = mapCharToSegment(c);

    if (segmentNumber == -1) {
      Serial.print("Stepper ");
      Serial.print(i + 1);
      Serial.println(": Invalid character");
      continue;
    }

    Serial.print("Stepper ");
    Serial.print(i + 1);
    Serial.print(": Moving to segment ");
    Serial.println(segmentNumber);

    targetSteps[i] = -(segmentNumber - prevSteps[i]) * stepsPerSegment;
    prevSteps[i] = segmentNumber; // Update previous position
  }

  // Find maximum number of steps for simultaneous motion
  int maxSteps = max(abs(targetSteps[0]), max(abs(targetSteps[1]), max(abs(targetSteps[2]), abs(targetSteps[3]))));

  // Move steppers simultaneously
  for (int step = 0; step < maxSteps; step++) {
    if (step < abs(targetSteps[0])) myStepper1.step(targetSteps[0] > 0 ? 1 : -1);
    if (step < abs(targetSteps[1])) myStepper2.step(targetSteps[1] > 0 ? 1 : -1);
    if (step < abs(targetSteps[2])) myStepper3.step(targetSteps[2] > 0 ? 1 : -1);
    if (step < abs(targetSteps[3])) myStepper4.step(targetSteps[3] > 0 ? 1 : -1);

    delayMicroseconds(3000); // Adjust delay for step balance
  }
}
