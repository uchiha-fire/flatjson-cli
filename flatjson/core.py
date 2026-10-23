"""
Core recursive flattening and schema extraction engine for flatjson-cli.
Pure standard library, zero external dependencies.
"""
import csv
import json
import os
from typing import Any, Dict, Generator, Iterable, List, Optional, Tuple


def flatten_record(
    nested_dict: Dict[str, Any],
    parent_key: str = "",
    separator: str = ".",
    array_strategy: str = "join",
) -> Dict[str, Any]:
    """
    Recursively flattens a nested dictionary into a single-level dictionary.

    Args:
        nested_dict: Dictionary to flatten.
        parent_key: Prefix for nested keys.
        separator: Delimiter for nested key paths.
        array_strategy: Strategy for handling lists: 'join', 'index'.

    Returns:
        Flattened single-level dictionary.
    """
    items: List[Tuple[str, Any]] = []

    for key, value in nested_dict.items():
        new_key = f"{parent_key}{separator}{key}" if parent_key else str(key)

        if isinstance(value, dict):
            if not value:
                items.append((new_key, ""))
            else:
                items.extend(
                    flatten_record(value, new_key, separator, array_strategy).items()
                )
        elif isinstance(value, list):
            if not value:
                items.append((new_key, ""))
            elif array_strategy == "join":
                # Join simple elements with semicolon
                joined_str = "; ".join(str(x) for x in value)
                items.append((new_key, joined_str))
            elif array_strategy == "index":
                for idx, item in enumerate(value):
                    indexed_key = f"{new_key}{separator}{idx}"
                    if isinstance(item, dict):
                        items.extend(
                            flatten_record(item, indexed_key, separator, array_strategy).items()
                        )
                    else:
                        items.append((indexed_key, item))
            else:
                items.append((new_key, value))
        else:
            items.append((new_key, value))

    return dict(items)


def flatten_record_exploded(
    nested_dict: Dict[str, Any],
    parent_key: str = "",
    separator: str = ".",
) -> List[Dict[str, Any]]:
    """
    Flattens a record, exploding array fields into multiple individual rows.
    """
    # Separate scalar/dict items from arrays
    scalars: Dict[str, Any] = {}
    arrays: Dict[str, List[Any]] = {}

    for key, value in nested_dict.items():
        new_key = f"{parent_key}{separator}{key}" if parent_key else str(key)
        if isinstance(value, dict):
            sub_rows = flatten_record_exploded(value, new_key, separator)
            if sub_rows:
                # Merge sub-dict fields
                scalars.update(sub_rows[0])
            else:
                scalars[new_key] = ""
        elif isinstance(value, list):
            if value:
                arrays[new_key] = value
            else:
                scalars[new_key] = ""
        else:
            scalars[new_key] = value

    if not arrays:
        return [scalars]

    # Explode the first array found (or cartesian if multiple)
    rows = [scalars]
    for arr_key, arr_val in arrays.items():
        new_rows = []
        for r in rows:
            for item in arr_val:
                expanded_r = dict(r)
                if isinstance(item, dict):
                    flat_sub = flatten_record(item, arr_key, separator)
                    expanded_r.update(flat_sub)
                else:
                    expanded_r[arr_key] = item
                new_rows.append(expanded_r)
        rows = new_rows

    return rows


def iter_json_records(file_path: str) -> Generator[Dict[str, Any], None, None]:
    """
    Yields dictionary records from a .json or .jsonl file in a memory-efficient manner.
    """
    is_jsonl = file_path.lower().endswith((".jsonl", ".ndjson"))

    if is_jsonl:
        with open(file_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, start=1):
                clean_line = line.strip()
                if not clean_line:
                    continue
                try:
                    record = json.loads(clean_line)
                    if isinstance(record, dict):
                        yield record
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON on line {line_num}: {e}") from e
    else:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        yield item
            elif isinstance(data, dict):
                yield data
            else:
                raise ValueError("JSON root must be an object or an array of objects.")


def infer_schema(
    records: Iterable[Dict[str, Any]],
    separator: str = ".",
    sample_limit: int = 500,
) -> List[Dict[str, Any]]:
    """
    Inspects records and infers column names, data types, and sample values.
    """
    field_types: Dict[str, str] = {}
    field_samples: Dict[str, Any] = {}

    for idx, rec in enumerate(records):
        if idx >= sample_limit:
            break
        flat = flatten_record(rec, separator=separator, array_strategy="join")
        for key, val in flat.items():
            if key not in field_samples and val is not None and val != "":
                field_samples[key] = val

            current_type = field_types.get(key)
            new_type = _infer_type(val)
            if current_type is None:
                field_types[key] = new_type
            elif current_type != new_type and new_type != "Null":
                if current_type == "Null":
                    field_types[key] = new_type
                elif {current_type, new_type} == {"Integer", "Float"}:
                    field_types[key] = "Float"
                else:
                    field_types[key] = "String"

    schema = []
    for key in sorted(field_types.keys()):
        sample = field_samples.get(key, "")
        schema.append({
            "name": key,
            "type": field_types.get(key, "Unknown"),
            "sample": sample
        })
    return schema


def _infer_type(value: Any) -> str:
    if value is None:
        return "Null"
    if isinstance(value, bool):
        return "Boolean"
    if isinstance(value, int):
        return "Integer"
    if isinstance(value, float):
        return "Float"
    if isinstance(value, list):
        return "Array"
    if isinstance(value, dict):
        return "Object"
    return "String"


def json_file_to_csv(
    input_path: str,
    output_path: str,
    separator: str = ".",
    array_strategy: str = "join",
) -> Dict[str, Any]:
    """
    Flattens a JSON/JSONL file into a tabular CSV.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Pass 1: discover all fieldnames and prepare records
    fieldnames_set = set()
    ordered_fieldnames: List[str] = []
    records_cache: List[Dict[str, Any]] = []

    for raw_record in iter_json_records(input_path):
        if array_strategy == "explode":
            flattened_rows = flatten_record_exploded(raw_record, separator=separator)
        else:
            flattened_rows = [flatten_record(raw_record, separator=separator, array_strategy=array_strategy)]

        for flat_row in flattened_rows:
            records_cache.append(flat_row)
            for k in flat_row.keys():
                if k not in fieldnames_set:
                    fieldnames_set.add(k)
                    ordered_fieldnames.append(k)

    # Pass 2: write CSV
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=ordered_fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in records_cache:
            writer.writerow(row)

    return {
        "records": len(records_cache),
        "columns": len(ordered_fieldnames),
        "output_path": output_path,
    }
