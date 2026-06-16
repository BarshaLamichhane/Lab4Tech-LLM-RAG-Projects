import os
from unittest import TestCase
from unittest.mock import patch

from backend.app.config import load_config


class LocalDevelopmentCorsTests(TestCase):
    def test_development_accepts_local_frontend_on_any_port(self):
        with patch.dict(
            os.environ,
            {
                "APP_ENV": "development",
                "JWT_SECRET": "development-secret",
            },
            clear=False,
        ):
            config = load_config()

        self.assertIsNotNone(config.cors_allow_origin_regex)

    def test_production_does_not_enable_local_origin_regex(self):
        with patch.dict(
            os.environ,
            {
                "APP_ENV": "production",
                "JWT_SECRET": "a-production-secret-that-is-over-32-characters",
                "CORS_ALLOWED_ORIGINS": "https://example.com",
                "ALLOWED_HOSTS": "example.com",
            },
            clear=False,
        ):
            config = load_config()

        self.assertIsNone(config.cors_allow_origin_regex)
