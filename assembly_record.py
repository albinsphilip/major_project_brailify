import os
import subprocess
import assemblyai as aai
import json
import re
import signal

# Replace with your API key
aai.settings.api_key = "91ed4cffb8a54c9cba735a07447472c2"

# Record audio
recording_file = 'recording.wav'
record_command = f'arecord -D hw:3,0 -f cd -c 1 -t wav {recording_file}'
print("Recording audio... Press Ctrl+C to stop.")

# Start recording process
process = subprocess.Popen(record_command, shell=True, preexec_fn=os.setsid)

try:
    process.wait()
except KeyboardInterrupt:
    os.killpg(os.getpgid(process.pid), signal.SIGINT)  # Gracefully stop the recording process
    print("Recording interrupted by user.")

print("Recording finished.")

# Proceed with transcription and processing
transcriber = aai.Transcriber()
transcript = transcriber.transcribe(recording_file)

if transcript.status == aai.TranscriptStatus.error:
    print(transcript.error)
else:
    # Create a dictionary with the transcription
    new_data = transcript.text

    # Process the text: make all characters lowercase and remove special characters except , and .
    processed_text = new_data.lower()
    processed_text = re.sub(r'[^a-z0-9,. ]+', '', processed_text)

    # Define the JSON file path
    json_file_path = 'transcriptions.json'

    # Check if the JSON file already exists
    if os.path.exists(json_file_path):
        # Read the existing data from the JSON file
        with open(json_file_path, 'r') as file:
            data = json.load(file)
    else:
        # Create an empty dictionary if the file does not exist
        data = {}

    # Determine the next index key
    next_index = len(data) + 1

    # Add the new transcription with the next index as the key
    data[next_index] = processed_text

    # Write the updated data back to the JSON file
    with open(json_file_path, 'w') as file:
        json.dump(data, file, indent=4)

    print(f"Transcription added to {json_file_path} with index: {next_index}")

    # Append the processed text to transcription.txt
    with open('transcription.txt', 'a') as file:
        file.write(processed_text + '\n')

