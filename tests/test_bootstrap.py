import copy
import json
from pathlib import Path
import tempfile
import unittest

from atm_app.infrastructure.bootstrap import DEFAULT_SEED, load_seed, validate_seed
from atm_app.shared.errors import SeedDataError


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(DEFAULT_SEED.read_text(encoding="utf-8"))

    def test_default_seed_and_document_fixture_match(self):
        fixture = Path(__file__).resolve().parents[1] / "docs" / "development" / "data" / "accounts.seed.json"
        self.assertEqual(self.data, json.loads(fixture.read_text(encoding="utf-8")))
        self.assertEqual(len(load_seed()), 3)

    def test_TC_Q06_reject_bad_seed_as_a_whole(self):
        changes = [
            lambda d: d["accounts"].append(copy.deepcopy(d["accounts"][0])),
            lambda d: d["accounts"][0].update(balance=-1),
            lambda d: d["accounts"][0].update(failedCount=5, blocked=False),
            lambda d: d["accounts"][0].update(balance=True),
            lambda d: d["accounts"][0].update(failedCount=True),
            lambda d: d["accounts"][0].update(blocked=0),
            lambda d: d["accounts"][0].update(password="12a3"),
            lambda d: d.update(schemaVersion=True),
            lambda d: d.update(extra="unexpected"),
            lambda d: d["accounts"][0].pop("password"),
        ]
        for change in changes:
            data = copy.deepcopy(self.data)
            change(data)
            with self.subTest(change=change), self.assertRaises(SeedDataError):
                validate_seed(data)

    def test_missing_malformed_and_duplicate_json_fields(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "seed.json"
            with self.assertRaises(SeedDataError):
                load_seed(path)
            for source in ('{', '{"schemaVersion":1,"schemaVersion":1,"accounts":[]}', '[]'):
                path.write_text(source, encoding="utf-8")
                with self.subTest(source=source), self.assertRaises(SeedDataError):
                    load_seed(path)

    def test_error_messages_do_not_expose_seed_pin(self):
        self.data["accounts"][0]["password"] = "secret-value"
        with self.assertRaises(SeedDataError) as error:
            validate_seed(self.data)
        self.assertNotIn("secret-value", str(error.exception))

    def test_empty_collection_and_valid_blocked_seed(self):
        validate_seed({"schemaVersion": 1, "accounts": []})
        self.data["accounts"][0].update(failedCount=5, blocked=True)
        validate_seed(self.data)
