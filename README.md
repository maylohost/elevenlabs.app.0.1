```
███╗   ███╗    █████╗    ██╗   ██╗██╗      ██████╗ 
████╗ ████║   ██╔══██╗   ╚██╗ ██╔╝██║     ██╔═══██╗
██╔████╔██║   ███████║    ╚████╔╝ ██║     ██║   ██║
██║╚██╔╝██║   ██╔══██║     ╚██╔╝  ██║     ██║   ██║
██║ ╚═╝ ██║   ██║  ██║      ██║   ███████╗╚██████╔╝
╚═╝     ╚═╝   ╚═╝  ╚═╝      ╚═╝   ╚══════╝ ╚═════╝ 
```

# ElevenLabs Voice Converter

A simple desktop application for Linux that records audio and converts it using the ElevenLabs Speech-to-Speech API.

## Features

- 🎙️ Real-time audio recording with live timer
- 🔄 Voice conversion using ElevenLabs API
- 💾 Automatic file organization with timestamps
- 🖥️ Simple GUI built with tkinter
- ✅ Comprehensive error handling and validation

## Requirements

- Python 3.8 or higher
- Linux with GUI support (X11/Wayland)
- Audio input device (microphone)
- tkinter (usually included, but may require installation on some distributions)

### System Dependencies

On Debian/Ubuntu-based systems:
```bash
sudo apt install python3-tk
```

## Installation

1. Clone or download this repository

2. Create a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

You need an ElevenLabs API key to use this application.

1. Get your API key from [ElevenLabs](https://elevenlabs.io/)

2. Set the environment variable before running:
```bash
export ELEVENLABS_API_KEY="your_api_key_here"
```

3. (Optional) Set a custom Voice ID:
```bash
export ELEVENLABS_VOICE_ID="your_voice_id_here"
```

To make it permanent, add these lines to your `~/.bashrc` or `~/.profile`:
```bash
echo 'export ELEVENLABS_API_KEY="your_api_key_here"' >> ~/.bashrc
source ~/.bashrc
```

## Usage

Run the application:
```bash
python3 voice_converter_final.py
```

### How to Use

1. Click "🎙️ Avvia / Ferma Registrazione" to start recording
2. Click the button again to stop recording
3. Click "📤 Invia a ElevenLabs" to convert the recorded audio
4. The converted audio will be saved automatically and the output folder will open

### File Organization

- Recordings are saved in: `~/Appz/voiceelevenlabs/registrazioni/`
- Converted files are saved in: `~/Appz/voiceelevenlabs/conversioni/`
- Files are automatically named with timestamps

## Error Handling

The application includes robust error handling for:
- Missing or invalid API keys
- Network connection issues
- Timeout errors
- File permission problems
- Invalid audio files

## License

This project is provided as-is for personal use.

## Notes

- The application requires an active internet connection to use the ElevenLabs API
- Large audio files may take longer to process
- Make sure you have sufficient API quota on your ElevenLabs account

