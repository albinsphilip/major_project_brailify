import os
import serial
import time
import subprocess
import assemblyai as aai
import json
import re
import signal
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError, NetworkError
import asyncio
import emoji
import pytz

import RPi.GPIO as GPIO


BUTTON_RECORD = 22
BUTTON_BACK = 23
BUTTON_TELEGRAM = 24
BUTTON_DELETE = 25

VIBRATION_MOTOR_PIN = 17
BUZZER_PIN = 27


GPIO.setmode(GPIO.BCM)  # Use Broadcom pin numbering
GPIO.setup(BUTTON_RECORD, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUTTON_BACK, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUTTON_TELEGRAM, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUTTON_DELETE, GPIO.IN, pull_up_down=GPIO.PUD_UP)

GPIO.setup(VIBRATION_MOTOR_PIN, GPIO.OUT)
GPIO.setup(BUZZER_PIN, GPIO.OUT)

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


API_TOKEN = '8161151599:AAHzydhxiawbOg_VrkfwHZI7R2EXstVN5cY'

# Path to JSON file
TELEGRAM_JSON_FILE = "telegram.json"

# Define IST timezone
IST = pytz.timezone("Asia/Kolkata")

show_value=""

SAVE_FILE = "stepper_positions.txt"

order = [';', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j',
         'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 
         'v', 'w', 'x', 'y', 'z', ' ', '.', ',', '*', '#']

def save_positions(positions):
    with open(SAVE_FILE, "w") as f:
        f.write(positions)
        
        
def load_positions():
    try:
        with open(SAVE_FILE, "r") as f:
            return f.read()
    except FileNotFoundError:
        return ';;;;;'  # Default positions

def activate_vibration(duration=0.5):
    """Activates the vibration motor for the given duration (default: 0.5s)."""
    GPIO.output(VIBRATION_MOTOR_PIN, GPIO.HIGH)
    time.sleep(duration)
    GPIO.output(VIBRATION_MOTOR_PIN, GPIO.LOW)

