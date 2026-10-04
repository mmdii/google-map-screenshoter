# google-map-screenshoter

Interactive terminal tool that downloads Google Maps screenshots with the Maps Static API.

## Setup

```bash
pip install -r requirements.txt
export GOOGLE_MAPS_API_KEY='your_key_here'
python gshoter.py
```

1. Create a Google Cloud project.
2. Enable **Maps Static API**.
3. Create an API key.
4. Set `GOOGLE_MAPS_API_KEY`, or paste the key when the script asks for it.

## Menu

1. **Simple screenshot** — map image for any latitude/longitude
2. **Screenshot with marker** — same image with a red pin/label
3. **Help / setup guide**
4. **Exit**

You can also choose zoom, image size, map type (`roadmap`, `satellite`, `terrain`, `hybrid`), and output filename.

## Tests

```bash
pip install -r requirements.txt
python -m unittest -v
```
