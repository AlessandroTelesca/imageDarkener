# Image Darkener

A small desktop app for recoloring bright pixels in an image using RGB threshold sliders.

This repository now also includes a browser-based TypeScript version for static hosting on GitHub Pages.

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

## Web Version (TypeScript)

The web app source is TypeScript-only and is built at deploy time.

- TypeScript source: `web/main.ts`
- Web entry HTML: `index.html`
- Styles: `web/styles.css`
- Build output: `dist/` (generated; not committed)

### Build Web Assets

From the project root:

```powershell
npm install
npm run build:web
```

### Run Locally (Static Preview)

Run a local dev server with hot reload:

```powershell
npm run dev:web
```

Or preview the production build:

```powershell
npm run build:web
npm run preview:web
```

### Enable GitHub Pages

1. Push the repository to GitHub.
2. Go to repository **Settings -> Pages**.
3. Under **Build and deployment**, choose:
	- **Source**: GitHub Actions
4. Save.
5. The workflow in `.github/workflows/pages.yml` builds TypeScript and deploys `dist/`.
6. Your app will be published at your GitHub Pages URL.

## Notes

- Input images should be placed in `src/images/`.
- The saved output defaults to `img_bright_recolored.jpg` in the project root.
- In the web version, use the file picker to upload an image and download the processed result.
