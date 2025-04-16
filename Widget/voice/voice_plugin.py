import tkinter as tk
from tkinter import ttk
import pyttsx3
import speech_recognition as sr
import threading
from typing import Callable, Optional
import pyperclip
import pyautogui
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
            
            # Create and style buttons
            self.create_buttons()
            self.setup_styles()
            
            # Configure keyboard shortcuts
            self.setup_shortcuts()
            
            logger.info("VoiceWidget initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize VoiceWidget: {str(e)}")
            raise
        
    def setup_styles(self):
        """Set up widget styles"""
        try:
            style = ttk.Style()
            style.configure('Icon.TButton', padding=2)
            style.configure('Active.TButton',
                          background='#007AFF',
                          foreground='white')
            logger.info("Widget styles configured")
        except Exception as e:
            logger.error(f"Failed to setup styles: {str(e)}")
    
    def setup_shortcuts(self):
        """Set up keyboard shortcuts"""
        try:
            keyboard.add_hotkey('ctrl+shift+s', self.toggle_speech_to_text)
            keyboard.add_hotkey('ctrl+shift+t', self.start_text_to_speech)
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
            logger.info("Buttons created successfully")
        except Exception as e:
            logger.error(f"Failed to create buttons: {str(e)}")
    
    def show_settings(self):
        """Show settings dialog"""
        try:
            settings = tk.Toplevel(self.root)
            settings.title("Voice Settings")
            settings.geometry("300x250")
            
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
            
            # Microphone selection
            ttk.Label(settings, text="Microphone:").pack(pady=5)
            mics = sr.Microphone.list_microphone_names()
            mic_var = tk.StringVar(value=mics[0] if mics else "")
            mic_menu = ttk.Combobox(settings, textvariable=mic_var)
            mic_menu['values'] = mics
            mic_menu.pack(pady=5)
            
            def apply_settings():
                try:
                    self.engine.setProperty('voice', voice_var.get())
                    self.engine.setProperty('rate', speed_var.get())
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