def activate_buzzer(duration=0.5):
    """Activates the buzzer for the given duration (default: 0.5s)."""
    GPIO.output(BUZZER_PIN, GPIO.HIGH)
    time.sleep(duration)
    GPIO.output(BUZZER_PIN, GPIO.LOW)

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
def show_message(index=0, preview="", delete="",telegram=""):
    activate_vibration(0.5)
    global show_value
    if current_index > 0 and data or delete or telegram:  # Ensure there are messages to display
        # Retrieve the message
        if preview != "":
            message = preview
        elif delete != "":
            message = delete
        elif telegram != "":
            message = telegram
        else:
            message = "#" + data[f'{index if index != 0 else current_index}']
            message = re.sub(r'(\b\d+)', r'*\1*', message)
            print(f"Showing Message at Index {index if index != 0 else current_index}: {message}")

        # Initialize buffer and other variables
        step = 5  # Number of characters to process at a time
        buffer_index = 0  # Start from the beginning

        # Start the interaction loop
        while True:
            prev_x, prev_y, prev_button = 0, 0, 1

            time.sleep(0.01)  # Prevent CPU overload

            # Get the current segment to display
            start_pos = buffer_index
            end_pos = min(buffer_index + step, len(message))

            # Generate the current segment and pad if necessary
            current_segment = message[start_pos:end_pos]
            if len(current_segment) < 5:
                current_segment += ";" * (5 - len(current_segment))

            # Flush the current segment to the device
            r=''
            msg=current_segment
            save_positions(msg)
            for i,j in zip(msg,load):
                r+=order[order.index(i)-order.index(j)]
            
            for char in r:
                ser.write(char.encode())
                ser.flush()
                time.sleep(0.2)
            ser.write('\n'.encode())
            ser.flush()
            ser.reset_input_buffer()
            ser.reset_output_buffer()
            print(f"Flushed: {current_segment}")
            
            try:
                while True:
                    ser.write(b'R')  # Send request to Arduino
                    data1 = ser.readline().decode().strip()  # Read response
                    current_back_state = GPIO.input(BUTTON_BACK)
                    if data1.startswith("DATA:") and data1.count(",") == 2:
                        x, y, button = map(int, data1.split(":")[1].split(","))
                        if (x, y, button) != (prev_x, prev_y, prev_button):
                            print(f"X: {x}, Y: {y}, Button: {button}")
                            prev_x, prev_y, prev_button = x, y, button                
                            break
                    if  current_back_state != prev_back_state :
                        break  # Exit loop if any button changed
                    time.sleep(0.01)
            except:
                print("Cannot read")

            if prev_y==-1:
                activate_buzzer(0.1)
                if buffer_index + step >= len(message):
                    print("End of message reached.")
                else:
                    buffer_index += step

            elif prev_y==1:
                activate_buzzer(0.1)
                if buffer_index - step < 0:
                    print("Beginning of message reached.")
                else:
                    buffer_index -= step
            elif prev_button == 0:
                activate_buzzer(0.1)
                show_value='ok'
                break
            elif current_back_state == GPIO.LOW and prev_back_state == GPIO.HIGH:
                activate_buzzer(0.1)
                show_value = 'exit'
                print("Exiting message view.")
                break

            else:
                print("Invalid input. Please enter 'next', 'prev', or 'exit'.")
    else:
        # When no messages are available
        message = "nomsg"
        print("No messages available to display.")

        # Start the interaction loop even if there is no actual message
        while True:
            prev_x, prev_y, prev_button = 0, 0, 1
            # Flush the "No messages" content (padded to 4 chars) to the device
            current_segment = message[:5]
            if len(current_segment) < 5:
                current_segment += ";" * (5 - len(current_segment))

            r=''
            msg=current_segment
            save_positions(msg)
            
            for i,j in zip(msg,load):
                r+=order[order.index(i)-order.index(j)]
            
            for char in r:
                ser.write(char.encode())
                ser.flush()
                time.sleep(0.2)
            ser.write('\n'.encode())
            ser.flush()
            ser.reset_input_buffer()
            ser.reset_output_buffer()
            
            print(f"Flushed: {current_segment}")

            try:
                while True:
                    ser.write(b'R')  # Send request to Arduino
                    data1 = ser.readline().decode().strip()  # Read response
                    current_back_state = GPIO.input(BUTTON_BACK)
                    if data1.startswith("DATA:") and data1.count(",") == 2:
                        x, y, button = map(int, data1.split(":")[1].split(","))
                        if (x, y, button) != (prev_x, prev_y, prev_button):
                            print(f"X: {x}, Y: {y}, Button: {button}")
                            prev_x, prev_y, prev_button = x, y, button                
                            break
                    if  current_back_state != prev_back_state :
                        break  # Exit loop if any button changed
                    time.sleep(0.01)
            except:
                print("Cannot read")
            if prev_y==-1:
                
                print("No messages available to navigate.")
            
            elif prev_y==1:
               
                print("No messages available to navigate.")
                
            elif GPIO.input(BUTTON_BACK) == GPIO.LOW:
                activate_buzzer(0.1)
                print("Exiting message view.")
                break
            
            else:
                print("Invalid input. Please enter 'next', 'prev', or 'exit'.")


# Record new audio and save transcription
def record_and_save():
    
    print("Recording started...")
    process = subprocess.Popen(record_command, shell=True, preexec_fn=os.setsid)

    try:
        print("Recording started.Release button to stop...")
        # Wait for button release
        while GPIO.input(BUTTON_RECORD) == GPIO.LOW:
            
            time.sleep(0.01)  # Small delay to prevent CPU overuse

        # Button released ? Stop recording
        os.killpg(os.getpgid(process.pid), signal.SIGINT)  
        activate_buzzer(0.1)
        print("Recording stopped.")

    except Exception as e:
        print(f"An error occurred: {e}")
        

    finally:
        print("Recording finished. Transcribing audio...")

    # Transcribe the recorded audio
    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(recording_file)

    if transcript.status == aai.TranscriptStatus.error:
        activate_vibration(0.5)
        print("Error in transcription:", transcript.error)
        return
        
        
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
        show_message(index=next_index)
        
        
        
