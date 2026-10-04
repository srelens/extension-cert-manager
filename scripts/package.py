"""Package exact, version-checked manifest bytes; signing is a required release step."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--version", required=True)
args = parser.parse_args()
raw = (ROOT / "manifest.json").read_bytes()
if json.loads(raw)["version"] != args.version:
    raise SystemExit("Requested release version does not match manifest.json")
out = ROOT / "dist"
out.mkdir(exist_ok=True)
(out / "manifest.json").write_bytes(raw)
(out / "SHA256SUMS").write_text(hashlib.sha256(raw).hexdigest() + "  manifest.json\n")

