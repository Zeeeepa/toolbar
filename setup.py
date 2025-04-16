from setuptools import setup, find_packages

setup(
    name="toolbar",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "PyQt6",  # For Windows UI
        "sounddevice",  # For audio recording
        "numpy",  # For audio processing
        "webrtcvad",  # Voice activity detection
        "torch",  # For TTS/STT models
        "torchaudio",  # Audio processing utilities
        "transformers",  # For TTS/STT models
    ],
    entry_points={
        "console_scripts": [
            "start_toolbar=toolbar:main",  # Updated entry point
        ],
    },
    python_requires=">=3.8",
    author="Zeeeepa",
    description="A Windows toolbar for TTS and speech-to-text functionality",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
)
