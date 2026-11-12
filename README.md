# Make the cutest picture — Baby Otter Hugging a Pink Heart

A deterministic Python 3 (stdlib only) program that draws a baby otter
hugging a glossy pink heart and writes it to `entry.png` (1024x1024,
about 124 KB).

## Run

```sh
python3 main.py
```

The program reads two optional environment variables:

- `MAKEFUN_PREVIEW_PX` — canvas size in pixels (default 1024).
- `MAKEFUN_OUTPUT_DIR` — output directory (default `/output`).

The output is always a valid PNG with correct chunk checksums, and the
program is deterministic: running it twice produces byte-identical output.

## The picture

A round baby otter, centered, head tilted slightly, hugging a pink heart
with two big clumsy paws. Big glossy eyes are the most important feature.
Soft cream-to-pink gradient background, bokeh circles, and a ground shadow.
Soft 3D-render / storybook style, no hard black outlines, no text.
