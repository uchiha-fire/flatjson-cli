# flatjson-cli

[![PyPI version](https://img.shields.io/pypi/v/flatjson-cli.svg)](https://pypi.org/project/flatjson-cli/)
[![Python versions](https://img.shields.io/pypi/pyversions/flatjson-cli.svg)](https://pypi.org/project/flatjson-cli/)
[![GitHub stars](https://img.shields.io/github/stars/uchiha-fire/flatjson-cli?style=social)](https://github.com/uchiha-fire/flatjson-cli)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Shubham%20Sharma-0A66C2.svg?style=flat&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/shubham-sharma-28487819b/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Zephyrus Labs](https://img.shields.io/badge/Developed%20by-Zephyrus%20Labs-6366f1.svg)](https://zephyrus-labs.tech/)

A fast, memory-efficient deep JSON and JSONL to tabular CSV flattener with schema inspection by **[Zephyrus Labs](https://zephyrus-labs.tech/)** for Linux, macOS, and Windows.

---

## Features

- ⚡ **Zero External Dependencies**: Pure Python standard library implementation.
- 🗂️ **Nested Structure Unrolling**: Recursively transforms deeply nested objects into flat dot-notation columns (`user.profile.address.city`).
- 🔄 **Multiple Array Handling Strategies**:
  - `join`: Concatenates list items with semicolons (`"admin; editor"`).
  - `index`: Unrolls list items into dedicated indexed columns (`roles.0`, `roles.1`).
  - `explode`: Duplicates records for relational unnesting of array items.
- 📊 **Streaming & JSONL Support**: Streams large `.jsonl` / `.ndjson` files without exhausting system RAM.
- 🔍 **Token-Saving Schema Discovery**: Inspects field names, inferred types, and sample values without generating full CSV files.
- 🧙 **Interactive Terminal Wizard**: User-friendly interactive mode with file selection, strategy picking, and real-time conversion stats.

---

## Installation

```bash
pip install flatjson-cli
```

Or install the latest development version directly from GitHub:

```bash
pip install git+https://github.com/uchiha-fire/flatjson-cli.git
```

---

## Interactive Mode

Simply run `flatjson` without arguments or pass `--interactive` to launch the step-by-step wizard:

```bash
flatjson
```

```text
╔══════════════════════════════════════════════════════════════╗
║               flatjson-cli  v0.1.0                           ║
║     Deep JSON & JSONL to Tabular CSV Flattener               ║
║     Zephyrus Labs (https://zephyrus-labs.tech/)              ║
╚══════════════════════════════════════════════════════════════╝

Welcome to the flatjson Interactive Wizard!

Enter path to JSON / JSONL file: telemetry.jsonl

Select Operation:
  [1] Flatten to CSV (Standard)
  [2] View Schema Summary (Zero CSV generated)
  [3] Preview First 5 Flattened Records
Choose [1/2/3] (default: 1): 1

Choose Key Separator:
  [1] '.'  (e.g., user.address.city) [Default]
  [2] '_'  (e.g., user_address_city)
  [3] Custom delimiter
Choose [1/2/3] (default: 1): 1

Choose Array Strategy:
  [1] 'join'    - Semicolon-separated string (e.g. 'admin; editor') [Default]
  [2] 'index'   - Unroll to indexed columns (e.g. roles.0, roles.1)
  [3] 'explode' - Duplicate rows for each array item
Choose [1/2/3] (default: 1): 1

Enter output CSV path (default: telemetry.csv): telemetry.csv

Flattening data...
✓ Successfully flattened 12500 records into 34 columns.
✓ CSV saved cleanly to: telemetry.csv
```

---

## CLI Usage & Options

```bash
# Basic conversion (outputs data.csv)
flatjson data.json

# Specify custom destination
flatjson data.json -o ./exports/clean.csv

# Process JSONL streaming data with underscore delimiter
flatjson stream.jsonl -s "_" -a index

# Inspect schema without writing CSV
flatjson complex_dataset.json --schema
```

### Options Reference

| Flag | Long Option | Default | Description |
| :--- | :--- | :--- | :--- |
| `input` | *(positional)* | None | Path to input `.json` or `.jsonl` file |
| `-o` | `--output` | `<input>.csv` | Destination path for output CSV |
| `-s` | `--sep` | `.` | Key delimiter for nesting (`.` or `_`) |
| `-a` | `--array-mode` | `join` | Array handling strategy (`join`, `index`, `explode`) |
| | `--schema` | `False` | Display schema summary without generating CSV |
| `-f` | `--force` | `False` | Overwrite existing output file without confirmation |
| `-q` | `--quiet` | `False` | Suppress non-essential progress messages |
| `-i` | `--interactive` | `False` | Launch interactive configuration wizard |
| `-v` | `--version` | — | Display package version |

---

## Python API Reference

`flatjson-cli` can be integrated directly into your Python pipelines:

```python
from flatjson import flatten_record, json_file_to_csv, infer_schema

# 1. Flatten an in-memory dictionary
record = {
    "user": {"name": "Alice", "contact": {"email": "alice@example.com"}},
    "tags": ["admin", "dev"]
}
flat = flatten_record(record, separator=".", array_strategy="join")
print(flat)
# Output:
# {
#     "user.name": "Alice",
#     "user.contact.email": "alice@example.com",
#     "tags": "admin; dev"
# }

# 2. File-to-file streaming conversion
stats = json_file_to_csv(
    input_path="raw_dump.jsonl",
    output_path="normalized.csv",
    separator=".",
    array_strategy="join"
)
print(f"Processed {stats['records']} records into {stats['columns']} columns.")
```

---

## Developed & Maintained by Zephyrus Labs

Built and maintained with ❤️ by **[Zephyrus Labs](https://zephyrus-labs.tech/)** and Lead Developer **[Shubham Sharma](https://www.linkedin.com/in/shubham-sharma-28487819b/)**.

- 💼 **LinkedIn**: [linkedin.com/in/shubham-sharma-28487819b](https://www.linkedin.com/in/shubham-sharma-28487819b/)
- 💻 **GitHub**: [@uchiha-fire](https://github.com/uchiha-fire)
- 🌐 **Website**: [zephyrus-labs.tech](https://zephyrus-labs.tech/)
- ✉️ **Organization Email**: [zephyrus.labs@gmail.com](mailto:zephyrus.labs@gmail.com)
- 📬 **Developer Email**: [sharmashubham25962@gmail.com](mailto:sharmashubham25962@gmail.com)

If you find this tool helpful, please give it a ⭐️ on [GitHub](https://github.com/uchiha-fire/flatjson-cli)!

---

## Acknowledgements & Attributions

This tool is built strictly with the Python Standard Library (`json`, `csv`, `argparse`, `os`, `sys`). No external runtime dependencies are required.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<p align="right">
  <sub>Lead Developer: <a href="https://www.linkedin.com/in/shubham-sharma-28487819b/">Shubham Sharma</a> (<a href="https://github.com/uchiha-fire">@uchiha-fire</a>) &bull; <a href="mailto:sharmashubham25962@gmail.com">sharmashubham25962@gmail.com</a></sub>
</p>
