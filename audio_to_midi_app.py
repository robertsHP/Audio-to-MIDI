import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import threading
import os
from audio_to_midi_converter import AudioToMidiConverter  # Ensure this is the correct import path

class AudioToMidiApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio to MIDI Converter")

        self.audio_folder_path = ""
        self.output_folder_path = ""
        self.enable_pitch_bends = tk.BooleanVar(value=True)
        self.conversion_thread = None
        self.cancel_conversion = tk.BooleanVar(value=False)

        # Create and place widgets
        self.create_widgets()

    def create_widgets(self):
        # Audio folder selection
        self.audio_folder_label = tk.Label(self.root, text="Audio Folder:")
        self.audio_folder_label.grid(row=0, column=0, padx=10, pady=10)
        
        self.audio_folder_entry = tk.Entry(self.root, width=50)
        self.audio_folder_entry.grid(row=0, column=1, padx=10, pady=10)
        
        self.audio_folder_button = tk.Button(self.root, text="Select Folder", command=self.select_audio_folder)
        self.audio_folder_button.grid(row=0, column=2, padx=10, pady=10)

        # MIDI folder selection
        self.output_folder_label = tk.Label(self.root, text="Output MIDI Folder:")
        self.output_folder_label.grid(row=1, column=0, padx=10, pady=10)
        
        self.output_folder_entry = tk.Entry(self.root, width=50)
        self.output_folder_entry.grid(row=1, column=1, padx=10, pady=10)
        
        self.output_folder_button = tk.Button(self.root, text="Select Folder", command=self.select_output_folder)
        self.output_folder_button.grid(row=1, column=2, padx=10, pady=10)

        # Pitch bend detection toggle
        self.pitch_bend_checkbox = tk.Checkbutton(
            self.root, text="Enable Pitch Bend Detection",
            variable=self.enable_pitch_bends)
        self.pitch_bend_checkbox.grid(row=2, column=0, columnspan=3, padx=10, pady=10)

        # Start conversion button
        self.start_button = tk.Button(self.root, text="Start Conversion", command=self.start_conversion)
        self.start_button.grid(row=3, column=0, columnspan=2, padx=10, pady=20, sticky="e")

        # Cancel conversion button
        self.cancel_button = tk.Button(self.root, text="Cancel Conversion", command=self.cancel_conversion)
        self.cancel_button.grid(row=3, column=1, columnspan=2, padx=10, pady=20, sticky="w")

        # Console output
        self.console_text = scrolledtext.ScrolledText(self.root, width=60, height=15)
        self.console_text.grid(row=4, column=0, columnspan=3, padx=10, pady=10)

    def select_audio_folder(self):
        self.audio_folder_path = filedialog.askdirectory()
        self.audio_folder_entry.delete(0, tk.END)
        self.audio_folder_entry.insert(0, self.audio_folder_path)

    def select_output_folder(self):
        self.output_folder_path = filedialog.askdirectory()
        self.output_folder_entry.delete(0, tk.END)
        self.output_folder_entry.insert(0, self.output_folder_path)

    def log_console(self, message):
        self.console_text.insert(tk.END, message + '\n')
        self.console_text.see(tk.END)  # Auto-scroll to the latest message

    def start_conversion(self):
        if not self.audio_folder_path or not self.output_folder_path:
            messagebox.showerror("Error", "Please select both folders before starting the conversion.")
            return
        
        self.cancel_conversion.set(False)
        self.console_text.delete(1.0, tk.END)  # Clear previous console messages
        
        # Run the conversion in a separate thread to keep the UI responsive
        self.conversion_thread = threading.Thread(target=self.run_conversion)
        self.conversion_thread.start()

    def cancel_conversion(self):
        self.cancel_conversion.set(True)
        self.log_console("Conversion cancelled by user.")

    def run_conversion(self):
        converter = AudioToMidiConverter(enable_pitch_bends=self.enable_pitch_bends.get())

        for filename in os.listdir(self.audio_folder_path):
            if self.cancel_conversion.get():
                self.log_console("Conversion stopped.")
                return

            if filename.endswith(".m4a"):  # Add more extensions if needed
                audio_path = os.path.join(self.audio_folder_path, filename)
                midi_filename = os.path.splitext(filename)[0] + '.mid'
                output_midi_path = os.path.join(self.output_folder_path, midi_filename)
                
                try:
                    # Convert audio to MIDI
                    converter.convert_audio_to_midi(audio_path, output_midi_path)
                    self.log_console(f'Converted {filename} to {midi_filename}')
                except Exception as e:
                    self.log_console(f'Error converting {filename}: {e}')
        
        self.log_console("Conversion complete.")
        messagebox.showinfo(
            "Conversion Complete", 
            "All files have been successfully converted or the process was cancelled.")
