# Image Darkener

A small desktop app for recoloring bright pixels in an image using RGB threshold sliders.

## Features

- Loads the first image found in `src/images/`
- Lets you pick minimum RGB threshold values
- Recolors matching pixels to a selected output RGB color
- Live preview with save support

## Requirements

- Python 3.10+
- Dependencies listed in `requirements.txt`

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```powershell
pip install -r requirements.txt
```

## Run

From the project root:

```powershell
python src/imageDarkener.py
```

## Notes

- Input images should be placed in `src/images/`.
- The saved output defaults to `img_bright_recolored.jpg` in the project root.
