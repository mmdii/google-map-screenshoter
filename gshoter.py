#!/usr/bin/env python3
"""Interactive Google Maps Static API screenshot tool."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from urllib.parse import urlencode

import requests

STATIC_MAP_URL = "https://maps.googleapis.com/maps/api/staticmap"
DEFAULT_SIZE = "640x640"
DEFAULT_ZOOM = 15
DEFAULT_OUTPUT = "map_screenshot.png"


class GoogleMapScreenShooter:
    def __init__(self, api_key: str) -> None:
        if not api_key.strip():
            raise ValueError("A Google Maps API key is required.")
        self.api_key = api_key.strip()

    def build_url(
        self,
        latitude: float,
        longitude: float,
        *,
        zoom: int = DEFAULT_ZOOM,
        size: str = DEFAULT_SIZE,
        maptype: str = "roadmap",
        marker: bool = False,
        marker_label: str | None = None,
    ) -> str:
        params: list[tuple[str, str]] = [
            ("center", f"{latitude},{longitude}"),
            ("zoom", str(zoom)),
            ("size", size),
            ("maptype", maptype),
            ("scale", "2"),
            ("key", self.api_key),
        ]

        if marker:
            label = (marker_label or "A")[:1].upper()
            params.append(
                ("markers", f"color:red|label:{label}|{latitude},{longitude}")
            )

        return f"{STATIC_MAP_URL}?{urlencode(params)}"

    def take_screenshot(
        self,
        latitude: float,
        longitude: float,
        *,
        zoom: int = DEFAULT_ZOOM,
        size: str = DEFAULT_SIZE,
        maptype: str = "roadmap",
        marker: bool = False,
        marker_label: str | None = None,
        output: str | Path = DEFAULT_OUTPUT,
    ) -> Path:
        url = self.build_url(
            latitude,
            longitude,
            zoom=zoom,
            size=size,
            maptype=maptype,
            marker=marker,
            marker_label=marker_label,
        )
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "")
        if "image" not in content_type:
            message = response.text.strip() or "Google Maps returned a non-image response."
            raise RuntimeError(
                "Could not download map image. Check your API key, billing, "
                f"and Static Maps API access.\nDetails: {message[:300]}"
            )

        output_path = Path(output).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(response.content)
        return output_path


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def prompt_text(label: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default is not None else ""
    while True:
        value = input(f"{label}{suffix}: ").strip()
        if value:
            return value
        if default is not None:
            return default
        print("Please enter a value.")


def prompt_float(label: str, default: float | None = None) -> float:
    while True:
        raw = prompt_text(label, None if default is None else str(default))
        try:
            return float(raw)
        except ValueError:
            print("Please enter a valid number.")


def prompt_int(label: str, default: int, minimum: int, maximum: int) -> int:
    while True:
        raw = prompt_text(label, str(default))
        try:
            value = int(raw)
        except ValueError:
            print("Please enter a whole number.")
            continue
        if minimum <= value <= maximum:
            return value
        print(f"Please enter a number between {minimum} and {maximum}.")


def prompt_choice(label: str, options: list[str], default: str) -> str:
    options_display = ", ".join(options)
    while True:
        value = prompt_text(f"{label} ({options_display})", default).lower()
        if value in options:
            return value
        print(f"Choose one of: {options_display}")


def prompt_yes_no(label: str, default: bool = False) -> bool:
    default_text = "Y/n" if default else "y/N"
    while True:
        value = input(f"{label} [{default_text}]: ").strip().lower()
        if not value:
            return default
        if value in {"y", "yes"}:
            return True
        if value in {"n", "no"}:
            return False
        print("Please answer y or n.")


def resolve_api_key() -> str:
    env_key = os.getenv("GOOGLE_MAPS_API_KEY", "").strip()
    if env_key:
        print("Using API key from GOOGLE_MAPS_API_KEY.")
        return env_key

    print(
        "No GOOGLE_MAPS_API_KEY environment variable found.\n"
        "Create a key in Google Cloud Console and enable the Maps Static API.\n"
        "Tip: export GOOGLE_MAPS_API_KEY='your_key' before running this script."
    )
    return prompt_text("Google Maps API key")


def collect_common_options() -> dict:
    latitude = prompt_float("Latitude")
    longitude = prompt_float("Longitude")
    zoom = prompt_int("Zoom level", DEFAULT_ZOOM, 0, 21)
    size = prompt_text("Image size (WIDTHxHEIGHT)", DEFAULT_SIZE)
    maptype = prompt_choice(
        "Map type",
        ["roadmap", "satellite", "terrain", "hybrid"],
        "roadmap",
    )
    output = prompt_text("Output filename", DEFAULT_OUTPUT)
    return {
        "latitude": latitude,
        "longitude": longitude,
        "zoom": zoom,
        "size": size,
        "maptype": maptype,
        "output": output,
    }


def run_simple_screenshot(shooter: GoogleMapScreenShooter) -> None:
    print("\n--- Simple screenshot ---")
    options = collect_common_options()
    path = shooter.take_screenshot(**options, marker=False)
    print(f"\nSaved map screenshot to: {path}")


def run_marker_screenshot(shooter: GoogleMapScreenShooter) -> None:
    print("\n--- Screenshot with marker ---")
    options = collect_common_options()
    label = prompt_text("Marker label (1 character)", "A")
    path = shooter.take_screenshot(
        **options,
        marker=True,
        marker_label=label,
    )
    print(f"\nSaved map screenshot with marker to: {path}")


def show_help() -> None:
    print(
        """
How to use
----------
1. Create a Google Cloud project.
2. Enable "Maps Static API".
3. Create an API key.
4. Optionally set it once in your shell:

   export GOOGLE_MAPS_API_KEY='your_key_here'

5. Run this script and choose an option from the menu.

Coordinates tip
---------------
Latitude and longitude look like: 35.6892, 51.3890
You can copy them from Google Maps by right-clicking a place.
""".strip()
    )


def print_menu() -> None:
    print(
        """
===============================
 Google Map Screenshoter
===============================
1) Simple screenshot
2) Screenshot with marker
3) Help / setup guide
4) Exit
""".rstrip()
    )


def main() -> int:
    try:
        api_key = resolve_api_key()
        shooter = GoogleMapScreenShooter(api_key)
    except (ValueError, KeyboardInterrupt) as exc:
        print(f"\n{exc or 'Cancelled.'}")
        return 1

    while True:
        print_menu()
        choice = input("Choose an option [1-4]: ").strip()

        try:
            if choice == "1":
                run_simple_screenshot(shooter)
            elif choice == "2":
                run_marker_screenshot(shooter)
            elif choice == "3":
                show_help()
            elif choice == "4":
                print("Goodbye.")
                return 0
            else:
                print("Invalid option. Choose 1, 2, 3, or 4.")
                continue
        except requests.HTTPError as exc:
            print(f"\nHTTP error from Google Maps: {exc}")
        except (ValueError, RuntimeError, OSError) as exc:
            print(f"\nError: {exc}")
        except KeyboardInterrupt:
            print("\nCancelled.")
            return 1

        input("\nPress Enter to return to the menu...")


if __name__ == "__main__":
    sys.exit(main())
