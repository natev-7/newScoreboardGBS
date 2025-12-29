# Scoreboard UI

Simple Tkinter scoreboard that uses the RTD packet parser from `newScoreboard.py`.

Usage

- Run the demo (no RTD device needed):

```bash
python scoreboard_ui.py --demo
```

- Listen for real RTD UDP packets on port 3000:

```bash
python scoreboard_ui.py --port 3000
```

## Running standalone Windows 11 executable
Open a Windows Command Prompt.
Navigate to location of executable.
Example for RTD serial command for COM23:
```
gbs-swim-scoreboard -h
gbs-swim-scoreboard --port COM23
```

Notes

- Requires Python 3 and Tkinter (standard on most Python installs).
- The UI imports `parse_rtd_packet` from `newScoreboard.py` in the same directory.
