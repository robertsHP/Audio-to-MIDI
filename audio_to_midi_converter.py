import os
import librosa
import pretty_midi
import numpy as np

class AudioToMidiConverter:
    def __init__(self, enable_pitch_bends=True):
        self.enable_pitch_bends = enable_pitch_bends

    def frequency_to_midi(self, frequency):
        """Convert frequency in Hz to MIDI note number."""
        if frequency <= 0:
            return None
        midi_number = 69 + 12 * np.log2(frequency / 440.0)
        if 0 <= midi_number <= 127:
            return int(round(midi_number))
        return None

    def estimate_note_duration(self, onset_times, index, audio_length, default_duration=0.5):
        """Estimate the duration of a note based on onset times."""
        if index < len(onset_times) - 1:
            return onset_times[index + 1] - onset_times[index]
        else:
            return min(default_duration, audio_length - onset_times[index])

    def pitch_to_bend(self, pitch, base_midi_note):
        """Convert pitch deviation into MIDI pitch bend value."""
        if base_midi_note is None:
            return 0
        semitone_offset = pitch - base_midi_note
        pitch_bend = int(semitone_offset * 8192 / 2)  # scale to MIDI pitch bend range
        return np.clip(pitch_bend, -8192, 8191)

    def convert_audio_to_midi(self, audio_path, output_midi_path):
        """Convert an audio file to a MIDI file with optional pitch bends."""
        y, sr = librosa.load(audio_path)
        audio_length = librosa.get_duration(y=y, sr=sr)
        
        # Detect onsets (where notes start)
        onset_frames = librosa.onset.onset_detect(y=y, sr=sr, units='frames')
        onset_times = librosa.frames_to_time(onset_frames, sr=sr)
        
        # More accurate pitch tracking with librosa's yin method
        pitches, magnitudes = librosa.core.pitch.piptrack(y=y, sr=sr)
        
        midi = pretty_midi.PrettyMIDI()
        
        # Create an Instrument instance
        piano_program = pretty_midi.instrument_name_to_program('Acoustic Grand Piano')
        piano = pretty_midi.Instrument(program=piano_program)
        
        for i, onset_time in enumerate(onset_times):
            frame = onset_frames[i]
            if frame >= pitches.shape[1]:
                continue
            pitch_values = pitches[:, frame]
            max_magnitude_index = magnitudes[:, frame].argmax()
            pitch = pitch_values[max_magnitude_index]
            
            # Convert the pitch to MIDI note number
            midi_note = self.frequency_to_midi(pitch)
            if midi_note is not None:  # Only add if pitch is within valid MIDI range
                midi_note_int = midi_note
                
                # Dynamic velocity calculation
                local_magnitude = magnitudes[max_magnitude_index, frame]
                velocity = min(127, int(local_magnitude * 127 / magnitudes.max()))
                if velocity == 0:
                    velocity = 1  # Ensure velocity is at least 1
                
                # Estimate note duration
                duration = self.estimate_note_duration(onset_times, i, audio_length)
                
                note = pretty_midi.Note(
                    velocity=velocity,
                    pitch=midi_note_int,
                    start=onset_time,
                    end=onset_time + duration
                )
                piano.notes.append(note)
                
                # Handle pitch bends if enabled
                if self.enable_pitch_bends:
                    bend_values = []
                    bend_times = []
                    for bend_frame in range(frame, frame + int(sr * duration)):
                        if bend_frame >= pitches.shape[1]:
                            break
                        bend_pitch_values = pitches[:, bend_frame]
                        bend_max_magnitude_index = magnitudes[:, bend_frame].argmax()
                        bend_pitch = bend_pitch_values[bend_max_magnitude_index]
                        
                        if bend_pitch > 0:
                            bend_midi_note = self.frequency_to_midi(bend_pitch)
                            if bend_midi_note is not None:
                                bend_value = self.pitch_to_bend(bend_midi_note, midi_note_int)
                                midi_time = librosa.frames_to_time(bend_frame, sr=sr)
                                bend_values.append(bend_value)
                                bend_times.append(midi_time)
                    
                    # Smooth the pitch bend values
                    if bend_values:
                        times = np.array(bend_times)
                        values = np.array(bend_values)
                        smoothed_values = np.interp(times, times, values)
                        
                        for time, bend_value in zip(times, smoothed_values):
                            bend = pretty_midi.PitchBend(int(bend_value), time)
                            piano.pitch_bends.append(bend)
        
        midi.instruments.append(piano)
        midi.write(output_midi_path)