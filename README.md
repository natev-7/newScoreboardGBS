# Scoreboard UI

Simple Tkinter scoreboard that listens to RTD data from the RTD serial port of the Daktronics OmniSports 2000 console.
Given the current priority, the main support is for the Glenbrook South High School swimming scoreboard (gbs-swim-scoreboard.exe). Only the RTD serial port has been tested so far.

## Running standalone Windows 11 executable
Open a Windows Command Prompt.
Navigate to location of executable.
Example for RTD serial command for COM23:
```
gbs-swim-scoreboard.exe --port COM23
```

## Development
There are two main versions of the scoreboard being developed:
- scoreboard_ui.py
- gbs-swim-scoreboard.py

Usage

- Run the demo (no RTD device needed):

```bash
python scoreboard_ui.py --demo
```

- Listen for real RTD UDP packets on port 3000:

```bash
python scoreboard_ui.py --port 3000
```



Notes

- Requires Python 3 and Tkinter (standard on most Python installs).
