import serial
import time
import json

# Replace with your serial port (e.g., '/dev/ttyACM0' or '/dev/ttyUSB0')
ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
time.sleep(2)  # Wait for the serial connection to initialize

# Read the JSON file
with open('transcriptions.json', 'r') as file:
    data = json.load(file)

mykey=input("Enter the key of the text: ")
# Extract the value
myvalue = data[mykey]  # Assuming the transcription is stored directly at the first key

# Send each character of the first value to the Arduino
for char in myvalue:
    ser.write(char.encode())
    ser.flush()
    time.sleep(0.2)  # Wait for 3 seconds before sending the next character

ser.close()
