"""
CLI interface and interactive wizard for flatjson.
Zephyrus Labs (https://zephyrus-labs.tech/)
Lead Developer: Shubham Sharma
"""
import argparse
import os
import sys
from typing import List, Optional

from flatjson import __version__
from flatjson.core import (
    infer_schema,
    iter_json_records,
    json_file_to_csv,
    flatten_record,
)

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_banner():
    banner = f"""{CYAN}{BOLD}
╔══════════════════════════════════════════════════════════════╗
║               flatjson-cli  v{__version__}                          ║
║     Deep JSON & JSONL to Tabular CSV Flattener               ║
║     Zephyrus Labs (https://zephyrus-labs.tech/)              ║
╚══════════════════════════════════════════════════════════════╝{RESET}"""
    print(banner)


def display_schema_table(schema: List[dict]):
    print(f"\n{BOLD}Discovered Schema Summary ({len(schema)} fields):{RESET}")
    print("-" * 75)
    print(f"{'Field Name':<35} {'Type':<15} {'Sample Value'}")
    print("-" * 75)
    for field in schema:
        sample_str = str(field["sample"])
        if len(sample_str) > 22:
            sample_str = sample_str[:19] + "..."
        print(f"{field['name']:<35} {field['type']:<15} {sample_str}")
    print("-" * 75)


def run_interactive_wizard() -> int:
    print_banner()
    print(f"\n{BOLD}Welcome to the flatjson Interactive Wizard!{RESET}\n")

    # 1. File Path
    while True:
        file_path = input(f"{BOLD}Enter path to JSON / JSONL file:{RESET} ").strip()
        if not file_path:
            print(f"{RED}File path cannot be empty.{RESET}")
            continue
        if not os.path.exists(file_path):
            print(f"{RED}File not found: '{file_path}'. Please try again.{RESET}")
            continue
        break

    # 2. Action Choice
    print(f"\n{BOLD}Select Operation:{RESET}")
    print("  [1] Flatten to CSV (Standard)")
    print("  [2] View Schema Summary (Zero CSV generated)")
    print("  [3] Preview First 5 Flattened Records")
    action_choice = input(f"{BOLD}Choose [1/2/3] (default: 1):{RESET} ").strip() or "1"

    if action_choice == "2":
        try:
            records = iter_json_records(file_path)
            schema = infer_schema(records)
            display_schema_table(schema)
            return 0
        except Exception as e:
            print(f"{RED}Error extracting schema: {e}{RESET}")
            return 1

    # 3. Separator Choice
    print(f"\n{BOLD}Choose Key Separator:{RESET}")
    print("  [1] '.'  (e.g., user.address.city) [Default]")
    print("  [2] '_'  (e.g., user_address_city)")
    print("  [3] Custom delimiter")
    sep_choice = input(f"{BOLD}Choose [1/2/3] (default: 1):{RESET} ").strip() or "1"
    if sep_choice == "2":
        sep = "_"
    elif sep_choice == "3":
        sep = input("Enter custom separator: ") or "."
    else:
        sep = "."

    # 4. Array Strategy
    print(f"\n{BOLD}Choose Array Strategy:{RESET}")
    print("  [1] 'join'    - Semicolon-separated string (e.g. 'admin; editor') [Default]")
    print("  [2] 'index'   - Unroll to indexed columns (e.g. roles.0, roles.1)")
    print("  [3] 'explode' - Duplicate rows for each array item")
    arr_choice = input(f"{BOLD}Choose [1/2/3] (default: 1):{RESET} ").strip() or "1"
    if arr_choice == "2":
        array_mode = "index"
    elif arr_choice == "3":
        array_mode = "explode"
    else:
        array_mode = "join"

    if action_choice == "3":
        try:
            print(f"\n{BOLD}Previewing first records with sep='{sep}', array_mode='{array_mode}':{RESET}")
            for idx, rec in enumerate(iter_json_records(file_path)):
                if idx >= 5:
                    break
                flat = flatten_record(rec, separator=sep, array_strategy=array_mode)
                print(f"\n--- Record {idx + 1} ---")
                for k, v in list(flat.items())[:10]:
                    print(f"  {k}: {v}")
                if len(flat) > 10:
                    print(f"  ... and {len(flat) - 10} more fields")
            return 0
        except Exception as e:
            print(f"{RED}Error previewing: {e}{RESET}")
            return 1

    # 5. Output CSV Path
    base, _ = os.path.splitext(file_path)
    default_out = f"{base}.csv"
    out_path = input(f"\n{BOLD}Enter output CSV path (default: {default_out}):{RESET} ").strip() or default_out

    if os.path.exists(out_path):
        overwrite = input(f"{YELLOW}File '{out_path}' exists. Overwrite? [y/N]:{RESET} ").strip().lower()
        if overwrite != "y":
            print(f"{YELLOW}Operation cancelled.{RESET}")
            return 0

    try:
        print(f"\n{CYAN}Flattening data...{RESET}")
        stats = json_file_to_csv(file_path, out_path, separator=sep, array_strategy=array_mode)
        print(f"{GREEN}✓ Successfully flattened {stats['records']} records into {stats['columns']} columns.{RESET}")
        print(f"{GREEN}✓ CSV saved cleanly to: {stats['output_path']}{RESET}\n")
        return 0
    except Exception as e:
        print(f"{RED}Error processing file: {e}{RESET}")
        return 1


