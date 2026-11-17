"""site/static/panchanga.js against dates whose pañcāṅga is well known (Bengaluru, at sunrise)."""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

JS = Path(__file__).resolve().parent.parent / "site" / "static" / "panchanga.js"
CASES = {   # date: (māsa, pakṣa, tithi, saṃvatsara)
    "2026-11-17": ("Kārtika", "Śukla", "Aṣṭamī", "Parābhava"),
    "2026-03-26": ("Caitra", "Śukla", "Aṣṭamī", "Parābhava"),      # Rāma Navamī day: Navamī begins during the day
    "2026-02-15": ("Māgha", "Kṛṣṇa", "Trayodaśī", "Viśvāvasu"),   # Mahāśivarātri: Caturdaśī sets in during the night
    "2026-08-28": ("Śrāvaṇa", "Śukla", "Pūrṇimā", "Parābhava"),    # Rakṣā Bandhan
    "2026-11-08": ("Āśvayuja", "Kṛṣṇa", "Caturdaśī", "Parābhava"),  # Dīpāvalī
}


@unittest.skipUnless(shutil.which("node"), "node not installed")
class Panchanga(unittest.TestCase):
    def test_known_days(self):
        js = ("global.window={};require(%r);const o={};for(const d of %s){const p=window.VRPanchanga(new Date(d+'T12:00:00+05:30'),12.9716,77.5946);"
              "o[d]=[p.masa,p.paksha,p.tithi,p.samvatsara,p.sunrise<p.sunset,p.tithiEnd>p.sunrise];}console.log(JSON.stringify(o))") % (str(JS), json.dumps(list(CASES)))
        got = json.loads(subprocess.run(["node", "-e", js], capture_output=True, text=True, check=True).stdout)
        for d, want in CASES.items():
            self.assertEqual(tuple(got[d][:4]), want, d)
            self.assertTrue(got[d][4] and got[d][5], d)


if __name__ == "__main__":
    unittest.main()
