# Brailify: Voice to Refreshable Braille Display

## Project Overview

Brailify is a project that converts voice input into a refreshable Braille display, providing a cost-effective speech-to-Braille device. The system uses a combination of Python scripts and an Arduino to process voice input, convert it to text, and then display the corresponding Braille characters using a stepper motor.

## Project Structure

### Files

1. **assembly_record.py**
   - **Description**: This script records audio input, transcribes it using AssemblyAI, and adds the transcription to `transcriptions.json` and `transcription.txt`.
   - **Functions**:
     - Records audio input.
     - Uses AssemblyAI to transcribe the audio.
     - Saves the transcription to `transcriptions.json` and `transcription.txt`.

2. **serial_send.py**
   - **Description**: This script reads the `transcriptions.json` file and sends the transcribed data serially to the Arduino.
   - **Functions**:
     - Reads the transcription data from `transcriptions.json`.
     - Sends the data to the Arduino via serial communication.

3. **assembly_record_and_send.py**
   - **Description**: This script combines the functionalities of `assembly_record.py` and `serial_send.py`. It records audio, transcribes it, and then sends the transcribed data to the Arduino.
   - **Functions**:
     - Records audio input.
     - Uses AssemblyAI to transcribe the audio.
     - Saves the transcription to `transcriptions.json` and `transcription.txt`.
     - Reads the transcription data and sends it to the Arduino via serial communication.

## Setup and Installation

1. **Clone the Repository**:
   ```sh
   git clone https://github.com/yourusername/brailify.git
   cd brailify
