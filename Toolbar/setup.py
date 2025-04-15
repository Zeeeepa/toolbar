from setuptools import setup, find_packages

setup(
    name="Toolbar",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "PyQt5>=5.15.9",
        "requests>=2.31.0",
        "pynput>=1.7.6",
        "pyautogui>=0.9.54",
        "keyboard>=0.13.5",
        "pyperclip>=1.8.2",
        "python-dotenv>=0.15.0",
        "PyGithub>=1.59.1",
        "pyngrok>=6.0.0",
    ],
    entry_points={
        'console_scripts': [
            'toolbar=Toolbar.main:main',
        ],
    },
    package_data={
        'Toolbar': [
            'icons/*.svg',
            'icons/*.png',
            'Prompts/*.prompt',
            'Prompts/*.promptp',
        ],
    },
    include_package_data=True,
)
