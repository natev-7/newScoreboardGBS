import threading
import socket
import queue
import argparse
import time
from tkinter import Tk, Frame, Label, BOTH, LEFT, RIGHT, X

from newScoreboard import parse_rtd_packet, parse_rtd_from_serial, map_itf_parsed_to_rtd

# Color palette
BG_COLOR = "#FFFFFF"        # white background
LANE_BG_1 = "#FFFFFF"       # white
LANE_BG_2 = "#FFF59D"       # light yellow
TEXT_COLOR = "#000000"      # black text
LANE_TEXT = "#000000"       # black text on lane backgrounds


def _parse_time_to_milliseconds(s: str):
    """Try to parse a variety of time formats into milliseconds.

    Supported inputs:
    - "MM:SS.ff" or "M:SS.ff" (minutes:seconds.fraction)
    - "SS.ff" (seconds.fraction)
    - integer or numeric string -> treated as seconds
    Returns integer milliseconds or None if parsing fails.
    """
    if not s:
        return None
    s = s.strip()

    # Already in MM:SS[.frac] form
    try:
        if ":" in s:
            parts = s.split(":")
            if len(parts) == 2:
                mins = int(parts[0])
                sec_part = float(parts[1])
                total_ms = int((mins * 60 + sec_part) * 1000)
                return total_ms
            # fallback: not expected
        else:
            # Pure number, treat as seconds (may have decimal)
            val = float(s)
            total_ms = int(val * 1000)
            return total_ms
    except Exception:
        return None


def _format_ms_as_mm_ss_ms(ms: int):
    """Format milliseconds into either M:SS.CC or SS.CC.

    - If minutes >= 1: return M:SS.CC (minutes unpadded)
    - If minutes == 0: return SS.CC (seconds padded to 2, centiseconds 2)
    """
    if ms is None:
        return "---"
    total_seconds, milli = divmod(int(ms), 1000)
    mins, secs = divmod(total_seconds, 60)
    centis = milli // 10
    if mins == 0:
        return f"{secs:02d}.{centis:02d}"
    return f"{mins}:{secs:02d}.{centis:02d}"


def _split_name_and_time(raw: str):
    """Heuristic: split a raw lane string into (name, ms).

    - If a token at the end parses as a time, treat it as the time.
    - Remaining tokens form the name.
    - If nothing parses as time and the whole string parses, use that as time.
    Returns (name_str or '', ms or None).
    """
    if not raw:
        return "", None
    s = raw.strip()
    tokens = s.split()

    # Try tokens from the end to find a time token
    for i in range(len(tokens) - 1, -1, -1):
        tok = tokens[i]
        ms = _parse_time_to_milliseconds(tok)
        if ms is not None:
            name = " ".join(tokens[:i]).strip()
            return name, ms

    # If nothing found, try the whole string
    ms = _parse_time_to_milliseconds(s)
    if ms is not None:
        return "", ms

    # Otherwise treat entire string as name
    return s, None


class ScoreboardUI:
    def __init__(self, root):
        self.root = root
        root.title("Scoreboard")
        root.configure(bg=BG_COLOR)

        self.header = Frame(root, bg=BG_COLOR)
        self.header.pack(fill=X, padx=8, pady=6)

        self.event_title_1 = Label(self.header, text="Event", font=("Helvetica", 24, "bold"), bg=BG_COLOR, fg=TEXT_COLOR)
        self.event_title_1.pack(fill=X)

        self.event_title_2 = Label(self.header, text="Sub", font=("Helvetica", 16), bg=BG_COLOR, fg=TEXT_COLOR)
        self.event_title_2.pack(fill=X)

        self.time_frame = Frame(root, bg=BG_COLOR)
        self.time_frame.pack(fill=X, padx=8, pady=6)

        self.running_time = Label(self.time_frame, text="00:00.00", font=("Helvetica", 36, "bold"), bg=BG_COLOR, fg=TEXT_COLOR)
        self.running_time.pack(side=LEFT)

        self.meta_label = Label(self.time_frame, text="Event: 000  Heat: 000", font=("Helvetica", 14), bg=BG_COLOR, fg=TEXT_COLOR)
        self.meta_label.pack(side=RIGHT)

        self.lanes_frame = Frame(root, bg=BG_COLOR)
        self.lanes_frame.pack(fill=BOTH, expand=True, padx=8, pady=6)

        self.lane_labels = []         # left-side lane name labels
        self.lane_value_labels = []   # right-side lane value/time labels

        for i in range(8):
            bg = LANE_BG_1 if (i % 2 == 0) else LANE_BG_2
            f = Frame(self.lanes_frame, bd=1, relief="solid", padx=6, pady=6, bg=bg)
            f.pack(fill=X, pady=2)

            # Left label: lane number
            lane_label = Label(f, text=f"Lane {i+1}", font=("Helvetica", 18), bg=bg, fg=LANE_TEXT)
            lane_label.pack(side=LEFT)
            self.lane_labels.append(lane_label)

            # Middle label: swimmer name (left-aligned, expands)
            name_label = Label(f, text="", font=("Helvetica", 18), bg=bg, fg=LANE_TEXT, anchor="w")
            name_label.pack(side=LEFT, fill=X, expand=True, padx=(8, 8))
            if not hasattr(self, 'lane_name_labels'):
                self.lane_name_labels = []
            self.lane_name_labels.append(name_label)

            # Right label: lane time/value (right-aligned)
            value_label = Label(f, text="---", font=("Helvetica", 18), anchor="e", bg=bg, fg=LANE_TEXT)
            value_label.pack(side=RIGHT)
            self.lane_value_labels.append(value_label)

        self.q = queue.Queue()

    def start_poll(self, interval_ms=100):
        self._poll_interval_ms = interval_ms
        self._poll_queue()

    def _poll_queue(self):
        try:
            while True:
                parsed = self.q.get_nowait()
                self.update_from_parsed(parsed)
        except queue.Empty:
            pass
        self.root.after(self._poll_interval_ms, self._poll_queue)

    def update_from_parsed(self, p):
        self.event_title_1.config(text=p.get("event_title_1", ""))
        self.event_title_2.config(text=p.get("event_title_2", ""))
        self.running_time.config(text=p.get("running_time", ""))
        event_num = p.get("event_number", "")
        heat_num = p.get("heat_number", "")
        self.meta_label.config(text=f"Event: {event_num}  Heat: {heat_num}")

        for i in range(8):
            key = f"lane_{i+1}"
            raw = p.get(key, "")

            name, ms = _split_name_and_time(raw)
            if ms is None:
                # if no ms, show raw as name if name empty
                if not name:
                    name = ""
                display = "---"
            else:
                display = _format_ms_as_mm_ss_ms(ms)

            # update left lane number, middle name, and right-side time
            self.lane_labels[i].config(text=f"Lane {i+1}")
            # ensure lane_name_labels list exists (older versions may not have it)
            if hasattr(self, 'lane_name_labels'):
                self.lane_name_labels[i].config(text=name)
            self.lane_value_labels[i].config(text=display)


