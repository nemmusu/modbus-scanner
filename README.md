# Modbus Scanner

This Modbus Scanner performs a full scan of Modbus register categories on a target device, allowing users to select specific categories to scan:

- **coil**: Coil (bit R/W) – Modbus Address: 00001-09999, RAW: 0-9998, Function: 01
- **discrete**: Input Discrete (bit R) – Modbus Address: 10001-19999, RAW: 0-9998, Function: 02
- **holding**: Holding Registers (16-bit R/W) – Modbus Address: 40001-49999, RAW: 0-9998, Function: 03
- **input**: Input Registers (16-bit R) – Modbus Address: 30001-39999, RAW: 0-9998, Function: 04

The script connects to the Modbus device via `pymodbus` and scans the RAW range (0-9998) in blocks (default 50 registers per request). It waits for a delay (default 4 second) after each block to avoid overwhelming the device.

Logs are written in real-time to an output file (if specified).

## Installation

1. Clone this repository or download `modbus_scanner.py`:
   ```bash
   git clone https://github.com/nemmusu/modbus-scanner.git
   cd modbus-scanner
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the script with the required parameters. Example:

```bash
./modbus_scanner.py --ip 192.168.1.100 --port 502 --slave 1 --block 50 --delay 4 --category holding input --output modbus_report.txt
```

### Main Parameters

- `--ip`: Modbus device IP address (required).
- `--port`: Modbus port (default: 502).
- `--slave`: Slave ID (default: 1).
- `--block`: Block size for scanning (default: 50 registers per request).
- `--delay`: Delay (in seconds) after each block (default: 4 seconds).
- `--category`: Select categories to scan (`coil`, `discrete`, `holding`, `input`). If omitted, all are scanned.
- `--output`: Output file in plain text format. If omitted, output is displayed in the console.
  **Note:** Logs are written in real-time in *append* mode.

## Logs and Report

During execution, the script displays progress for each category, showing the current block and the RAW range converted to Modbus addresses (e.g., `raw 0-49 -> modbus 40001-40050` for Holding Registers).
Logs are written in real-time in *append* mode.


