import tkinter as tk
from tkinter import font
import serial
import threading
import sys
import time

LANE_COUNT = 8

class SwimScoreboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Swim Scoreboard")
        self.configure(bg="#ffffff")
        self.geometry("700x500")
        # self.resizable(False, False)  # Allow window to be resizable
        self.custom_font = font.Font(family="Segoe UI", size=16, weight="bold")
        self.header_font = font.Font(family="Segoe UI", size=22, weight="bold")
        self._build_ui()
        # self._update_clock()
        self.bind('<Configure>', self._on_resize)

    def _build_ui(self):
        # Event Name on its own line, aligned left
        event_name_frame = tk.Frame(self, bg="#ffffff")
        event_name_frame.pack(pady=(0, 0), fill="x")
        self.event_name_label = tk.Label(
            event_name_frame,
            text="",
            font=self.header_font,
            fg="#002366",
            bg="#ffffff",
            anchor="w",           # Align text to the left
            justify="left"        # Justify left for multi-line (if needed)
        )
        self.event_name_label.pack(side="left", padx=(0, 0), fill="x", expand=True)

        # Event, Heat, and Clock on same line
        top_frame = tk.Frame(self, bg="#ffffff")
        top_frame.pack(pady=(0, 0), fill="x")
        self.event_label_label = tk.Label(top_frame, text="Event:", font=self.header_font, fg="#002366", bg="#ffffff")
        self.event_label_label.pack(side="left", padx=(0, 5))
        self.event_label = tk.Label(top_frame, text="1", font=self.header_font, fg="#002366", bg="#ffffff")
        self.event_label.pack(side="left", padx=(0, 20))
        self.heat_label = tk.Label(top_frame, text="Heat: 1", font=self.header_font, fg="#002366", bg="#ffffff")
        self.heat_label.pack(side="left", padx=(0, 20))
        self.clock_label = tk.Label(top_frame, text="", font=self.header_font, fg="#002366", bg="#ffffff")
        self.clock_label.pack(side="left", padx=(0, 20))

        # Lane headers
        header_frame = tk.Frame(self, bg="#e6e6e6")
        header_frame.pack(fill="x", padx=40)
        tk.Label(header_frame, text="Lane", font=self.custom_font, fg="#002366", bg="#e6e6e6", width=6).grid(row=0, column=0, sticky="ew")
        tk.Label(header_frame, text="Name", font=self.custom_font, fg="#002366", bg="#e6e6e6", width=18).grid(row=0, column=1, sticky="ew")
        tk.Label(header_frame, text="Team", font=self.custom_font, fg="#002366", bg="#e6e6e6", width=8).grid(row=0, column=2, sticky="ew")
        tk.Label(header_frame, text="Time", font=self.custom_font, fg="#002366", bg="#e6e6e6", width=10).grid(row=0, column=3, sticky="ew")
        tk.Label(header_frame, text="Place", font=self.custom_font, fg="#002366", bg="#e6e6e6", width=6).grid(row=0, column=4, sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)
        header_frame.grid_columnconfigure(1, weight=3)
        header_frame.grid_columnconfigure(2, weight=2)
        header_frame.grid_columnconfigure(3, weight=2)
        header_frame.grid_columnconfigure(4, weight=1)

        # Lane rows
        self.lane_rows = []
        self.lane_row_frames = []
        self.lane_rows_container = tk.Frame(self, bg="#ffffff")
        self.lane_rows_container.pack(fill="both", expand=True)
        for lane in range(1, LANE_COUNT+1):
            row_frame = tk.Frame(self.lane_rows_container, bg="#ffffff", highlightbackground="#e6e6e6", highlightthickness=2)
            row_frame.grid(row=lane-1, column=0, sticky="nsew", padx=40, pady=0)
            lane_label = tk.Label(row_frame, text=str(lane), font=self.custom_font, fg="#002366", bg="#ffffff", width=6)
            lane_label.grid(row=0, column=0, sticky="ew")
            name_label = tk.Label(row_frame, text=f"Swimmer {lane}", font=self.custom_font, fg="#002366", bg="#ffffff", width=18, anchor="w", justify="left")
            name_label.grid(row=0, column=1, sticky="ew")
            team_label = tk.Label(row_frame, text="-", font=self.custom_font, fg="#002366", bg="#ffffff", width=8, anchor="w", justify="left")
            team_label.grid(row=0, column=2, sticky="ew")
            time_label = tk.Label(row_frame, text="-", font=self.custom_font, fg="#002366", bg="#ffffff", width=10)
            time_label.grid(row=0, column=3, sticky="ew")
            place_label = tk.Label(row_frame, text="-", font=self.custom_font, fg="#002366", bg="#ffffff", width=6)
            place_label.grid(row=0, column=4, sticky="ew")
            row_frame.grid_columnconfigure(0, weight=1)
            row_frame.grid_columnconfigure(1, weight=3)
            row_frame.grid_columnconfigure(2, weight=2)
            row_frame.grid_columnconfigure(3, weight=2)
            row_frame.grid_columnconfigure(4, weight=1)
            self.lane_rows.append((name_label, team_label, time_label, place_label))
            self.lane_row_frames.append(row_frame)
        self.lane_rows_container.grid_columnconfigure(0, weight=1)

    def _update_clock(self):
        import time
        now = time.time()
        minutes = int(now // 60) % 60
        seconds = int(now % 60)
        milliseconds = int((now - int(now)) * 1000)
        self.clock_label.config(text=f"Time: {minutes:02}:{seconds:02}.{milliseconds:03}")
        self.after(50, self._update_clock)

    def update_event(self, event_num):
        self.event_label.config(text=f"Event: {event_num}")

    def update_heat(self, heat_num):
        self.heat_label.config(text=f"Heat: {heat_num}")

    def update_lane(self, lane, name=None, team=None, time=None, place=None):
        if 1 <= lane <= LANE_COUNT:
            name_label, team_label, time_label, place_label = self.lane_rows[lane-1]
            if name is not None:
                name_label.config(text=name)
            if team is not None:
                team_label.config(text=team)
            if time is not None:
                time_label.config(text=time)
            if place is not None:
                place_label.config(text=place)

    def _on_resize(self, event):
        # Calculate new font size to fill row height as much as possible
        min_font = 12
        max_font = 200
        if hasattr(self, 'lane_rows_container'):
            container_height = self.lane_rows_container.winfo_height()
            if container_height > 0:
                row_height = int(container_height / LANE_COUNT)
                # Try to fill the row height with the font (approximate, as font metrics vary)
                # Use 0.8 as a scaling factor to fill most of the row
                font_size = int(min(max_font, max(min_font, row_height * 0.5)))
                self.header_font.configure(size=font_size)
                self.custom_font.configure(size=font_size)
                # Resize row_frame heights to fill container
                for row_frame in self.lane_row_frames:
                    row_frame.configure(height=row_height)

    def start_serial(self, port='COM1', baudrate=19200, itf_path='OS2-Swimming.itf', test_file=None):
        parser = OS2FrameParser(itf_path)
        def on_frame(frame):
            # Update event and heat
            event_num = frame.get('Event Number', '').strip()
            heat_num = frame.get('Heat Number', '').strip()
            event_name = frame.get('Event Title Line 1', '').strip()
            if event_num:
                self.event_label.config(text=event_num)
            if heat_num:
                self.heat_label.config(text=f"Heat: {heat_num}")
            if event_name:
                self.event_name_label.config(text=event_name)
            # Update lanes
            for lane in range(1, LANE_COUNT+1):
                name = frame.get(f'Line {lane} Swimmer Name', '')
                team = frame.get(f'Line {lane} Team Name', '')
                time = frame.get(f'Line {lane} Split/Finish Time', '')
                place = frame.get(f'Line {lane} Place Number', '')
                self.update_lane(lane, name=name, team=team, time=time, place=place)
        def on_data(data):
            # print(f"on_data called with data: {data}, len={len(data)}")
            if len(data) == 9:
                time = data.strip()
                if (time != '0.00'):
                    self.clock_label.config(text=f"Time: {data.strip()}")
                if (time == '0.0'): # Start of new race, clear scoreboard data
                    self.event_name_label.config(text="")
                    self.event_label.config(text="")
                    self.heat_label.config(text="Heat: ")
                    for lane in range(1, LANE_COUNT+1):
                        self.update_lane(lane, name="-", time="-", place="-")
            elif len(data) == 29: # Event[4],Heat[2],Notused[21],Length=[2]
                event_num = data[0:4].strip()
                heat_num = data[4:6].strip()
                print(f"Received event/heat/time update: event={event_num}, heat={heat_num}")
                if event_num:
                    self.event_label.config(text=event_num)
                if heat_num:
                    self.heat_label.config(text=f"Heat: {heat_num}")
            elif len(data) == 30: # Event name update
                event_name = data.strip()
                print(f"Received event name update: {event_name}")
                # Only update if existing event name is not blank
                if not self.event_name_label.cget("text"):
                    self.event_name_label.config(text=event_name)
            elif len(data) == 36: # Name[15],Team[5],Lane[2],Place[3],Split/FinishTime[9],Completed[2]
                print(f"Processing lane update data: {data[0:20]} {data[20:24]}")
                name = data[0:15].strip()
                # name = name if name else None
                team = data[15:20].strip()
                lane = data[20:22].strip()
                lane = int(lane) if lane.isdigit() else None
                place = data[22:25].strip()
                # place = place if place else None
                time = data[25:34].strip()
                # time = time if time and time != '0.00' else None
                time = time if time != '0.00' else None
                print(f"Received lane update: lane={lane}, name={name}, place={place}, time={time}")
                if (lane is not None):
                    self.update_lane(lane, name=name, team=team, time=time, place=place)
            else:
                print(f"Unprocessed data: {data}, len={len(data)}")

        self.serial_receiver = SerialReceiver(port, baudrate, parser, lambda frame: self.after(0, on_frame, frame), lambda data: self.after(0, on_data, data), test_file=test_file)
        self.serial_receiver.start()

class OS2FrameParser:
    def __init__(self, itf_path):
        self.fields = self._parse_itf(itf_path)
        self.frame_length = sum(f['LENGTH'] for f in self.fields)
        print(f"Parsed ITF with fields: {self.fields}")
        print(f"Parsed ITF with frame length: {self.frame_length}")

    def _parse_itf(self, path):
        fields = []
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        field = None
        for line in lines:
            line = line.strip()
            if line.startswith('[FIELD'):
                if field:
                    fields.append(field)
                field = {}
            elif '=' in line and field is not None:
                k, v = line.split('=', 1)
                if k == 'LENGTH':
                    v = int(v)
                field[k] = v
        if field:
            fields.append(field)
        return fields

    def parse_frame(self, data):
        result = {}
        idx = 0
        for field in self.fields:
            length = field['LENGTH']
            name = field['NAME']
            result[name] = data[idx:idx+length].decode(errors='ignore').strip()
            print(f"Parsed field {name}: {result[name]}")
            idx += length
        return result

class SerialReceiver:
    def __init__(self, port, baudrate, parser, on_frame, on_data, test_file=None):
        self.test_file = test_file
        if not test_file:
            self.ser = serial.Serial(port, baudrate, timeout=1)
        self.parser = parser
        self.on_frame = on_frame
        self.on_data = on_data
        self.thread = threading.Thread(target=self._read_loop, daemon=True)
        self.running = False

    def start(self):
        self.running = True
        self.thread.start()

    def stop(self):
        self.running = False
        if hasattr(self, 'ser'):
            self.ser.close()

    def _read_loop(self):
        buffer = b''
        STX = 0x02
        ETX = 0x04
        with open('serial_log.bin', 'ab') as log_file:
            if self.test_file:
                with open(self.test_file, 'rb') as f:
                    while self.running:
                        byte = f.read(1)
                        if not byte:
                            break
                        log_file.write(byte)
                        log_file.flush()
                        buffer += byte
                        time.sleep(0.001)
                        while True:
                            start = buffer.find(bytes([STX]))
                            end = buffer.find(bytes([ETX]), start + 1)
                            if start != -1 and end != -1 and end > start:
                                frame = buffer[start + 1:end]
                                buffer = buffer[end + 1:]
                                if len(frame) == self.parser.frame_length:
                                    try:
                                        parsed = self.parser.parse_frame(frame)
                                        self.on_frame(parsed)
                                    except Exception as e:
                                        print(f"Frame parse error: {e}")
                                else:
                                    temp = frame.decode(errors='ignore')
                                    self.on_data(temp)
                            else:
                                if len(buffer) > 4096:
                                    buffer = buffer[-4096:]
                                break
            else:
                while self.running:
                    try:
                        data = self.ser.read(256)
                        if not data:
                            continue
                        log_file.write(data)
                        log_file.flush()
                        buffer += data
                        while True:
                            start = buffer.find(bytes([STX]))
                            end = buffer.find(bytes([ETX]), start + 1)
                            if start != -1 and end != -1 and end > start:
                                frame = buffer[start + 1:end]
                                buffer = buffer[end + 1:]
                                if len(frame) == self.parser.frame_length:
                                    try:
                                        parsed = self.parser.parse_frame(frame)
                                        self.on_frame(parsed)
                                    except Exception as e:
                                        print(f"Frame parse error: {e}")
                                else:
                                    temp = frame.decode(errors='ignore')
                                    self.on_data(temp)
                            else:
                                if len(buffer) > 4096:
                                    buffer = buffer[-4096:]
                                break
                    except Exception as e:
                        print(f"Serial read error: {e}")

if __name__ == "__main__":
    test_file = None
    if len(sys.argv) > 1 and sys.argv[1] == "--test-file" and len(sys.argv) > 2:
        test_file = sys.argv[2]
    app = SwimScoreboard()
    try:
        app.start_serial(port='COM23', baudrate=19200, itf_path='OS2-Swimming.itf', test_file=test_file)
    except Exception as e:
        print(f"Error starting serial: {e}")
    # Example updates
    # app.update_event(5)
    # app.update_heat(2)
    # app.update_lane(3, name="Alice Smith", time="56.78")
    # app.update_lane(5, name="Bob Lee", time="54.32")
    app.mainloop()
