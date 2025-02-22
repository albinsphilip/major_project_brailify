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
else:
    data = {}
    

# This will keep track of the current index in the list
current_index = 1  # Start at the end

# Function to save data to the JSON file
def save_data():
    with open(json_file_path, 'w') as file:
        json.dump(data, file, indent=4)

# Display the transcription from the current index
def preview_message():
    if current_index > 0 and data:
        message = data[f'{current_index}']
        message=f'{current_index} '+message[:min(len(message),6)]+".."
        message = re.sub(r'(\b\d+)', r'*\1*', message)
        print(f"Previewing Message at Index {current_index}: {message}")  # Preview the first 10 chars
        show_message(preview=message)
    else:
        show_message()


    
# Show full message from the current index
def show_message(index=0, preview="", delete=""):
    if current_index > 0 and data:  # Ensure there are messages to display
        # Retrieve the message
        if preview != "":
            message = preview
        elif delete != "":
            message = delete
        else:
            message = "#" + data[f'{index if index != 0 else current_index}']
            message = re.sub(r'(\b\d+)', r'*\1*', message)
            print(f"Showing Message at Index {index if index != 0 else current_index}: {message}")

        # Initialize buffer and other variables
        step = 4  # Number of characters to process at a time
        buffer_index = 0  # Start from the beginning

        # Start the interaction loop
        while True:
            # Get the current segment to display
            start_pos = buffer_index
            end_pos = min(buffer_index + step, len(message))

            # Generate the current segment and pad if necessary
            current_segment = message[start_pos:end_pos]
            if len(current_segment) < 4:
                current_segment += ";" * (4 - len(current_segment))

            # Flush the current segment to the device
            for char in current_segment:
                ser.write(char.encode())
                ser.flush()
                time.sleep(0.2)

            ser.write('\n'.encode())
            ser.flush()
            print(f"Flushed: {current_segment}")

            # Prompt user for the next action
            direction = input("Enter 'next' to show next 4 characters, 'prev' to show previous 4 characters, or 'exit' to stop: ").strip().lower()

            if direction == 'next':
                if buffer_index + step >= len(message):
                    print("End of message reached.")
                else:
                    buffer_index += step

            elif direction == 'prev':
                if buffer_index - step < 0:
                    print("Beginning of message reached.")
                else:
                    buffer_index -= step

            elif direction == 'exit':
                print("Exiting message view.")
                break

            else:
                print("Invalid input. Please enter 'next', 'prev', or 'exit'.")
    else:
        # When no messages are available
        message = "no messages available."
        print("No messages available to display.")

        # Start the interaction loop even if there is no actual message
        while True:
            # Flush the "No messages" content (padded to 4 chars) to the device
            current_segment = message[:4]
            if len(current_segment) < 4:
                current_segment += ";" * (4 - len(current_segment))

            for char in current_segment:
                ser.write(char.encode())
                ser.flush()
                time.sleep(0.2)

            ser.write('\n'.encode())
            ser.flush()
            print(f"Flushed: {current_segment}")

            # Prompt user for the next action
            direction = input("Enter 'next' to show next 4 characters, 'prev' to show previous 4 characters, or 'exit' to stop: ").strip().lower()

            if direction == 'next':
                print("No messages available to navigate.")
            
            elif direction == 'prev':
                print("No messages available to navigate.")
                
            elif direction == 'exit':
                print("Exiting message view.")
                break
            
            else:
                print("Invalid input. Please enter 'next', 'prev', or 'exit'.")


# Record new audio and save transcription
def record_and_save():
    process = subprocess.Popen(record_command, shell=True, preexec_fn=os.setsid)
    try:
        print("Recording started. Press Enter to stop...")
        input()  # Wait for the user to press Enter
        os.killpg(os.getpgid(process.pid), signal.SIGINT)  # Gracefully stop recording
        print("Recording stopped by user.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
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
        show_message(index= next_index)

def delete():
    global current_index, data
    if current_index > 0 and data:
        # Get the current message
        message = data.get(f'{current_index}', None)
        if not message:
            print("No message found at the current index.")
            return
        
        # Prepare preview with limited characters
        preview_message = f'd{current_index} ' + message[:min(len(message), 6)] + ".."
        preview_message = re.sub(r'(\b\d+)', r'*\1*', preview_message)  # Highlight index number
        show_message(delete=preview_message)
        
        # Ask for confirmation
        inp = input(f"Are you sure you want to delete Message at Index {current_index}: '{preview_message}'? Type 'yes' to proceed or 'no' to cancel: ").strip().lower()
        delete_message= f'd{current_index} ' + "deleted"
        
        if inp == "yes":
            # Perform deletion
            print(f"Message at Index {current_index} deleted.")
            show_message(delete=delete_message)

            # Delete the current index
            del data[f'{current_index}']

            if not data:  # If no keys exist after deletion
                print("No more messages left.")
                current_index = 0  # Reset the current index
                with open('data.json', 'w') as file:
                    json.dump(data, file, indent=4)
                return  # Exit the function

            # Renumber remaining keys if keys exist
            updated_data = {}
            new_index = 1
            for old_index in sorted(int(k) for k in data.keys()):  # Iterate over sorted numeric keys
                updated_data[str(new_index)] = data.pop(str(old_index))
                new_index += 1
            data = updated_data  # Assign the updated data back to the original variable

            # Update current_index to point to the previous valid index
            current_index = min(current_index - 1, len(data))

            # Update the JSON file (if persisting data)
            with open('data.json', 'w') as file:
                json.dump(data, file, indent=4)

            print("Data updated successfully.")

    else:
        show_message()
# Main loop to prompt user for actions
while True:
    command = input("\nEnter a command [record, up, down, preview, show,delete, exit]: ").strip().lower()

    if command == "record":
        record_and_save()

    elif command == "down":
        if current_index < len(data):
            current_index += 1
            print(f"Index {current_index}")
        else:
            print("You are at the latest message.")

    elif command == "up":
        if current_index > 1:
            current_index -= 1
            print(f"Index {current_index}")
        else:
            print("You are at the first message.")

    elif command == "preview":
        preview_message()
    
    elif command == "delete":
        delete()

    elif command == "show":
        show_message()
    elif command == "exit":
        print("Exiting program...")
        break

    else:
        print("Invalid command. Please try again.")
    
ser.close()
