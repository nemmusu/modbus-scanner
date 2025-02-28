#!/usr/bin/env python3
"""
modbus_scanner.py

This script scans the RAW range for selected Modbus register categories.
The possible categories are:
    - coil:         Coil (bit R/W)                  : Modbus Address 00001-09999, RAW: 0-9998, Function 01
    - discrete:     Input Discrete (bit R)          : Modbus Address 10001-19999, RAW: 0-9998, Function 02
    - holding:      Holding Registers (16-bit R/W)  : Modbus Address 40001-49999, RAW: 0-9998, Function 03
    - input:        Input Registers (16-bit R)      : Modbus Address 30001-39999, RAW: 0-9998, Function 04

The script scans the RAW range from 0 to 9998 in blocks (default 50 registers per request)
and waits a delay (default 4.0 seconds) after each block to avoid overloading the device.
Logs are written in real time to the output file (if specified).

Usage:
  ./modbus_scanner.py --ip <IP_TARGET> [--port <PORT>] [--slave <ID>] [--block <block_size>] [--delay <seconds>] [--category <category1> <category2> ...] [--output report.txt]

Example:
  ./modbus_scanner.py --ip 192.168.1.100 --port 502 --slave 1 --block 50 --delay 4 --category holding input --output modbus_report.txt
"""

import argparse
import time
import math
from pymodbus.client import ModbusTcpClient
import sys

def parse_args():
    parser = argparse.ArgumentParser(
        description="Scan Modbus register categories with real-time logging (plain text output)"
    )
    parser.add_argument("--ip", required=True, help="IP address of the Modbus device")
    parser.add_argument("--port", type=int, default=502, help="Modbus port (default 502)")
    parser.add_argument("--slave", type=int, default=1, help="Slave ID (default 1)")
    parser.add_argument("--block", type=int, default=50, help="Block size for scanning (default 50)")
    parser.add_argument("--delay", type=float, default=4.0, help="Delay in seconds after each block (default 4.0 sec)")
    parser.add_argument("--category", nargs="+", choices=["coil", "discrete", "holding", "input"],
                        help="Categories to scan. If omitted, all categories are scanned.")
    parser.add_argument("--output", help="Plain text output file (if omitted, prints to screen)", default="")
    return parser.parse_args()

def static_register_table_plain():
    table = (
        "Register Type                 | Modbus Address   | RAW Address (without offset) | Modbus Function\n"
        "--------------------------------|------------------|------------------------------|-----------------\n"
        "Coil (bit R/W)                 | 00001-09999      | 0-9998                       | 01\n"
        "Input Discrete (bit R)         | 10001-19999      | 0-9998                       | 02\n"
        "Holding Registers (16-bit R/W) | 40001-49999      | 0-9998                       | 03\n"
        "Input Registers (16-bit R)     | 30001-39999      | 0-9998                       | 04"
    )
    return table

def scan_category(client, block_size, delay, max_raw=9999, function_type="coil", slave=1, log_file=None):
    """
    Scans the RAW range from 0 to max_raw-1 in blocks, using the corresponding Modbus function.
    function_type can be "coil", "discrete", "holding", or "input".
    Inserts a delay after each block to avoid overloading the device.
    If log_file is specified, writes log messages in real time.
    Returns a list of tuples (modbus_address, value).
    """
    results = []
    if function_type == "coil":
        offset = 1
    elif function_type == "discrete":
        offset = 10001
    elif function_type == "holding":
        offset = 40001
    elif function_type == "input":
        offset = 30001
    else:
        return results

    total_blocks = math.ceil(max_raw / block_size)
    for idx, raw in enumerate(range(0, max_raw, block_size)):
        count = min(block_size, max_raw - raw)
        modbus_start = raw + offset
        modbus_end = raw + count - 1 + offset
        progress_msg = f"[{function_type.upper()}] Scanning block {idx+1}/{total_blocks} (RAW {raw}-{raw+count-1} -> Modbus {modbus_start}-{modbus_end})"
        print(progress_msg, end="\r", flush=True)
        if log_file:
            log_file.write(progress_msg + "\n")
            log_file.flush()
        if function_type == "coil":
            response = client.read_coils(raw, count, unit=slave)
        elif function_type == "discrete":
            response = client.read_discrete_inputs(raw, count, unit=slave)
        elif function_type == "holding":
            response = client.read_holding_registers(raw, count, unit=slave)
        elif function_type == "input":
            response = client.read_input_registers(raw, count, unit=slave)
        
        if not response.isError():
            try:
                registers = response.registers
            except AttributeError:
                registers = response.bits
            for i, val in enumerate(registers):
                modbus_addr = raw + i + offset
                results.append((modbus_addr, val))
        time.sleep(delay)
    completion_msg = f"[{function_type.upper()}] Scanning complete. Registers read: {len(results)}"
    print(completion_msg)
    if log_file:
        log_file.write(completion_msg + "\n")
        log_file.flush()
    return results

def generate_plain_report(ip, port, slave, block_size, delay, scan_results):
    lines = []
    lines.append(f"Modbus Scan Report for {ip}:{port} (Slave ID: {slave})")
    lines.append("=" * 60)
    lines.append("Modbus Register Categories Table:")
    lines.append(static_register_table_plain())
    lines.append("")
    for category, results in scan_results.items():
        lines.append(f"Category: {category.capitalize()}")
        if results:
            lines.append("Modbus Address   | Value")
            lines.append("-----------------|--------")
            for addr, val in results:
                lines.append(f"{addr:<16} | {val}")
        else:
            lines.append("No data found.")
        lines.append("")
    lines.append(f"(Scan performed with blocks of {block_size} registers and a delay of {delay} seconds per block)")
    return "\n".join(lines)

def main():
    args = parse_args()
    
    log_file = None
    if args.output:
        log_file = open(args.output, "a", encoding="utf-8")
    
    client = ModbusTcpClient(args.ip, args.port)
    if not client.connect():
        print(f"Error: unable to connect to {args.ip}:{args.port}")
        sys.exit(1)
    
    categories = args.category if args.category is not None else ["coil", "discrete", "holding", "input"]
    scan_results = {}

    for cat in categories:
        msg = f"\nStarting scan for category: {cat.upper()}"
        print(msg)
        if log_file:
            log_file.write(msg + "\n")
            log_file.flush()
        scan_results[cat] = scan_category(client, block_size=args.block, delay=args.delay, max_raw=9999, function_type=cat, slave=args.slave, log_file=log_file)
    
    client.close()

    if log_file:
        log_file.close()

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            report = generate_plain_report(args.ip, args.port, args.slave, args.block, args.delay, scan_results)
            f.write(report + "\n")
        print(f"\nReport written in {args.output}")
    else:
        print("\n" + generate_plain_report(args.ip, args.port, args.slave, args.block, args.delay, scan_results))


if __name__ == "__main__":
    main()