def main(argv: Optional[List[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        prog="flatjson",
        description="Deep JSON & JSONL to Tabular CSV Flattener by Zephyrus Labs",
    )
    parser.add_argument(
        "input",
        nargs="?",
        help="Path to input .json or .jsonl file",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Target CSV output path (default: <input>.csv)",
    )
    parser.add_argument(
        "-s",
        "--sep",
        default=".",
        help="Delimiter for nested keys (e.g. '.' or '_', default: '.')",
    )
    parser.add_argument(
        "-a",
        "--array-mode",
        choices=["join", "index", "explode"],
        default="join",
        help="Array handling mode: join, index, explode (default: join)",
    )
    parser.add_argument(
        "--schema",
        action="store_true",
        help="Display schema summary without exporting CSV",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Overwrite existing output CSV file without confirmation",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress banner and non-essential progress messages",
    )
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Launch interactive wizard",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"flatjson-cli {__version__} by Zephyrus Labs",
    )

    args = parser.parse_args(argv)

    if args.interactive or not args.input:
        return run_interactive_wizard()

    input_file = args.input
    if not os.path.exists(input_file):
        print(f"{RED}Error: Input file '{input_file}' not found.{RESET}", file=sys.stderr)
        return 1

    if args.schema:
        try:
            records = iter_json_records(input_file)
            schema = infer_schema(records, separator=args.sep)
            display_schema_table(schema)
            return 0
        except Exception as e:
            print(f"{RED}Error extracting schema: {e}{RESET}", file=sys.stderr)
            return 1

    output_file = args.output
    if not output_file:
        base, _ = os.path.splitext(input_file)
        output_file = f"{base}.csv"

    if os.path.exists(output_file) and not args.force:
        print(f"{RED}Error: Output file '{output_file}' already exists. Use -f/--force to overwrite.{RESET}", file=sys.stderr)
        return 1

    try:
        stats = json_file_to_csv(
            input_path=input_file,
            output_path=output_file,
            separator=args.sep,
            array_strategy=args.array_mode,
        )
        if not args.quiet:
            print(f"{GREEN}✓ Successfully flattened {stats['records']} records into {stats['columns']} columns.{RESET}")
            print(f"{GREEN}✓ Output written to: {stats['output_path']}{RESET}")
        return 0
    except Exception as e:
        print(f"{RED}Error during conversion: {e}{RESET}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
