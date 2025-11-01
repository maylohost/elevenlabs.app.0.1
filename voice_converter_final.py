# AVVISO: tkinter e sounddevice richiedono l'esecuzione su un sistema locale con GUI e accesso all'audio
# Per installare tkinter: sudo apt install python3-tk
# Per installare sounddevice: pip install sounddevice

try:
    import tkinter as tk
except ImportError:
    print("Errore: Il modulo 'tkinter' non è disponibile. Assicurati di eseguire questo script in un ambiente con GUI.")
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

# Configurazione API
API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "YKUjKbMlejgvkOZlnnvt")

if not API_KEY:
    print("Errore: ELEVENLABS_API_KEY non impostata. Imposta la variabile d'ambiente prima di eseguire.")
    exit(1)

# Percorsi
BASE_DIR = os.path.expanduser("~/Appz/voiceelevenlabs")
RECORDINGS_DIR = os.path.join(BASE_DIR, "registrazioni")
CONVERSIONS_DIR = os.path.join(BASE_DIR, "conversioni")
os.makedirs(RECORDINGS_DIR, exist_ok=True)
os.makedirs(CONVERSIONS_DIR, exist_ok=True)

# Registrazione audio
recording_data = []
is_recording = False
start_time = None

def record_audio_live(filename, samplerate=44100):
    global is_recording, recording_data, start_time
    try:
        app.append_output("[*] Inizio registrazione. Premi di nuovo il tasto per fermare...")
        recording_data = []
        is_recording = True
        start_time = time.time()

        def callback(indata, frames, time_info, status):
            if is_recording:
                recording_data.append(indata.copy())
                elapsed = int(time.time() - start_time)
                app.append_output(f"[+] Secondi registrati: {elapsed}")
            else:
                raise sd.CallbackStop()

        with sd.InputStream(callback=callback, samplerate=samplerate, channels=1):
            while is_recording:
                sd.sleep(100)

        audio_np = np.concatenate(recording_data, axis=0)
        sf.write(filename, audio_np, samplerate)
        app.append_output("[✓] Registrazione completata.")

    except Exception as e:
        app.append_output(f"[!] Errore durante la registrazione: {str(e)}")

# Invio a ElevenLabs
def convert_voice(input_path, output_path):
    # Validazione file input
    if not os.path.exists(input_path):
        app.append_output(f"[!] Errore: File di registrazione non trovato: {input_path}")
        return
    
    file_size = os.path.getsize(input_path)
    if file_size == 0:
        app.append_output(f"[!] Errore: Il file di registrazione è vuoto.")
        return
    
    app.append_output(f"[*] Invio file a ElevenLabs ({file_size / 1024:.1f} KB)...")
    
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
            # Aggiunto timeout per evitare attese infinite
            response = requests.post(url, headers=headers, files=files, timeout=120)
            
            if response.status_code == 200:
                with open(output_path, 'wb') as out_file:
                    out_file.write(response.content)
                output_size = os.path.getsize(output_path)
                app.append_output(f"[✓] Audio convertito salvato come {os.path.basename(output_path)} ({output_size / 1024:.1f} KB)")
                try:
                    subprocess.run(["xdg-open", CONVERSIONS_DIR], timeout=5, check=False)
                except Exception:
                    pass  # Ignora errori se xdg-open non disponibile
            elif response.status_code == 401:
                app.append_output(f"[!] Errore: API key non valida. Verifica la chiave ELEVENLABS_API_KEY")
            elif response.status_code == 429:
                app.append_output(f"[!] Errore: Limite di richieste superato. Riprova più tardi.")
            elif response.status_code == 400:
                app.append_output(f"[!] Errore: Richiesta non valida. Verifica il formato del file audio.\n{response.text[:200]}")
            else:
                app.append_output(f"[!] Errore nella conversione (HTTP {response.status_code}):\n{response.text[:300]}")
                
    except requests.exceptions.Timeout:
        app.append_output(f"[!] Errore: Timeout della richiesta. Il file potrebbe essere troppo grande o la connessione troppo lenta.")
    except requests.exceptions.ConnectionError:
        app.append_output(f"[!] Errore: Impossibile connettersi a ElevenLabs. Verifica la connessione internet.")
    except requests.exceptions.RequestException as e:
        app.append_output(f"[!] Errore durante la richiesta: {str(e)}")
    except FileNotFoundError:
        app.append_output(f"[!] Errore: File di registrazione non trovato: {input_path}")
    except PermissionError:
        app.append_output(f"[!] Errore: Permessi insufficienti per scrivere il file di output.")
    except Exception as e:
        app.append_output(f"[!] Errore imprevisto durante l'invio: {str(e)}")

# GUI
class VoiceApp:
    def __init__(self, master):
        self.master = master
        master.title("Voice Converter ElevenLabs")
        master.configure(bg='black')
        master.geometry("500x400")

        self.label = tk.Label(master, text="Registratore Voce → ElevenLabs", bg='black', fg='white', font=('Courier', 14, 'bold'))
        self.label.pack(pady=10)

        self.record_button = tk.Button(master, text="🎙️ Avvia / Ferma Registrazione", command=self.toggle_recording, bg='black', fg='white', activebackground='gray', font=('Courier', 10, 'bold'))
        self.record_button.pack(pady=5)

        self.convert_button = tk.Button(master, text="📤 Invia a ElevenLabs", command=self.process_conversion, bg='black', fg='white', activebackground='gray', font=('Courier', 10, 'bold'))
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
            # Aggiorna il timestamp per il nuovo file di registrazione
            timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
            self.filename = os.path.join(RECORDINGS_DIR, f"recording_{timestamp}.wav")
            self.thread = threading.Thread(target=record_audio_live, args=(self.filename,))
            self.thread.daemon = True  # Permette chiusura app anche se thread attivo
            self.thread.start()
        else:
            is_recording = False
            self.append_output("[*] Stopping registrazione...")

    def process_conversion(self):
        if not os.path.exists(self.filename):
            self.append_output("[!] Errore: Nessuna registrazione trovata. Registra prima un audio.")
            return
        
        if os.path.getsize(self.filename) == 0:
            self.append_output("[!] Errore: La registrazione è vuota. Registra di nuovo.")
            return
        
        # Aggiorna il timestamp per il file di output
        timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        self.output_filename = os.path.join(CONVERSIONS_DIR, f"converted_{timestamp}.mp3")
        
        threading.Thread(target=convert_voice, args=(self.filename, self.output_filename)).start()

if __name__ == "__main__":
    print("Avvio GUI...")
    root = tk.Tk()
    app = VoiceApp(root)
    root.mainloop()
