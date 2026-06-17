"""
Agent 1: Log Ingestion and Normalization Agent

Responsibilities:
- Accept txt, csv, json, jsonl files.
- Normalize raw logs/events into a compact incident context.
- Produce signal counts, error samples, time range, and suspected services.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd


@dataclass
class ParsedLogContext:
    file_name: str
    file_type: str
    total_records: int
    time_range: Dict[str, str]
    severity_counts: Dict[str, int]
    top_error_terms: List[str]
    suspected_services: List[str]
    samples: List[str]
    raw_preview: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_name": self.file_name,
            "file_type": self.file_type,
            "total_records": self.total_records,
            "time_range": self.time_range,
            "severity_counts": self.severity_counts,
            "top_error_terms": self.top_error_terms,
            "suspected_services": self.suspected_services,
            "samples": self.samples,
            "raw_preview": self.raw_preview,
        }


class LogIngestionAgent:
    """Parses and summarizes uploaded observability files."""

    SEVERITY_TERMS = ["CRITICAL", "FATAL", "ERROR", "WARN", "WARNING", "INFO", "DEBUG"]
    ERROR_PATTERNS = [
        r"timeout",
        r"connection refused",
        r"connection reset",
        r"outofmemory|oom",
        r"disk full|no space",
        r"5xx|500|502|503|504",
        r"latency",
        r"exception",
        r"failed|failure",
        r"unauthorized|403|401",
        r"rate limit|throttle",
        r"dbconnectiontimeout|database.*timeout",
        r"pod restart|crashloopbackoff",
    ]

    def run(self, file_path: str) -> Dict[str, Any]:
        path = Path(file_path)
        suffix = path.suffix.lower().replace(".", "") or "txt"

        if suffix == "csv":
            records, preview = self._read_csv(path)
        elif suffix in {"json", "jsonl"}:
            records, preview = self._read_json(path, suffix)
        else:
            records, preview = self._read_text(path)

        flat_text = "\n".join(self._record_to_text(r) for r in records)
        severity_counts = self._count_severity(flat_text)
        top_error_terms = self._extract_error_terms(flat_text)
        suspected_services = self._extract_services(flat_text)
        time_range = self._extract_time_range(records, flat_text)
        samples = self._extract_samples(records, flat_text)

        context = ParsedLogContext(
            file_name=path.name,
            file_type=suffix,
            total_records=len(records),
            time_range=time_range,
            severity_counts=severity_counts,
            top_error_terms=top_error_terms,
            suspected_services=suspected_services,
            samples=samples,
            raw_preview=preview[:4000],
        )
        return context.to_dict()

    def _read_csv(self, path: Path):
        df = pd.read_csv(path)
        df = df.fillna("")
        records = df.to_dict(orient="records")
        preview = df.head(30).to_csv(index=False)
        return records, preview

    def _read_json(self, path: Path, suffix: str):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if suffix == "jsonl":
            records = [json.loads(line) for line in text.splitlines() if line.strip()]
        else:
            obj = json.loads(text)
            if isinstance(obj, list):
                records = obj
            elif isinstance(obj, dict):
                # If dict contains a list-like payload, use it; otherwise treat dict as one record.
                list_values = [v for v in obj.values() if isinstance(v, list)]
                records = list_values[0] if list_values else [obj]
            else:
                records = [{"value": obj}]
        preview = json.dumps(records[:20], indent=2)[:4000]
        return records, preview

    def _read_text(self, path: Path):
        text = path.read_text(encoding="utf-8", errors="ignore")
        lines = [line for line in text.splitlines() if line.strip()]
        records = [{"message": line} for line in lines]
        preview = "\n".join(lines[:80])
        return records, preview

    def _record_to_text(self, record: Any) -> str:
        if isinstance(record, dict):
            return " ".join(f"{k}={v}" for k, v in record.items())
        return str(record)

    def _count_severity(self, text: str) -> Dict[str, int]:
        counts = {}
        upper = text.upper()
        for term in self.SEVERITY_TERMS:
            counts[term] = len(re.findall(rf"\b{re.escape(term)}\b", upper))
        return {k: v for k, v in counts.items() if v > 0}

    def _extract_error_terms(self, text: str) -> List[str]:
        found = []
        lower = text.lower()
        for pattern in self.ERROR_PATTERNS:
            if re.search(pattern, lower):
                found.append(pattern.replace("|", "/"))
        return found[:12]

    def _extract_services(self, text: str) -> List[str]:
        patterns = [
            r"service[=: ]([a-zA-Z0-9_.-]+)",
            r"app[=: ]([a-zA-Z0-9_.-]+)",
            r"pod[=: ]([a-zA-Z0-9_.-]+)",
            r"container[=: ]([a-zA-Z0-9_.-]+)",
        ]
        candidates = []
        for pattern in patterns:
            candidates.extend(re.findall(pattern, text, flags=re.IGNORECASE))
        seen = []
        for item in candidates:
            if item not in seen:
                seen.append(item)
        return seen[:10]

    def _extract_time_range(self, records: List[Any], text: str) -> Dict[str, str]:
        timestamps = []
        for rec in records:
            if isinstance(rec, dict):
                for key in ["timestamp", "time", "datetime", "date", "@timestamp"]:
                    if key in rec and str(rec[key]).strip():
                        timestamps.append(str(rec[key]))
        if not timestamps:
            # fallback regex for ISO-like timestamps
            timestamps = re.findall(r"\d{4}-\d{2}-\d{2}[T ][0-9:.+-Z]+", text)
        return {
            "start": min(timestamps) if timestamps else "unknown",
            "end": max(timestamps) if timestamps else "unknown",
        }

    def _extract_samples(self, records: List[Any], text: str) -> List[str]:
        lines = [self._record_to_text(r) for r in records]
        interesting = []
        for line in lines:
            if re.search(r"error|critical|fatal|warn|timeout|failed|exception|5xx|500|oom", line, flags=re.I):
                interesting.append(line[:700])
        if not interesting:
            interesting = lines[:10]
        return interesting[:20]
