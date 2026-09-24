from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class Glossary:
    entries: dict[str, str] = field(default_factory=dict)

    @classmethod
    def load(cls, path: str | Path) -> "Glossary":
        file_path = Path(path)
        if not file_path.exists():
            return cls()
        raw = json.loads(file_path.read_text(encoding="utf-8"))
        entries: dict[str, str] = {}
        for item in raw.get("entries", []):
            term = str(item["term"]).strip()
            replacement = str(item.get("translation", term)).strip()
            if term:
                entries[term] = replacement
        return cls(entries=entries)

    def as_mapping(self) -> dict[str, str]:
        return dict(self.entries)
