"""
Comprehensive test suite for flatjson-cli.
Follows TDD principles: tests all core logic, edge cases, schema inference,
streaming, CLI arguments, and interactive prompt modes.
"""
import csv
import json
import os
import tempfile
import pytest

from flatjson.core import (
    flatten_record,
    flatten_record_exploded,
    infer_schema,
    json_file_to_csv,
    iter_json_records,
)
from flatjson.cli import main


# ---------------------------------------------------------------------------
# Core Flattening Tests
# ---------------------------------------------------------------------------

def test_flatten_record_flat():
    data = {"id": 1, "name": "Alice"}
    flat = flatten_record(data)
    assert flat == {"id": 1, "name": "Alice"}


def test_flatten_record_nested():
    data = {
        "user": {
            "name": "Alice",
            "contact": {
                "email": "alice@example.com",
                "phone": "123-456"
            }
        }
    }
    flat = flatten_record(data, separator=".")
    assert flat == {
        "user.name": "Alice",
        "user.contact.email": "alice@example.com",
        "user.contact.phone": "123-456",
    }


def test_flatten_record_custom_separator():
    data = {"user": {"details": {"age": 30}}}
    flat = flatten_record(data, separator="__")
    assert flat == {"user__details__age": 30}


def test_flatten_record_array_join():
    data = {"roles": ["admin", "editor", "moderator"]}
    flat = flatten_record(data, array_strategy="join")
    assert flat == {"roles": "admin; editor; moderator"}


def test_flatten_record_array_index():
    data = {
        "tags": ["python", "cli"],
        "items": [{"name": "item1"}, {"name": "item2"}]
    }
    flat = flatten_record(data, array_strategy="index")
    assert flat == {
        "tags.0": "python",
        "tags.1": "cli",
        "items.0.name": "item1",
        "items.1.name": "item2",
    }


def test_flatten_record_empty_structures():
    data = {
        "empty_dict": {},
        "empty_list": [],
        "null_val": None,
        "valid": 42
    }
    flat = flatten_record(data)
    assert flat == {
        "empty_dict": "",
        "empty_list": "",
        "null_val": None,
        "valid": 42
    }


def test_flatten_record_exploded():
    data = {
        "order_id": 99,
        "customer": {"name": "Charlie"},
        "items": ["apple", "banana"]
    }
    rows = flatten_record_exploded(data, separator=".")
    assert len(rows) == 2
    assert rows[0] == {"order_id": 99, "customer.name": "Charlie", "items": "apple"}
    assert rows[1] == {"order_id": 99, "customer.name": "Charlie", "items": "banana"}


# ---------------------------------------------------------------------------
# Schema Inference Tests
# ---------------------------------------------------------------------------

def test_infer_schema():
    records = [
        {
            "id": "u1",
            "age": 28,
            "balance": 150.50,
            "active": True,
            "profile": {"city": "Berlin"},
            "tags": ["fast", "reliable"]
        },
        {
            "id": "u2",
            "age": 34,
            "balance": 0.0,
            "active": False,
            "profile": {"city": "Munich"},
            "tags": ["enterprise"]
        }
    ]
    schema = infer_schema(records, separator=".")
    field_names = [f["name"] for f in schema]
    assert "id" in field_names
    assert "age" in field_names
    assert "balance" in field_names
    assert "active" in field_names
    assert "profile.city" in field_names
    assert "tags" in field_names

    age_field = next(f for f in schema if f["name"] == "age")
    assert age_field["type"] == "Integer"
    assert age_field["sample"] in ("28", 28)

    balance_field = next(f for f in schema if f["name"] == "balance")
    assert balance_field["type"] == "Float"


# ---------------------------------------------------------------------------
# File Conversion & Streaming Tests
# ---------------------------------------------------------------------------

