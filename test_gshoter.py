from __future__ import annotations

import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import requests

import gshoter
from gshoter import GoogleMapScreenShooter


class GoogleMapScreenShooterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.shooter = GoogleMapScreenShooter("test-api-key")

    def test_init_rejects_empty_api_key(self) -> None:
        with self.assertRaisesRegex(ValueError, "API key is required"):
            GoogleMapScreenShooter("   ")

    def test_init_strips_api_key(self) -> None:
        self.assertEqual(GoogleMapScreenShooter("  abc123  ").api_key, "abc123")

    def test_build_url_simple(self) -> None:
        url = self.shooter.build_url(
            35.6892,
            51.3890,
            zoom=12,
            size="400x400",
            maptype="satellite",
        )

        self.assertTrue(url.startswith(gshoter.STATIC_MAP_URL + "?"))
        self.assertIn("center=35.6892%2C51.389", url)
        self.assertIn("zoom=12", url)
        self.assertIn("size=400x400", url)
        self.assertIn("maptype=satellite", url)
        self.assertIn("scale=2", url)
        self.assertIn("key=test-api-key", url)
        self.assertNotIn("markers=", url)

    def test_build_url_with_marker_label(self) -> None:
        url = self.shooter.build_url(
            35.0,
            51.0,
            marker=True,
            marker_label="hello",
        )
        self.assertIn("markers=color%3Ared%7Clabel%3AH%7C35.0%2C51.0", url)

    def test_build_url_with_default_marker_label(self) -> None:
        url = self.shooter.build_url(1.0, 2.0, marker=True)
        self.assertIn("label%3AA%7C1.0%2C2.0", url)

    def test_take_screenshot_writes_image(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "nested" / "map.png"
            fake_response = MagicMock()
            fake_response.headers = {"Content-Type": "image/png"}
            fake_response.content = b"fake-png-bytes"
            fake_response.raise_for_status = MagicMock()

            with patch("gshoter.requests.get", return_value=fake_response) as mock_get:
                path = self.shooter.take_screenshot(
                    35.0,
                    51.0,
                    output=output,
                    marker=True,
                    marker_label="B",
                )

            mock_get.assert_called_once()
            args, kwargs = mock_get.call_args
            self.assertTrue(args[0].startswith(gshoter.STATIC_MAP_URL))
            self.assertIn("markers=", args[0])
            self.assertEqual(kwargs["timeout"], 30)
            self.assertEqual(path, output.resolve())
            self.assertEqual(path.read_bytes(), b"fake-png-bytes")

    def test_take_screenshot_rejects_non_image(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fake_response = MagicMock()
            fake_response.headers = {"Content-Type": "application/json"}
            fake_response.text = '{"error":"bad key"}'
            fake_response.raise_for_status = MagicMock()

            with patch("gshoter.requests.get", return_value=fake_response):
                with self.assertRaisesRegex(RuntimeError, "Could not download map image"):
                    self.shooter.take_screenshot(35.0, 51.0, output=Path(tmp) / "bad.png")

    def test_take_screenshot_raises_http_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fake_response = MagicMock()
            fake_response.raise_for_status.side_effect = requests.HTTPError("403 Forbidden")

            with patch("gshoter.requests.get", return_value=fake_response):
                with self.assertRaises(requests.HTTPError):
                    self.shooter.take_screenshot(35.0, 51.0, output=Path(tmp) / "fail.png")


class PromptHelperTests(unittest.TestCase):
    def test_prompt_text_uses_default(self) -> None:
        with patch("builtins.input", return_value="   "):
            self.assertEqual(gshoter.prompt_text("Name", "default.png"), "default.png")

    def test_prompt_text_requires_value(self) -> None:
        answers = iter(["", "final"])
        with patch("builtins.input", side_effect=lambda _: next(answers)):
            with patch("sys.stdout", new_callable=io.StringIO) as stdout:
                self.assertEqual(gshoter.prompt_text("Name"), "final")
                self.assertIn("Please enter a value.", stdout.getvalue())

    def test_prompt_float_retries_invalid(self) -> None:
        answers = iter(["nope", "35.5"])
        with patch("builtins.input", side_effect=lambda _: next(answers)):
            self.assertEqual(gshoter.prompt_float("Latitude"), 35.5)

    def test_prompt_int_enforces_range(self) -> None:
        answers = iter(["99", "abc", "10"])
        with patch("builtins.input", side_effect=lambda _: next(answers)):
            self.assertEqual(gshoter.prompt_int("Zoom", 15, 0, 21), 10)

    def test_prompt_choice_accepts_valid(self) -> None:
        with patch("builtins.input", return_value="Satellite"):
            self.assertEqual(
                gshoter.prompt_choice("Map", ["roadmap", "satellite"], "roadmap"),
                "satellite",
            )

    def test_prompt_yes_no_defaults_and_answers(self) -> None:
        with patch("builtins.input", return_value=""):
            self.assertTrue(gshoter.prompt_yes_no("Continue?", default=True))

        with patch("builtins.input", return_value="n"):
            self.assertFalse(gshoter.prompt_yes_no("Continue?"))


class ApiKeyAndMenuTests(unittest.TestCase):
    def test_resolve_api_key_from_env(self) -> None:
        with patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": " env-key "}):
            self.assertEqual(gshoter.resolve_api_key(), "env-key")

    def test_resolve_api_key_prompts_when_missing(self) -> None:
        env = os.environ.copy()
        env.pop("GOOGLE_MAPS_API_KEY", None)
        with patch.dict(os.environ, env, clear=True):
            with patch("gshoter.prompt_text", return_value="typed-key"):
                self.assertEqual(gshoter.resolve_api_key(), "typed-key")

    def test_collect_common_options(self) -> None:
        with patch("gshoter.prompt_float", side_effect=[35.1, 51.2]):
            with patch("gshoter.prompt_int", return_value=14):
                with patch("gshoter.prompt_text", side_effect=["800x600", "out.png"]):
                    with patch("gshoter.prompt_choice", return_value="terrain"):
                        options = gshoter.collect_common_options()

        self.assertEqual(
            options,
            {
                "latitude": 35.1,
                "longitude": 51.2,
                "zoom": 14,
                "size": "800x600",
                "maptype": "terrain",
                "output": "out.png",
            },
        )

    def test_main_exits_from_menu(self) -> None:
        with patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "menu-key"}):
            with patch("builtins.input", return_value="4"):
                self.assertEqual(gshoter.main(), 0)

    def test_main_runs_simple_screenshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = str(Path(tmp) / "simple.png")
            inputs = iter(["1", "", "4"])
            fake_response = MagicMock()
            fake_response.headers = {"Content-Type": "image/png"}
            fake_response.content = b"png"
            fake_response.raise_for_status = MagicMock()

            with patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "menu-key"}):
                with patch(
                    "gshoter.collect_common_options",
                    return_value={
                        "latitude": 1.0,
                        "longitude": 2.0,
                        "zoom": 10,
                        "size": "400x400",
                        "maptype": "roadmap",
                        "output": output,
                    },
                ):
                    with patch("builtins.input", side_effect=lambda _: next(inputs)):
                        with patch("gshoter.requests.get", return_value=fake_response):
                            self.assertEqual(gshoter.main(), 0)

            self.assertEqual(Path(output).read_bytes(), b"png")


if __name__ == "__main__":
    unittest.main()
