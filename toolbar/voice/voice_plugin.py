import tkinter as tk
from tkinter import ttk
import pyttsx3
import speech_recognition as sr
import threading
from typing import Callable, Optional, List, Dict
import pyperclip
import pyautogui
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sounddevice as sd
from ..utils.audio_processing import AudioProcessor, AudioFormat
from ..utils.logger import logger

class VoiceWidget:
    """Widget for voice-related functionality including speech-to-text and text-to-speech"""
    def __init__(self, root: tk.Tk):
        try:
            self.root = root
            self.frame = ttk.Frame(root)
            self.frame.pack(side=tk.TOP, fill=tk.X)
            
            # Initialize engines
            self.engine = pyttsx3.init()
            self.recognizer = sr.Recognizer()
            self.audio_processor = AudioProcessor()
            
            # State variables
            self.is_listening = False
            self.is_speaking = False
            self.is_recording = False
            self.current_language = 'en-US'
            self.available_languages = self._get_available_languages()
            
            # Audio visualization
            self.setup_visualization()
            
            # Create and style buttons
            self.create_buttons()
            self.setup_styles()
            
            # Configure keyboard shortcuts
            self.setup_shortcuts()
            
            # Audio recording setup
            self.recording_stream = None
            self.recorded_audio = []
            self.sample_rate = 44100
            
            logger.info("VoiceWidget initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize VoiceWidget: {str(e)}")
            raise
    
    def _get_available_languages(self) -> Dict[str, str]:
        """Get available languages for speech recognition"""
        return {
            'en-US': 'English (US)',
            'es-ES': 'Spanish',
            'fr-FR': 'French',
            'de-DE': 'German',
            'it-IT': 'Italian',
            'ja-JP': 'Japanese',
            'ko-KR': 'Korean',
            'zh-CN': 'Chinese (Simplified)',
            'ru-RU': 'Russian'
        }
    
    def setup_visualization(self):
        """Set up audio visualization"""
        try:
            # Create matplotlib figure for visualization
            self.fig = Figure(figsize=(4, 1), dpi=100)
            self.ax = self.fig.add_subplot(111)
            self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)
            
            # Initialize empty plot
            self.line, = self.ax.plot([], [])
            self.ax.set_ylim(-1, 1)
            self.ax.set_xlim(0, 100)
            self.ax.axis('off')
            
            logger.info("Audio visualization setup complete")
        except Exception as e:
            logger.error(f"Failed to setup visualization: {str(e)}")
    
    def update_visualization(self, audio_data):
        """Update the audio waveform visualization"""
        try:
            if len(audio_data) > 0:
                # Normalize and reshape audio data
                data = np.frombuffer(audio_data, dtype=np.int16)
                data = data.astype(np.float32) / 32768.0
                
                # Update plot
                self.ax.clear()
                self.ax.plot(data)
                self.ax.set_ylim(-1, 1)
                self.ax.axis('off')
                self.canvas.draw()
        except Exception as e:
            logger.error(f"Failed to update visualization: {str(e)}")
    
    def setup_styles(self):
        """Set up widget styles"""
        try:
            style = ttk.Style()
            style.configure('Icon.TButton', padding=2)
            style.configure('Active.TButton',
                          background='#007AFF',
                          foreground='white')
            style.configure('Record.TButton',
                          background='#FF3B30',
                          foreground='white')
            logger.info("Widget styles configured")
        except Exception as e:
            logger.error(f"Failed to setup styles: {str(e)}")
    
    def setup_shortcuts(self):
        """Set up keyboard shortcuts"""
        try:
            keyboard.add_hotkey('ctrl+shift+s', self.toggle_speech_to_text)
            keyboard.add_hotkey('ctrl+shift+t', self.start_text_to_speech)
            keyboard.add_hotkey('ctrl+shift+r', self.toggle_recording)
            logger.info("Keyboard shortcuts registered")
        except Exception as e:
            logger.error(f"Failed to setup shortcuts: {str(e)}")
    
    def create_buttons(self):
        """Create widget buttons"""
        try:
            # Settings button
            self.settings_btn = ttk.Button(
                self.frame,
                text="⚙️",
                width=3,
                style='Icon.TButton',
                command=self.show_settings
            )
            self.settings_btn.pack(side=tk.LEFT, padx=2)
            
            # Speech-to-text button
            self.stt_btn = ttk.Button(
                self.frame,
                text="🎤",
                width=3,
                style='Icon.TButton',
                command=self.toggle_speech_to_text
            )
            self.stt_btn.pack(side=tk.LEFT, padx=2)
            
            # Text-to-speech button
            self.tts_btn = ttk.Button(
                self.frame,
                text="🔊",
                width=3,
                style='Icon.TButton',
                command=self.start_text_to_speech
            )
            self.tts_btn.pack(side=tk.LEFT, padx=2)
            
            # Record button
            self.record_btn = ttk.Button(
                self.frame,
                text="⏺",
                width=3,
                style='Icon.TButton',
                command=self.toggle_recording
            )
            self.record_btn.pack(side=tk.LEFT, padx=2)
            
            # Language selector
            self.lang_var = tk.StringVar(value=self.current_language)
            self.lang_menu = ttk.Combobox(
                self.frame,
                textvariable=self.lang_var,
                values=list(self.available_languages.keys()),
                width=6,
                state='readonly'
            )
            self.lang_menu.pack(side=tk.LEFT, padx=2)
            self.lang_menu.bind('<<ComboboxSelected>>', self.on_language_change)
            
            logger.info("Buttons created successfully")
        except Exception as e:
            logger.error(f"Failed to create buttons: {str(e)}")
    
    def on_language_change(self, event):
        """Handle language change"""
        try:
            self.current_language = self.lang_var.get()
            logger.info(f"Language changed to: {self.current_language}")
        except Exception as e:
            logger.error(f"Failed to change language: {str(e)}")
    
    def toggle_recording(self):
        """Toggle audio recording"""
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()
    
    def start_recording(self):
        """Start audio recording"""
        try:
            self.is_recording = True
            self.record_btn.configure(style='Record.TButton')
            self.recorded_audio = []
            
            def audio_callback(indata, frames, time, status):
                if status:
                    logger.warning(f"Audio recording status: {status}")
                if self.is_recording:
                    self.recorded_audio.extend(indata.copy())
                    self.root.after(0, lambda: self.update_visualization(indata.tobytes()))
            
            self.recording_stream = sd.InputStream(
                channels=1,
                samplerate=self.sample_rate,
                callback=audio_callback
            )
            self.recording_stream.start()
            logger.info("Started audio recording")
        except Exception as e:
            logger.error(f"Failed to start recording: {str(e)}")
            self.stop_recording()
    
    def stop_recording(self):
        """Stop audio recording"""
        try:
            self.is_recording = False
            self.record_btn.configure(style='Icon.TButton')
            
            if self.recording_stream:
                self.recording_stream.stop()
                self.recording_stream.close()
                self.recording_stream = None
            
            if len(self.recorded_audio) > 0:
                # Convert recorded audio to numpy array
                audio_data = np.concatenate(self.recorded_audio)
                
                # Process the recorded audio
                processed_audio = self.audio_processor.process_audio(
                    audio_data.tobytes(),
                    AudioFormat.RAW
                )
                
                # Save the processed audio or use it for speech recognition
                self.process_recorded_audio(processed_audio)
            
            logger.info("Stopped audio recording")
        except Exception as e:
            logger.error(f"Failed to stop recording: {str(e)}")
    
    def process_recorded_audio(self, audio_data: bytes):
        """Process recorded audio data"""
        try:
            # Convert to audio data recognizable by speech_recognition
            audio = sr.AudioData(
                audio_data,
                self.sample_rate,
                2  # sample width in bytes
            )
            
            # Perform speech recognition
            text = self.recognizer.recognize_google(
                audio,
                language=self.current_language
            )
            
            # Type the recognized text
            self.root.after(0, lambda: self.type_text(text))
            logger.info(f"Processed recorded audio: {text}")
        except Exception as e:
            logger.error(f"Failed to process recorded audio: {str(e)}")
    
    def show_settings(self):
        """Show settings dialog"""
        try:
            settings = tk.Toplevel(self.root)
            settings.title("Voice Settings")
            settings.geometry("300x400")
            
            # Voice selection
            ttk.Label(settings, text="Voice:").pack(pady=5)
            voices = self.engine.getProperty('voices')
            voice_var = tk.StringVar(value=voices[0].id)
            voice_menu = ttk.Combobox(settings, textvariable=voice_var)
            voice_menu['values'] = [v.id for v in voices]
            voice_menu.pack(pady=5)
            
            # Speed control
            ttk.Label(settings, text="Speed:").pack(pady=5)
            speed_var = tk.IntVar(value=self.engine.getProperty('rate'))
            speed_scale = ttk.Scale(settings, from_=100, to=300, variable=speed_var)
            speed_scale.pack(pady=5)
            
            # Volume control
            ttk.Label(settings, text="Volume:").pack(pady=5)
            volume_var = tk.DoubleVar(value=self.engine.getProperty('volume'))
            volume_scale = ttk.Scale(settings, from_=0, to=1, variable=volume_var)
            volume_scale.pack(pady=5)
            
            # Microphone selection
            ttk.Label(settings, text="Microphone:").pack(pady=5)
            mics = sr.Microphone.list_microphone_names()
            mic_var = tk.StringVar(value=mics[0] if mics else "")
            mic_menu = ttk.Combobox(settings, textvariable=mic_var)
            mic_menu['values'] = mics
            mic_menu.pack(pady=5)
            
            # Noise reduction settings
            ttk.Label(settings, text="Noise Reduction:").pack(pady=5)
            noise_var = tk.BooleanVar(value=True)
            noise_check = ttk.Checkbutton(settings, text="Enable", variable=noise_var)
            noise_check.pack(pady=5)
            
            def apply_settings():
                try:
                    self.engine.setProperty('voice', voice_var.get())
                    self.engine.setProperty('rate', speed_var.get())
                    self.engine.setProperty('volume', volume_var.get())
                    settings.destroy()
                    logger.info("Voice settings updated")
                except Exception as e:
                    logger.error(f"Failed to apply settings: {str(e)}")
                    
            ttk.Button(settings, text="Apply", command=apply_settings).pack(pady=10)
        except Exception as e:
            logger.error(f"Failed to show settings: {str(e)}")
    
    def toggle_speech_to_text(self):
        """Toggle speech-to-text functionality"""
        if self.is_listening:
            self.stop_listening()
        else:
            self.start_listening()
    
    def start_listening(self):
        """Start speech recognition"""
        try:
            self.is_listening = True
            self.stt_btn.configure(style='Active.TButton')
            
            def listen_thread():
                with sr.Microphone() as source:
                    try:
                        # Adjust for ambient noise
                        self.recognizer.adjust_for_ambient_noise(source)
                        logger.info("Adjusted for ambient noise")
                        
                        while self.is_listening:
                            try:
                                audio = self.recognizer.listen(source, timeout=1)
                                text = self.recognizer.recognize_google(audio)
                                
                                # Process audio through our audio processor
                                processed_audio = self.audio_processor.process_audio(
                                    audio.get_raw_data(),
                                    AudioFormat.RAW
                                )
                                
                                # Simulate typing the recognized text
                                self.root.after(0, lambda: self.type_text(text))
                                logger.info(f"Recognized text: {text}")
                                
                            except sr.WaitTimeoutError:
                                continue
                            except Exception as e:
                                logger.error(f"Error in speech recognition: {str(e)}")
                    except Exception as e:
                        logger.error(f"Error in microphone setup: {str(e)}")
                        self.stop_listening()
            
            threading.Thread(target=listen_thread, daemon=True).start()
            logger.info("Started speech recognition")
        except Exception as e:
            logger.error(f"Failed to start listening: {str(e)}")
            self.stop_listening()
    
    def stop_listening(self):
        """Stop speech recognition"""
        try:
            self.is_listening = False
            self.stt_btn.configure(style='Icon.TButton')
            logger.info("Stopped speech recognition")
        except Exception as e:
            logger.error(f"Failed to stop listening: {str(e)}")
    
    def start_text_to_speech(self):
        """Start text-to-speech functionality"""
        if self.is_speaking:
            self.stop_speaking()
            return
        
        try:
            # Get selected text using clipboard
            previous_clipboard = pyperclip.paste()
            pyautogui.hotkey('ctrl', 'c')
            selected_text = pyperclip.paste()
            pyperclip.copy(previous_clipboard)
            
            if not selected_text or selected_text == previous_clipboard:
                logger.info("No text selected for TTS")
                return
            
            self.is_speaking = True
            self.tts_btn.configure(style='Active.TButton')
            
            def speak_thread():
                try:
                    self.engine.say(selected_text)
                    self.engine.runAndWait()
                    self.root.after(0, self.stop_speaking)
                    logger.info("TTS completed successfully")
                except Exception as e:
                    logger.error(f"Error in TTS: {str(e)}")
                    self.root.after(0, self.stop_speaking)
            
            threading.Thread(target=speak_thread, daemon=True).start()
        except Exception as e:
            logger.error(f"Failed to start TTS: {str(e)}")
            self.stop_speaking()
    
    def stop_speaking(self):
        """Stop text-to-speech"""
        try:
            self.is_speaking = False
            self.engine.stop()
            self.tts_btn.configure(style='Icon.TButton')
            logger.info("TTS stopped")
        except Exception as e:
            logger.error(f"Failed to stop TTS: {str(e)}")
    
    def type_text(self, text: str):
        """Type the recognized text at the current cursor position"""
        try:
            pyautogui.write(text + ' ')
            logger.info(f"Typed text: {text}")
        except Exception as e:
            logger.error(f"Failed to type text: {str(e)}")

class VoicePlugin:
    """Plugin for voice-related functionality"""
    def __init__(self):
        self.widget: Optional[VoiceWidget] = None
    
    def initialize(self, root: tk.Tk):
        """Initialize the voice plugin"""
        try:
            self.widget = VoiceWidget(root)
            logger.info("VoicePlugin initialized")
        except Exception as e:
            logger.error(f"Failed to initialize VoicePlugin: {str(e)}")
            raise
    
    def cleanup(self):
        """Clean up resources"""
        try:
            if self.widget:
                self.widget.frame.destroy()
                self.widget = None
            logger.info("VoicePlugin cleaned up")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