def test_json_file_array_to_csv(tmp_path):
    json_path = tmp_path / "data.json"
    csv_path = tmp_path / "output.csv"

    dataset = [
        {"user": {"name": "Alice", "city": "NYC"}},
        {"user": {"name": "Bob", "city": "SF"}}
    ]
    json_path.write_text(json.dumps(dataset), encoding="utf-8")

    stats = json_file_to_csv(str(json_path), str(csv_path), separator=".")
    assert stats["records"] == 2
    assert stats["columns"] == 2
    assert os.path.exists(csv_path)

    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 2
        assert rows[0]["user.name"] == "Alice"
        assert rows[1]["user.city"] == "SF"


def test_single_json_object_to_csv(tmp_path):
    json_path = tmp_path / "single.json"
    csv_path = tmp_path / "single.csv"

    data = {"system": {"cpu": 95.2, "status": "alert"}}
    json_path.write_text(json.dumps(data), encoding="utf-8")

    stats = json_file_to_csv(str(json_path), str(csv_path))
    assert stats["records"] == 1
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert rows[0]["system.cpu"] == "95.2"


def test_jsonl_streaming_to_csv(tmp_path):
    jsonl_path = tmp_path / "stream.jsonl"
    csv_path = tmp_path / "stream.csv"

    lines = [
        json.dumps({"id": 1, "meta": {"label": "first"}}),
        json.dumps({"id": 2, "meta": {"label": "second"}}),
        json.dumps({"id": 3, "meta": {"label": "third"}}),
    ]
    jsonl_path.write_text("\n".join(lines), encoding="utf-8")

    stats = json_file_to_csv(str(jsonl_path), str(csv_path), separator="_")
    assert stats["records"] == 3
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 3
        assert rows[0]["meta_label"] == "first"


def test_csv_escaping_special_characters(tmp_path):
    json_path = tmp_path / "special.json"
    csv_path = tmp_path / "special.csv"

    data = [{"text": 'He said, "Hello, World!"\nNew line here.'}]
    json_path.write_text(json.dumps(data), encoding="utf-8")

    json_file_to_csv(str(json_path), str(csv_path))
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert rows[0]["text"] == 'He said, "Hello, World!"\nNew line here.'


# ---------------------------------------------------------------------------
# CLI Argument and Interactive Tests
# ---------------------------------------------------------------------------

def test_cli_version(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "flatjson-cli" in captured.out or "0.1.0" in captured.out


def test_cli_schema_flag(tmp_path, capsys):
    json_path = tmp_path / "test.json"
    data = [{"user": {"name": "Alice", "age": 25}}]
    json_path.write_text(json.dumps(data), encoding="utf-8")

    exit_code = main([str(json_path), "--schema"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "user.name" in captured.out
    assert "user.age" in captured.out
    assert "Schema Summary" in captured.out


def test_cli_convert_file(tmp_path, capsys):
    json_path = tmp_path / "data.json"
    csv_path = tmp_path / "data.csv"
    data = [{"title": "Test", "nested": {"val": 123}}]
    json_path.write_text(json.dumps(data), encoding="utf-8")

    exit_code = main([str(json_path), "-o", str(csv_path), "-f"])
    assert exit_code == 0
    assert os.path.exists(csv_path)
    captured = capsys.readouterr()
    assert "Successfully flattened" in captured.out or "Processed" in captured.out


def test_cli_interactive_wizard(tmp_path, monkeypatch, capsys):
    json_path = tmp_path / "interactive.json"
    csv_path = tmp_path / "interactive.csv"
    data = [{"hero": {"name": "Batman", "vehicle": "Batmobile"}}]
    json_path.write_text(json.dumps(data), encoding="utf-8")

    # Simulate user inputs for interactive wizard:
    # 1. file path
    # 2. action: 1 (Flatten to CSV)
    # 3. separator choice: 1 (.)
    # 4. array strategy choice: 1 (join)
    # 5. output path
    # 6. overwrite confirm (if prompted)
    inputs = iter([
        str(json_path),
        "1",               # Action: Flatten to CSV
        "1",               # Separator: '.'
        "1",               # Array: join
        str(csv_path),     # Output file
        "y"                # Proceed
    ])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    exit_code = main(["--interactive"])
    assert exit_code == 0
    assert os.path.exists(csv_path)
