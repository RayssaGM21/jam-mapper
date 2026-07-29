import unittest
import sys
import types

sys.modules.setdefault("streamlit", types.SimpleNamespace())

from jam_mapper.web.auth import hash_password, verify_password


class PasswordHashTests(unittest.TestCase):
    def test_hash_round_trip(self):
        encoded = hash_password("senha longa de teste", salt=b"0123456789abcdef")
        self.assertTrue(verify_password("senha longa de teste", encoded))
        self.assertFalse(verify_password("senha errada", encoded))

    def test_invalid_hash_is_rejected(self):
        self.assertFalse(verify_password("senha", "invalido"))


if __name__ == "__main__":
    unittest.main()