def delete():
    activate_buzzer(0.1)
    global current_index, data,show_value
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
        if show_value=='exit':
            show_value=''
            return
        else:
            show_value=''
        
        delete_message= f'd{current_index} ' + "deleted"
        

        # Perform deletion
        print(f"Message at Index {current_index} deleted.")
        show_message(delete=delete_message)
            
        # Delete the current index
        del data[f'{current_index}']
        
        if not data:  # If no keys exist after deletion
            print("No more messages left.")
            current_index = 0  # Reset the current index
            with open('data.json', 'w') as file:
                json.dump(data, file, indent=5)
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
        with open('transcriptions.json', 'w') as file:
            json.dump(data, file, indent=5)

        print("Data updated successfully.")

    else:
        show_message()
# Main loop to prompt user for actions



def load_json_file(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            return json.load(file)
    return {}


# Utility to save JSON data
def save_json_file(data, file_path):
    with open(file_path, "w") as file:
        json.dump(data, file, indent=5)


# Fetch and update messages

async def telegram():
    bot = Bot(token=API_TOKEN)
    offset = None  # Fetch new messages
    
    try:
        telegram_data = load_json_file(TELEGRAM_JSON_FILE)  # Load previous messages
    except Exception as e:
        print(f"Error loading JSON file: {e}")
        telegram_data = {}

    while True:
        try:
            updates = await bot.get_updates(offset=offset)

            if updates:
                for update in updates:
                    if update.message and update.message.text:
                        user_message = update.message.text.strip()

                        if is_pure_text(user_message):  # Check for valid text message
                            user_name = update.effective_user.full_name
                            chat_id = update.message.chat_id
                            chat_key = f"{user_name}-{chat_id}"
                            
                            msg_time_utc = update.message.date.replace(tzinfo=pytz.utc)
                            msg_time_ist = msg_time_utc.astimezone(IST)
                            timestamp = f"*{msg_time_ist.strftime('%d%m%y')}* *{msg_time_ist.strftime('%H%M')}*"

                            # Update message data
                            if chat_key not in telegram_data:
                                telegram_data[chat_key] = {}

                            telegram_data[chat_key][timestamp] = user_message

                        # Update offset for next message
                        offset = update.update_id + 1
            else:
                break  # No new messages, exit loop

        except NetworkError:
            activate_vibration(0.5)
            print("Network error")
            break
        except TelegramError as e:
            activate_vibration(0.5)
            print(f"Telegram API error: {e}")
            break
        except Exception as e:
            activate_vibration(0.5)
            print(f"Unexpected error: {e}")
            break

    try:
        save_json_file(telegram_data, TELEGRAM_JSON_FILE)  # Save data safely
    except Exception as e:
        print(f"Error saving JSON file: {e}")


# Chat and message navigation
async def navigate_chats():
    global show_value
    
    telegram_data = load_json_file(TELEGRAM_JSON_FILE)

    if not telegram_data:
        print("No chats available.")
        show_message(telegram="no chats, exiting telegram")
        return

    chat_names = list(telegram_data.keys())
    chat_index = 0

    while True:
        prev_x, prev_y, prev_button = 0, 0, 1
        print(f"Flushed: 'teleg'")
        msg='teleg'
        save_positions(msg)
        r=''
        for i,j in zip(msg,load):
            r+=order[order.index(i)-order.index(j)]
            
        for char in r:
            ser.write(char.encode())
            ser.flush()
            time.sleep(0.2)

        ser.write('\n'.encode())
        ser.flush()
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        time.sleep(0.05)
        chat_name = chat_names[chat_index]
        chat_name1 = chat_name.split("-")[0]
        chat_name1 = re.sub(r'(\b\d+)', r'*\1*', chat_name1.lower())
        print(f"Chat [{chat_index + 1}/{len(chat_names)}]: {chat_name}")
        
        try:
            while True:
                ser.write(b'R')  # Request Arduino data
                data1 = ser.readline().decode().strip()
                current_back_state = GPIO.input(BUTTON_BACK)
                
                
                if data1.startswith("DATA:") and data1.count(",") == 2:
                    x, y, button = map(int, data1.split(":")[1].split(","))
                    if (x, y, button) != (prev_x, prev_y, prev_button):
                        print(f"X: {x}, Y: {y}, Button: {button}")
                        prev_x, prev_y, prev_button = x, y, button
                        break
                  # Check if any button state changed
                if (current_back_state != prev_back_state ):
                    break  # Exit loop if any button changed
                time.sleep(0.01)
        except:
            print("Cannot read serial data")
        
        if prev_x == -1:
            activate_buzzer(0.1)
            chat_index = (chat_index - 1) % len(chat_names)
        elif prev_x == 1:
            activate_buzzer(0.1)
            chat_index = (chat_index + 1) % len(chat_names)
            
        elif prev_button == 0:
            activate_buzzer(0.1)
            show_message(telegram=chat_name1)
            
            if show_value=="ok":
                show_value =''
                await show_messages_in_chat(chat_name, telegram_data[chat_name])
            else:
                show_value=''
                continue
        elif current_back_state == GPIO.LOW and prev_back_state == GPIO.HIGH:
            activate_buzzer(0.1)
            print("Exiting telegram")
            return
        else:
            print("Invalid input. Please try again.")


async def show_messages_in_chat(chat_name, chat_messages):
    global show_value
    
    timestamps = list(chat_messages.keys())
    msg_index = 0
    chat_id = chat_name.split("-")[1]
    name = chat_name.split("-")[0]

    while True:
        prev_x, prev_y, prev_button = 0, 0, 1
        print(f"Flushed: 'chat'")
        r=''
        msg='chat;'
        save_positions(msg)
        for i,j in zip(msg,load):
            r+=order[order.index(i)-order.index(j)]
        
        for char in r:
            ser.write(char.encode())
            ser.flush()
            time.sleep(0.2)

        ser.write('\n'.encode())
        ser.flush()
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        time.sleep(0.05)
        
        timestamp = timestamps[msg_index]
        message = chat_messages[timestamp]
        message = "#" + message.lower()
        message = re.sub(r'(\b\d+)', r'*\1*', message)
        tele_message = f"{timestamp} {message}"
        print(f"{timestamp.replace('*', '')}[{msg_index + 1}/{len(timestamps)}]: {message}\n")
        
        try:
            while True:
                ser.write(b'R')  # Request Arduino data
                data1 = ser.readline().decode().strip()
                current_back_state = GPIO.input(BUTTON_BACK)
                current_record_state = GPIO.input(BUTTON_RECORD)
                
                if data1.startswith("DATA:") and data1.count(",") == 2:
                    x, y, button = map(int, data1.split(":")[1].split(","))
                    if (x, y, button) != (prev_x, prev_y, prev_button):
                        #print(f"X: {x}, Y: {y}, Button: {button}")
                        prev_x, prev_y, prev_button = x, y, button
                        break
                  # Check if any button state changed
                if (current_back_state != prev_back_state or 
                current_record_state != prev_record_state):
                    break  # Exit loop if any button changed
                time.sleep(0.01)
        except:
            print("Cannot read serial data")
        if prev_x == -1:
            activate_buzzer(0.1)
            msg_index = (msg_index - 1) % len(timestamps)
        elif prev_x == 1:
            activate_buzzer(0.1)
            msg_index = (msg_index + 1) % len(timestamps)
        elif prev_button == 0:
            activate_buzzer(0.1)
            show_message(telegram=tele_message)
        elif current_record_state == GPIO.LOW and prev_record_state == GPIO.HIGH:
            activate_buzzer(0.1)
            await send_telegram_message(chat_id)
        elif current_back_state == GPIO.LOW and prev_back_state == GPIO.HIGH:
            activate_buzzer(0.1)
            print(f"Exiting {name}.")
            
            return
        else:
            print("Invalid input. Please try again.")

async def send_telegram_message(chat_id):
    """
    Function to record an audio message and send it to the selected chat on Telegram.
    """
    RECORDING_FILE="telegram.wav"
    record_command = f"arecord -d 10 -f cd {RECORDING_FILE}"  # Modify for your platform if needed
    process = subprocess.Popen(record_command, shell=True, preexec_fn=os.setsid)

    try:
        print("Recording started.Release button to stop...")
        
        while GPIO.input(BUTTON_RECORD) == GPIO.LOW:
            time.sleep(0.01)  # Small delay to prevent CPU overuse
        os.killpg(os.getpgid(process.pid), signal.SIGINT)  # Stop recording
        print("Recording stopped. Sending message to Telegram...")

        # Initialize bot
        bot = Bot(token=API_TOKEN)
        
        # Send voice message
        with open(RECORDING_FILE, 'rb') as audio_file:
            await bot.send_voice(chat_id=chat_id, voice=audio_file)

        print("Voice message sent successfully!")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(RECORDING_FILE):
            os.remove(RECORDING_FILE)  # Delete recorded file after sending



def is_pure_text(text):
    """Check if text contains only letters, numbers, spaces, and basic punctuation."""
    text = emoji.replace_emoji(text, replace="")  # Remove emojis
    return bool(re.match(r"^[A-Za-z0-9\s.,!?'-]+$", text))  # Allowed characters

def telegram_app():
    activate_buzzer(0.1)
    print("Fetching Telegram messages...")
    
    asyncio.run(telegram())
    # Start chat navigation
    print("\nNavigating chats:")
    asyncio.run(navigate_chats())


prev_record_state = GPIO.HIGH
prev_back_state = GPIO.HIGH
prev_telegram_state = GPIO.HIGH
prev_delete_state = GPIO.HIGH

try:
    activate_vibration(0.5)
    time.sleep(0.5)
    activate_vibration(0.5)
    load=load_positions()
    while True:
        prev_x, prev_y, prev_button = 0, 0, 1
        print(f"Flushed: 'main'")

        # Send 'main' over serial
        r=''
        msg='main;'
        save_positions(msg)
        for i,j in zip(msg,load):
            r+=order[order.index(i)-order.index(j)]
        
        for char in r:
            ser.write(char.encode())
            ser.flush()
            time.sleep(0.1)

        ser.write(b'\n')
        ser.flush()
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        time.sleep(0.05)

        # Read joystick/button data from serial
        try:
            while True:
                ser.write(b'R')  # Request Arduino data
                data1 = ser.readline().decode().strip()
                current_record_state = GPIO.input(BUTTON_RECORD)
                current_back_state = GPIO.input(BUTTON_BACK)
                current_telegram_state = GPIO.input(BUTTON_TELEGRAM)
                current_delete_state = GPIO.input(BUTTON_DELETE)
                
                
                if data1.startswith("DATA:") and data1.count(",") == 2:
                    x, y, button = map(int, data1.split(":")[1].split(","))
                    if (x, y, button) != (prev_x, prev_y, prev_button):
                        #print(f"X: {x}, Y: {y}, Button: {button}")
                        prev_x, prev_y, prev_button = x, y, button
                        break
                  # Check if any button state changed
                if (current_record_state != prev_record_state or 
                    current_back_state != prev_back_state or 
                    current_telegram_state != prev_telegram_state or 
                    current_delete_state != prev_delete_state):
                    break  # Exit loop if any button changed
                time.sleep(0.01)
        except:
   
             current_record_state == GPIO.LOW and prev_record_state == GPIO.HIGH:
            activate_buzzer(0.1)
            record_and_save()  # Call function when button is pressed
            time.sleep(0.02)  # Small delay to prevent CPU overuse


        elif current_telegram_state == GPIO.LOW and prev_telegram_state == GPIO.HIGH:
            telegram_app()
            time.sleep(0.2)  # Debounce

        elif current_delete_state == GPIO.LOW and prev_delete_state == GPIO.HIGH:
            delete()
            time.sleep(0.2)  # Debounce

        # Handle Serial Joystick/Buttons
        if prev_x == -1:
            activate_buzzer(0.1)
            if current_index < len(data):
                current_index += 1
                print(f"Index {current_index}")
            else:
                print("You are at the latest message.")

        elif prev_x == 1:
            activate_buzzer(0.1)
            if current_index > 1:
                current_index -= 1
                print(f"Index {current_index}")
            else:
                print("You are at the first message.")

        elif prev_button == 0:
            activate_buzzer(0.1)
            show_message()
            time.sleep(0.2)

except KeyboardInterrupt:
    print("Exiting...")
    GPIO.cleanup()
    ser.close()
finally:
        GPIO.cleanup()
