from __future__ import annotations

import csv
import io

from .schemas import CompanyRecord

REQUIRED_COLUMNS = {"id", "name"}
OPTIONAL_COLUMNS = {"website", "country"}


def parse_company_csv(content: bytes) -> list[CompanyRecord]:
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))

    if not reader.fieldnames:
        raise ValueError("CSV appears to be empty or missing header row")

    headers = {h.strip() for h in reader.fieldnames if h}
    missing = REQUIRED_COLUMNS - headers
    if missing:
        raise ValueError(f"CSV missing required columns: {', '.join(sorted(missing))}")

    records: list[CompanyRecord] = []
    for idx, row in enumerate(reader, start=2):
        rec_id = (row.get("id") or "").strip()
        name = (row.get("name") or "").strip()
        if not rec_id or not name:
            raise ValueError(f"Invalid row {idx}: id and name are required")

        base = {
            "id": rec_id,
            "name": name,
            "website": (row.get("website") or "").strip() or None,
            "country": (row.get("country") or "").strip() or None,
        }

        # Keep additional columns in metadata
        metadata = {}
        for k, v in row.items():
            if k in REQUIRED_COLUMNS or k in OPTIONAL_COLUMNS:
                continue
            metadata[k] = v
        if metadata:
            base["metadata"] = metadata

        records.append(CompanyRecord(**base))

    return records
