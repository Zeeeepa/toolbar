import tkinter as tk
from tkinter import ttk
import pyttsx3
import speech_recognition as sr
import threading
import keyboard
from typing import Callable, Optional
import pyperclip
import pyautogui

class VoiceWidget:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.frame = ttk.Frame(root)
        self.frame.pack(side=tk.TOP, fill=tk.X)
        
        # Initialize engines
        self.engine = pyttsx3.init()
        self.recognizer = sr.Recognizer()
        
        # State variables
        self.is_listening = False
        self.is_speaking = False
        
        # Create and style buttons
        self.create_buttons()
        self.setup_styles()
        
        # Configure keyboard shortcuts
        keyboard.add_hotkey('ctrl+shift+s', self.toggle_speech_to_text)
        keyboard.add_hotkey('ctrl+shift+t', self.start_text_to_speech)
        
    def setup_styles(self):
        style = ttk.Style()
        style.configure('Icon.TButton', padding=2)
        style.configure('Active.TButton',
                       background='#007AFF',
                       foreground='white')
    
    def create_buttons(self):
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
    
    def show_settings(self):
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
        mic_var = tk.StringVar(value=mics[0])
        mic_menu = ttk.Combobox(settings, textvariable=mic_var)
        mic_menu['values'] = mics
        mic_menu.pack(pady=5)
        
        def apply_settings():
            self.engine.setProperty('voice', voice_var.get())
            self.engine.setProperty('rate', speed_var.get())
            settings.destroy()
            
        ttk.Button(settings, text="Apply", command=apply_settings).pack(pady=10)
    
    def toggle_speech_to_text(self):
        if self.is_listening:
            self.stop_listening()
        else:
            self.start_listening()
    
    def start_listening(self):
        self.is_listening = True
        self.stt_btn.configure(style='Active.TButton')
        
        def listen_thread():
            with sr.Microphone() as source:
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source)
                
                while self.is_listening:
                    try:
                        audio = self.recognizer.listen(source, timeout=1)
                        text = self.recognizer.recognize_google(audio)
                        
                        # Simulate typing the recognized text
                        self.root.after(0, lambda: self.type_text(text))
                        
                    except sr.WaitTimeoutError:
                        continue
                    except Exception as e:
                        print(f"Error in speech recognition: {e}")
        
        threading.Thread(target=listen_thread, daemon=True).start()
    
    def stop_listening(self):
        self.is_listening = False
        self.stt_btn.configure(style='Icon.TButton')
    
    def start_text_to_speech(self):
        if self.is_speaking:
            self.stop_speaking()
            return
        
        # Get selected text using clipboard
        previous_clipboard = pyperclip.paste()
        pyautogui.hotkey('ctrl', 'c')
        selected_text = pyperclip.paste()
        pyperclip.copy(previous_clipboard)
        
        if not selected_text or selected_text == previous_clipboard:
            return
        
        self.is_speaking = True
        self.tts_btn.configure(style='Active.TButton')
        
        def speak_thread():
            self.engine.say(selected_text)
            self.engine.runAndWait()
            self.root.after(0, self.stop_speaking)
        
        threading.Thread(target=speak_thread, daemon=True).start()
    
    def stop_speaking(self):
        self.is_speaking = False
        self.engine.stop()
        self.tts_btn.configure(style='Icon.TButton')
    
    def type_text(self, text: str):
        """Type the recognized text at the current cursor position"""
        pyautogui.write(text + ' ')

class VoicePlugin:
    def __init__(self):
        self.widget = None
    
    def initialize(self, root: tk.Tk):
        self.widget = VoiceWidget(root)
    
    def cleanup(self):
        if self.widget:
            self.widget.frame.destroy()
            self.widget = None