def udp_listener(port, out_queue, stop_event):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.bind(("", port))
    sock.settimeout(1.0)

    while not stop_event.is_set():
        try:
            data, addr = sock.recvfrom(4096)
        except socket.timeout:
            continue
        try:
            parsed = parse_rtd_packet(data)
            out_queue.put(parsed)
        except Exception:
            continue


def serial_listener(port_name, out_queue, stop_event, baudrate=9600, itf_path="OS2-Swimming.itf", interval=0.1):
    """
    Poll a serial port for RTD data and push parsed dictionaries to `out_queue`.

    This uses `parse_rtd_from_serial` from `newScoreboard.py`, which will
    attempt to read a full record (based on the .itf layout). The listener
    loops until `stop_event` is set. `interval` controls sleep between polls
    when no data is available.
    """
    while not stop_event.is_set():
        try:
            parsed = parse_rtd_from_serial(port_name, baudrate=baudrate, itf_path=itf_path)
            if parsed:
                # If parse_rtd_from_serial returns ITF-named fields, map them
                # to the RTD keys expected by the UI.
                try:
                    mapped = map_itf_parsed_to_rtd(parsed)
                except Exception:
                    mapped = parsed

                out_queue.put(mapped)
            else:
                # no data read; sleep briefly to avoid busy-loop
                time.sleep(interval)
        except Exception:
            # ignore transient errors and keep trying until stop_event
            time.sleep(interval)


def demo_feeder(out_queue, stop_event, interval=0.01):
    i = 0
    # sample swimmer names for demo
    names = [
        "Liam Smith",
        "Noah Johnson",
        "Oliver Williams",
        "Elijah Brown",
        "William Jones",
        "James Garcia",
        "Benjamin Miller",
        "Lucas Davis",
    ]

    start = time.time()
    # per-lane offsets in milliseconds
    lane_offsets_ms = [0, 120, 250, 400, 30, 180, 320, 500]

    while not stop_event.is_set():
        now = time.time()
        elapsed_ms = int((now - start) * 1000)

        parsed = {
            "running_time": _format_ms_as_mm_ss_ms(elapsed_ms),
            "event_title_1": "Demo Men's 100 Free",
            "event_title_2": "Finals",
            "event_number": f"{5:03d}",
            "heat_number": f"{2:03d}",
        }

        # generate lane times as elapsed + per-lane offset, and include the name
        for lane in range(1, 9):
            ms = elapsed_ms + lane_offsets_ms[(lane - 1) % len(lane_offsets_ms)]
            # format as seconds with two decimal places so parser will interpret
            sec = ms / 1000.0
            time_str = f"{sec:.2f}"
            parsed[f"lane_{lane}"] = f"{names[lane-1]} {time_str}"

        out_queue.put(parsed)
        i += 1
        time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description="Run scoreboard UI")
    parser.add_argument("--port", type=int, default=3000, help="UDP port to listen on")
    parser.add_argument("--demo", action="store_true", help="Run demo feeder instead of UDP")
    parser.add_argument("--serial-port", type=str, help="Serial port to read RTD from (e.g., COM3)")
    parser.add_argument("--baudrate", type=int, default=9600, help="Serial baud rate")
    parser.add_argument("--itf", type=str, default="OS2-Swimming.itf", help="Path to .itf field definition file")
    args = parser.parse_args()

    root = Tk()
    ui = ScoreboardUI(root)

    stop_event = threading.Event()

    # Priority: demo -> serial -> udp
    if args.demo:
        t = threading.Thread(target=demo_feeder, args=(ui.q, stop_event), daemon=True)
        t.start()
    elif args.serial_port:
        t = threading.Thread(
            target=serial_listener,
            args=(args.serial_port, ui.q, stop_event),
            kwargs={"baudrate": args.baudrate, "itf_path": args.itf},
            daemon=True,
        )
        t.start()
    else:
        t = threading.Thread(target=udp_listener, args=(args.port, ui.q, stop_event), daemon=True)
        t.start()

    ui.start_poll(10)

    try:
        root.mainloop()
    finally:
        stop_event.set()


if __name__ == "__main__":
    main()
