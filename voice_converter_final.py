# NOTE: tkinter and sounddevice require execution on a local system with GUI and audio access
# To install tkinter: sudo apt install python3-tk
# To install sounddevice: pip install sounddevice

try:
    import tkinter as tk
except ImportError:
    print("Error: The 'tkinter' module is not available. Make sure to run this script in a GUI environment.")
    exit(1)

import sounddevice as sd
import soundfile as sf
import requests
import os
import threading
import numpy as np
import time
import subprocess
from datetime import datetime

# API Configuration
API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "YKUjKbMlejgvkOZlnnvt")

if not API_KEY:
    print("Error: ELEVENLABS_API_KEY not set. Set the environment variable before running.")
    exit(1)

# Paths
BASE_DIR = os.path.expanduser("~/Appz/voiceelevenlabs")
RECORDINGS_DIR = os.path.join(BASE_DIR, "recordings")
CONVERSIONS_DIR = os.path.join(BASE_DIR, "conversions")
os.makedirs(RECORDINGS_DIR, exist_ok=True)
os.makedirs(CONVERSIONS_DIR, exist_ok=True)

# Audio recording
recording_data = []
is_recording = False
start_time = None

def record_audio_live(filename, samplerate=44100):
    global is_recording, recording_data, start_time
    try:
        app.append_output("[*] Starting recording. Press the button again to stop...")
        recording_data = []
        is_recording = True
        start_time = time.time()

        def callback(indata, frames, time_info, status):
            if is_recording:
                recording_data.append(indata.copy())
                elapsed = int(time.time() - start_time)
                app.append_output(f"[+] Seconds recorded: {elapsed}")
            else:
                raise sd.CallbackStop()

        with sd.InputStream(callback=callback, samplerate=samplerate, channels=1):
            while is_recording:
                sd.sleep(100)

        audio_np = np.concatenate(recording_data, axis=0)
        sf.write(filename, audio_np, samplerate)
        app.append_output("[✓] Recording completed.")

    except Exception as e:
        app.append_output(f"[!] Error during recording: {str(e)}")

# Send to ElevenLabs
def convert_voice(input_path, output_path):
    # Input file validation
    if not os.path.exists(input_path):
        app.append_output(f"[!] Error: Recording file not found: {input_path}")
        return
    
    file_size = os.path.getsize(input_path)
    if file_size == 0:
        app.append_output(f"[!] Error: The recording file is empty.")
        return
    
    app.append_output(f"[*] Sending file to ElevenLabs ({file_size / 1024:.1f} KB)...")
    
    url = f"https://api.elevenlabs.io/v1/speech-to-speech/{VOICE_ID}"
    headers = {
        "xi-api-key": API_KEY,
        "Accept": "audio/mpeg"
    }
    
    try:
        with open(input_path, 'rb') as audio_file:
            files = {
                'audio': (os.path.basename(input_path), audio_file, 'audio/wav')
            }
            # Added timeout to avoid infinite waits
            response = requests.post(url, headers=headers, files=files, timeout=120)
            
            if response.status_code == 200:
                with open(output_path, 'wb') as out_file:
                    out_file.write(response.content)
                output_size = os.path.getsize(output_path)
                app.append_output(f"[✓] Converted audio saved as {os.path.basename(output_path)} ({output_size / 1024:.1f} KB)")
                try:
                    subprocess.run(["xdg-open", CONVERSIONS_DIR], timeout=5, check=False)
                except Exception:
                    pass  # Ignore errors if xdg-open is not available
            elif response.status_code == 401:
                app.append_output(f"[!] Error: Invalid API key. Check your ELEVENLABS_API_KEY")
            elif response.status_code == 429:
                app.append_output(f"[!] Error: Rate limit exceeded. Please try again later.")
            elif response.status_code == 400:
                app.append_output(f"[!] Error: Invalid request. Check the audio file format.\n{response.text[:200]}")
            else:
                app.append_output(f"[!] Conversion error (HTTP {response.status_code}):\n{response.text[:300]}")
                
    except requests.exceptions.Timeout:
        app.append_output(f"[!] Error: Request timeout. The file might be too large or the connection too slow.")
    except requests.exceptions.ConnectionError:
        app.append_output(f"[!] Error: Unable to connect to ElevenLabs. Check your internet connection.")
    except requests.exceptions.RequestException as e:
        app.append_output(f"[!] Error during request: {str(e)}")
    except FileNotFoundError:
        app.append_output(f"[!] Error: Recording file not found: {input_path}")
    except PermissionError:
        app.append_output(f"[!] Error: Insufficient permissions to write the output file.")
    except Exception as e:
        app.append_output(f"[!] Unexpected error during upload: {str(e)}")

