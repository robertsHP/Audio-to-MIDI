import tkinter as tk

from audio_to_midi_app import AudioToMidiApp

# Main application
if __name__ == "__main__":
    root = tk.Tk()
    app = AudioToMidiApp(root)
    root.mainloop()