import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

class ReleaseTests(unittest.TestCase):
    def run_package(self, version):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "scripts").mkdir()
            shutil.copy(ROOT / "scripts/package.py", root / "scripts/package.py")
            for name in ["README.md", "LICENSE", "icons/icon.svg"]:
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / name, target)
            raw = (ROOT / "manifest.json").read_bytes()
            (root / "manifest.json").write_bytes(raw)
            result = subprocess.run(["python3", str(root / "scripts/package.py"), "--version", version],
                                    cwd=root, text=True, capture_output=True)
            if result.returncode == 0:
                self.assertEqual((root / "dist/manifest.json").read_bytes(), raw)
                self.assertEqual((root / "dist/SHA256SUMS").read_text(), hashlib.sha256(raw).hexdigest()+"  manifest.json\n")
            else:
                self.assertFalse((root / "dist").exists())
            return result

    def test_packages_the_exact_release_bytes(self):
        self.assertEqual(self.run_package(json.loads((ROOT / "manifest.json").read_text())["version"]).returncode, 0)

    def test_version_mismatch_produces_no_release(self):
        result = self.run_package("9999.0.0")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("version", result.stderr.lower())

if __name__ == "__main__":
    unittest.main()

