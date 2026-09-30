import json
import os
from pathlib import Path


def data_dir():
    return Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "BrokenSkyscraper"


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix+".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)
