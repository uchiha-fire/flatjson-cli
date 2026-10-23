"""
flatjson-cli
Deep JSON & JSONL to Tabular CSV Flattener
"""

__version__ = "0.1.0"
__author__ = "Zephyrus Labs"
__maintainer__ = "Shubham Sharma"
__email__ = "zephyrus.labs@gmail.com"
__developer_email__ = "sharmashubham25962@gmail.com"

from .core import (
    flatten_record,
    flatten_record_exploded,
    json_file_to_csv,
    infer_schema,
    iter_json_records,
)

__all__ = [
    "flatten_record",
    "flatten_record_exploded",
    "json_file_to_csv",
    "infer_schema",
    "iter_json_records",
    "__version__",
    "__author__",
    "__maintainer__",
    "__email__",
    "__developer_email__",
]
