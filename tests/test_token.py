import unittest
from types import SimpleNamespace
from unittest.mock import patch

from jam_mapper.core.token import get_runtime_authorization_token


class RuntimeTokenTests(unittest.TestCase):
    @patch("jam_mapper.core.token.get_cached_authorization_token", return_value="")
    @patch("jam_mapper.core.token.refresh_authorization_token")
    @patch("jam_mapper.core.token.get_settings")
    def test_falls_back_to_configured_jwt_when_refresh_fails(self, settings_mock, refresh_mock, _cached_mock):
        settings_mock.return_value = SimpleNamespace(token_refresh_enabled=True, jwt="configured-jwt")
        refresh_mock.side_effect = RuntimeError("boom")

        self.assertEqual(get_runtime_authorization_token(force=True), "configured-jwt")


if __name__ == "__main__":
    unittest.main()
