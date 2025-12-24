import socket
import os

# -------------------------------------------------------------------
# RTD FIELD DEFINITIONS (from OmniSport 2000 Appendix D)
# Each field is fixed-width ASCII. The parser slices the packet
# according to these lengths.
# -------------------------------------------------------------------
RTD_FIELDS = [
    ("running_time", 9),      # e.g., "00:24.53"
    ("event_title_1", 30),    # e.g., "Men's 100 Free"
    ("event_title_2", 30),    # e.g., "Finals"
    ("event_number", 3),      # e.g., "005"
    ("heat_number", 3),       # e.g., "002"
    ("lane_1", 9),
    ("lane_2", 9),
    ("lane_3", 9),
    ("lane_4", 9),
    ("lane_5", 9),
    ("lane_6", 9),
    ("lane_7", 9),
    ("lane_8", 9),
]


def parse_rtd_packet(data):
    """
    Parse a fixed-width RTD packet into a dictionary.

    The OmniSport 2000 RTD format uses ASCII fields with fixed lengths.
    This function walks through the packet, slicing out each field
    according to the RTD_FIELDS table above.
    """
    pos = 0
    parsed = {}

    for field_name, length in RTD_FIELDS:
        # Extract the exact slice for this field
        raw = data[pos:pos+length].decode(errors="ignore")

        # Strip whitespace and store
        parsed[field_name] = raw.strip()

        # Move the cursor forward
        pos += length

    return parsed


def load_itf_field_defs(itf_path="OS2-Swimming.itf"):
    """
    Load field definitions from an .itf file and return a list of
    (field_name, length) tuples in order.

    The function looks for lines like `NAME=...` and `LENGTH=...`
    in each FIELD block. If the file is not found a FileNotFoundError
    is raised.
    """
    if not os.path.exists(itf_path):
        raise FileNotFoundError(f"ITF file not found: {itf_path}")

    fields = []
    current_name = None

    with open(itf_path, "r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue

            if line.startswith("NAME="):
                # NAME=... (may contain spaces)
                current_name = line.split("=", 1)[1]

            elif line.startswith("LENGTH="):
                # LENGTH=NNN
                try:
                    length = int(line.split("=", 1)[1])
                except ValueError:
                    continue

                # If a NAME was not seen immediately before, use a generic
                # name to preserve field order.
                if current_name is None:
                    current_name = f"field_{len(fields)+1}"

                fields.append((current_name, length))
                current_name = None

    return fields


def parse_rtd_bytes_with_defs(data, field_defs):
    """
    Parse raw RTD bytes using a list of (name, length) field_defs.

    Returns an ordered dict-like mapping (regular dict preserving order)
    from field name to stripped text value.
    """
    parsed = {}
    pos = 0

    for name, length in field_defs:
        raw = data[pos:pos + length].decode("ascii", errors="ignore")
        parsed[name.strip()] = raw.rstrip()
        pos += length

    return parsed


def map_itf_parsed_to_rtd(itf_parsed: dict):
    """
    Map a parsed ITF field dictionary (keys are the ITF `NAME=` values)
    to the RTD keys used by the UI (`running_time`, `event_title_1`,
    `event_title_2`, `event_number`, `heat_number`, `lane_1`..`lane_8`).

    The function will look for common ITF field names and build
    per-lane strings of the form "<Swimmer Name> <Split/Finish Time>"
    when both are present. Missing values become empty strings.
    """
    r = {}

    # Top-level mappings
    r["running_time"] = itf_parsed.get("Running Time", "").strip()
    r["event_title_1"] = itf_parsed.get("Event Title Line 1", "").strip()
    r["event_title_2"] = itf_parsed.get("Event Title Line 2", "").strip()
    # fallback: combined title field
    if not r["event_title_1"]:
        r["event_title_1"] = itf_parsed.get("Event Title Lines 1 & 2", "").strip()

    r["event_number"] = itf_parsed.get("Event Number", "").strip()
    r["heat_number"] = itf_parsed.get("Heat Number", "").strip()

    # Build lanes 1..8 from the per-line fields in the ITF layout
    for i in range(1, 9):
        name_key = f"Line {i} Swimmer Name"
        time_key = f"Line {i} Split/Finish Time"
        # Some ITF templates might use slightly different keys; try a few fallbacks
        name = itf_parsed.get(name_key, "").strip()
        time = itf_parsed.get(time_key, "").strip()

        # If no swimmer name present, try the single-line fields
        if not name:
            name = itf_parsed.get("Single Line Swimmer Name", "").strip()

        if name and time:
            value = f"{name} {time}"
        elif name:
            value = name
        elif time:
            value = time
        else:
            value = ""

        r[f"lane_{i}"] = value

    return r


def parse_rtd_from_serial(port, baudrate=9600, itf_path="OS2-Swimming.itf", timeout=1.0):
    """
    Open a serial port, read a single RTD packet (based on the total
    length described in `itf_path`), and return the parsed fields.

    Requires `pyserial` installed. Parameters:
    - port: serial port name (e.g., 'COM3' on Windows)
    - baudrate: serial baud rate
    - itf_path: path to the .itf file describing field lengths
    - timeout: read timeout in seconds

    Example:
        parsed = parse_rtd_from_serial('COM3', 9600)
    """
    try:
        import serial
    except Exception as e:
        raise ImportError("pyserial is required for reading from serial ports") from e

    field_defs = load_itf_field_defs(itf_path)
    total_len = sum(length for _, length in field_defs)

    ser = serial.Serial(port, baudrate=baudrate, timeout=timeout)
    try:
        # read exactly total_len bytes (serial.read will return fewer on timeout)
        data = ser.read(total_len)
    finally:
        ser.close()

    if not data:
        return {}

    # If we got less than expected, still attempt to parse what we have
    return parse_rtd_bytes_with_defs(data, field_defs)


def listen_udp(port=3000):
    """
    Listen for UDP broadcast packets on the given port.

    This works on Windows, Linux, and macOS.
    The OmniSport 2000 (if configured for Ethernet RTD) will broadcast
    packets to this port. If the console uses a different port, change it.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Allow reusing the port if the script is restarted
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Allow receiving broadcast packets
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    # Bind to all interfaces on the given port
    sock.bind(("", port))

    print(f"Listening for RTD UDP packets on port {port}...")

    while True:
        # Receive up to 4096 bytes (RTD packets are usually < 300 bytes)
        data, addr = sock.recvfrom(4096)

        print(f"\nPacket received from {addr}")
        # Decode the raw bytes to an ASCII-safe string. Non-ASCII
        # bytes are shown with backslash escapes so the binary
        # content remains visible.
        print(data.decode('ascii', errors='backslashreplace'))

        # Parse the RTD payload
        parsed = parse_rtd_packet(data)

        # Print each field in a clean, readable format
        # for k, v in parsed.items():
        #     print(f"{k:15}: {v}")


if __name__ == "__main__":
    listen_udp(21003)