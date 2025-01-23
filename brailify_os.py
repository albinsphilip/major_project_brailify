import os
import serial
import time
import subprocess
import assemblyai as aai
import json
import re
import signal


# Replace with your Assembly AI API key
aai.settings.api_key = "91ed4cffb8a54c9cba735a07447472c2"

# Set up the serial connection
ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
time.sleep(2)  # Wait for the serial connection to initialize

recording_file = 'recording.wav'
record_command = f'arecord -D hw:3,0 -f cd -c 1 -t wav {recording_file}'

# Define the JSON file path for transcription storage
json_file_path = 'transcriptions.json'

# A list to store messages (simulating a database of transcriptions)


# Load data if it exists
# Read the JSON file
if os.path.exists(json_file_path):
    with open(json_file_path, 'r') as file:
        data = json.load(file)
    

# This will keep track of the current index in the list
current_index = 1  # Start at the end

# Function to save data to the JSON file
def save_data():
    with open(json_file_path, 'w') as file:
        json.dump(data, file, indent=4)

# Display the transcription from the current index
def preview_message():
    if current_index > 0:
        message = data[f'{current_index}']
        print(f"Previewing Message at Index {current_index}: {message[:2]}..")  # Preview the first 10 chars
        for char in message:
            ser.write(char.encode())  # Send character
            ser.flush()
            time.sleep(0.2)           # Short delay before next character

# Send the terminator character to signal end of message
        ser.write('\n'.encode())
        ser.flush()
        print("Message sent!")
    else:
        print("No messages available to preview.")

# Show full message from the current index
def show_message():
    if current_index > 0:
        # Retrieve the message
        message = data[f'{current_index}']
        print(f"Showing Message at Index {current_index}: {message}")

        # Initialize buffer and other variables
        step = 4  # Number of characters to process at a time
        buffer_index = 0  # Start from the beginning
        displayed_segments = []  # Store each segment displayed

        # Show the first 4 characters, append ';;' if fewer than 4 characters
        end_pos = min(step, len(message))
        current_segment = message[buffer_index:end_pos]

        # If the current segment is less than 4 characters, append ';;'
        if len(current_segment) < 4:
            current_segment += ";;"[:(4 - len(current_segment))]

        displayed_segments.append(current_segment)
        
        # Flush the first segment of characters
        for char in current_segment:
            ser.write(char.encode())  # Send character
            ser.flush()
            time.sleep(0.2)  # Short delay before next character
        
        ser.write('\n'.encode())  # End of message
        ser.flush()
        print(f"First 4 chars flushed: {current_segment}")

        # Update buffer index after displaying the first segment
        buffer_index += len(current_segment)
        
        while True:
            direction = input("Enter 'next' to show next 4 characters, 'prev' to show previous 4 characters, or 'exit' to stop: ").strip().lower()

            if direction == 'next':
                # Display next 4 characters, append ';;' if fewer than 4 characters
                start_pos = buffer_index
                end_pos = min(start_pos + step, len(message))
                if start_pos >= len(message):
                    print("End of message reached.")
                    break  # Stop if there's no more content to display

                current_segment = message[start_pos:end_pos]
                
                # If the current segment is less than 4 characters, append ';;'
                if len(current_segment) < 4:
                    current_segment += ";;"[:(4 - len(current_segment))]
                
                displayed_segments.append(current_segment)  # Add to displayed segments
                
                # Flush the next segment of characters
                for char in current_segment:
                    ser.write(char.encode())  # Send character
                    ser.flush()
                    time.sleep(0.2)  # Short delay before next character
                
                ser.write('\n'.encode())  # End of message
                ser.flush()
                print(f"Next 4 chars flushed: {current_segment}")

                buffer_index = end_pos  # Update buffer index after the next segment is shown

            elif direction == 'prev':
                # Display previous 4 characters
                if len(displayed_segments) > 1:
                    previous_segment = displayed_segments[-2]  # Get the last shown segment before the current one
                    
                    # Flush previous segment of characters
                    for char in previous_segment:
                        ser.write(char.encode())  # Send character
                        ser.flush()
                        time.sleep(0.2)  # Short delay before next character
                    
                    ser.write('\n'.encode())  # End of message
                    ser.flush()
                    print(f"Previous 4 chars flushed: {previous_segment}")
                    
                    # Update buffer index after displaying the previous segment
                    buffer_index -= len(previous_segment)
                    displayed_segments.pop()  # Remove the current displayed segment from history
                else:
                    print("Beginning of message reached.")
                    break  # Stop if there's no more content to go back to

            elif direction == 'exit':
                print("Exiting message view.")
                break  # Exit if user wants to stop the process

            else:
                print("Invalid input. Please enter 'next', 'prev', or 'exit'.")
    else:
        print("No messages available to display.")



# Record new audio and save transcription
def record_and_save():
    print("Recording audio... Press Ctrl+C to stop.")
    process = subprocess.Popen(record_command, shell=True, preexec_fn=os.setsid)

    try:
        process.wait()
    except KeyboardInterrupt:
        os.killpg(os.getpgid(process.pid), signal.SIGINT)  # Gracefully stop recording
        print("Recording interrupted by user.")
    
    print("Recording finished. Transcribing audio...")

    # Transcribe the recorded audio
    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(recording_file)

    if transcript.status == aai.TranscriptStatus.error:
        print("Error in transcription:", transcript.error)
    else:
        processed_text = transcript.text.lower()
        processed_text = re.sub(r'[^a-z0-9,. ]+', '', processed_text)

        # Add to the data (messages)
        next_index = len(data) + 1
        data[f'{next_index}'] = processed_text
        save_data()  # Save the updated data to the file

        print(f"Transcription added to {json_file_path} with index: {next_index}")
        print(f"Transcription: {processed_text}")

        # Send transcription via serial
        print("Sending transcription to Arduino...")
        for char in processed_text:
            ser.write(char.encode())
            ser.flush()
            time.sleep(0.2)  # Adjust delay as needed
        ser.write('\n'.encode())  # End of message

# Main loop to prompt user for actions
while True:
    command = input("\nEnter a command [record, up, down, preview, show, confirm, exit]: ").strip().lower()

    if command == "record":
        record_and_save()

    elif command == "up":
        if current_index < len(data) - 1:
            current_index += 1
            print(f"Index {current_index}")
        else:
            print("You are at the latest message.")

    elif command == "down":
        if current_index > 1:
            current_index -= 1
            print(f"Index {current_index}")
        else:
            print("You are at the first message.")

    elif command == "preview":
        preview_message()

    elif command == "show":
        show_message()

    elif command == "exit":
        print("Exiting program...")
        break

    else:
        print("Invalid command. Please try again.")
    
ser.close()
