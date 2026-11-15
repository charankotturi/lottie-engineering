import json, pathlib, subprocess, sys, tempfile, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"skills"/"lottie"/"scripts"/"validate_lottie.py"
VALID=ROOT/"skills"/"lottie"/"assets"/"minimal-valid.json"

class ValidatorTests(unittest.TestCase):
    def run_validator(self, data):
        with tempfile.TemporaryDirectory() as d:
            p=pathlib.Path(d)/"test.json"; p.write_text(json.dumps(data))
            return subprocess.run([sys.executable,str(SCRIPT),str(p)],capture_output=True,text=True)
    def test_valid_fixture_passes(self):
        r=subprocess.run([sys.executable,str(SCRIPT),str(VALID)],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
    def test_missing_width_fails(self):
        d=json.loads(VALID.read_text()); del d["w"]
        r=self.run_validator(d)
        self.assertNotEqual(r.returncode,0)
        self.assertIn("MISSING_ROOT_FIELD",r.stdout)
    def test_invalid_frame_range_fails(self):
        d=json.loads(VALID.read_text()); d["op"]=d["ip"]
        r=self.run_validator(d)
        self.assertNotEqual(r.returncode,0)
        self.assertIn("INVALID_FRAME_RANGE",r.stdout)
    def test_non_finite_number_fails(self):
        d=json.loads(VALID.read_text()); d["layers"][0]["ks"]["o"]["k"]=float("nan")
        r=self.run_validator(d)
        self.assertNotEqual(r.returncode,0)
        self.assertIn("NON_FINITE_NUMBER",r.stdout)
    def test_missing_asset_reference_fails(self):
        d=json.loads(VALID.read_text()); d["layers"][0]["refId"]="missing"
        r=self.run_validator(d)
        self.assertNotEqual(r.returncode,0)
        self.assertIn("UNRESOLVED_ASSET_REF",r.stdout)

if __name__=="__main__": unittest.main()
