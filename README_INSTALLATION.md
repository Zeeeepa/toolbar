# Toolbar Installation Guide

This guide will help you properly install and run the Toolbar application.

## Installation Issues

If you're seeing errors like:
```
ModuleNotFoundError: No module named 'Toolbar'
```
or
```
NameError: name 'Toolbar' is not defined
```

This means the Toolbar package is not properly installed or not in your Python path.

## Installation Methods

### Method 1: Using the Fix Script (Recommended)

1. Navigate to the toolkit directory (where the `Toolbar` folder is located)
2. Run the fix script:
   ```
   python fix_toolbar_installation.py
   ```
3. The script will automatically install the package in development mode and verify the installation

### Method 2: Manual Installation

1. Navigate to the toolkit directory (where the `Toolbar` folder is located)
2. Install the package in development mode:
   ```
   pip install -e .
   ```
3. Verify the installation:
   ```python
   import Toolbar
   from Toolbar.ui.toolbar_ui import Toolbar
   print("Installation successful!")
   ```

### Method 3: Running Without Installation

If you prefer not to install the package, you can use the provided `run_toolbar.py` script:
```
python run_toolbar.py
```

## Troubleshooting

If you continue to experience issues:

1. Make sure you're running the commands from the toolkit directory (where the `Toolbar` folder is located)
2. Check your Python version (Python 3.8 or higher is required)
3. Verify that all dependencies are installed:
   ```
   pip install -r requirements.txt
   ```
4. If using a virtual environment, make sure it's activated
5. Try reinstalling the package:
   ```
   pip uninstall Toolbar
   pip install -e .
   ```

## System Requirements

- Python 3.8 or higher
- PyQt5 5.15.0 or higher
- Other dependencies as listed in setup.py