# GUI
class VoiceApp:
    def __init__(self, master):
        self.master = master
        master.title("Voice Converter ElevenLabs")
        master.configure(bg='black')
        master.geometry("500x400")

        self.label = tk.Label(master, text="Voice Recorder → ElevenLabs", bg='black', fg='white', font=('Courier', 14, 'bold'))
        self.label.pack(pady=10)

        self.record_button = tk.Button(master, text="🎙️ Start / Stop Recording", command=self.toggle_recording, bg='black', fg='white', activebackground='gray', font=('Courier', 10, 'bold'))
        self.record_button.pack(pady=5)

        self.convert_button = tk.Button(master, text="📤 Send to ElevenLabs", command=self.process_conversion, bg='black', fg='white', activebackground='gray', font=('Courier', 10, 'bold'))
        self.convert_button.pack(pady=5)

        self.clear_button = tk.Button(master, text="🧹 Clear Log", command=self.clear_output, bg='black', fg='white', activebackground='gray', font=('Courier', 10))
        self.clear_button.pack(pady=5)

        self.output_box = tk.Text(master, height=10, bg='black', fg='lime', font=('Courier', 10), wrap='word')
        self.output_box.pack(padx=10, pady=10, fill='both', expand=True)
        self.output_box.insert(tk.END, "[~] echo welcome\n")
        self.output_box.config(state='disabled')

        timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        self.filename = os.path.join(RECORDINGS_DIR, f"recording_{timestamp}.wav")
        self.output_filename = os.path.join(CONVERSIONS_DIR, f"converted_{timestamp}.mp3")
        self.thread = None

    def append_output(self, text):
        self.output_box.config(state='normal')
        self.output_box.insert(tk.END, text + '\n')
        self.output_box.see(tk.END)
        self.output_box.config(state='disabled')

    def clear_output(self):
        self.output_box.config(state='normal')
        self.output_box.delete('1.0', tk.END)
        self.output_box.insert(tk.END, "[~] echo welcome\n")
        self.output_box.config(state='disabled')

    def toggle_recording(self):
        global is_recording
        if not is_recording:
            # Update timestamp for the new recording file
            timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
            self.filename = os.path.join(RECORDINGS_DIR, f"recording_{timestamp}.wav")
            self.thread = threading.Thread(target=record_audio_live, args=(self.filename,))
            self.thread.daemon = True  # Allows app to close even if thread is active
            self.thread.start()
        else:
            is_recording = False
            self.append_output("[*] Stopping recording...")

    def process_conversion(self):
        if not os.path.exists(self.filename):
            self.append_output("[!] Error: No recording found. Record an audio first.")
            return
        
        if os.path.getsize(self.filename) == 0:
            self.append_output("[!] Error: The recording is empty. Record again.")
            return
        
        # Update timestamp for the output file
        timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        self.output_filename = os.path.join(CONVERSIONS_DIR, f"converted_{timestamp}.mp3")
        
        threading.Thread(target=convert_voice, args=(self.filename, self.output_filename)).start()

if __name__ == "__main__":
    print("Starting GUI...")
    root = tk.Tk()
    app = VoiceApp(root)
    root.mainloop()
