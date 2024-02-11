# epub-shrink

epub-shrink is a Python tool designed to reduce the size of EPUB files. It achieves this by compressing images, optionally resizing and converting them to grayscale, and ensuring that the EPUB file itself is compressed using maximum ZIP compression. This utility is perfect for optimizing EPUB files to make them smaller and more manageable, especially useful for devices with limited storage capacity. It was forked from https://github.com/murrple-1/epub-shrink 

## Features

- **Image Compression:** Reduces the file size of images within the EPUB without significantly compromising quality.
- **Image Resizing:** Option to resize images based on a percentage of the original size or a maximum width.
- **Grayscale Conversion:** Can convert images to grayscale to further reduce size.
- **ZIP Compression:** Ensures that the output EPUB file is compressed to the smallest possible size.

## Requirements

- Python 3.x
- Pillow library for image processing (install with `pip install Pillow`)

## Usage

```shell
python epub-shrink.py <input_epub_filepath> <output_epub_filepath> [options]
```

### Arguments

- `in_epub_filepath`: The path to the input EPUB file.
- `out_epub_filepath`: The path for the output optimized EPUB file.

### Options

- `-l`, `--log-level`: Set the logging level (e.g., INFO, DEBUG).
- `--jpeg-quality`: JPEG compression quality (default is 75).
- `--image-resize-percent`: Percentage to resize images (e.g., 50 for 50%).
- `--image-resize-maxwidth`: Resize images to a maximum with (in pixels)
- `--image-resize-resample`: Resampling method when resizing images (e.g., BILINEAR, NEAREST).
- `--grayscale`: Convert images to grayscale.

### Examples

Optimize an EPUB, reducing image quality to 75% JPEG compression:

```shell
python epub-shrink.py input.epub output.epub --jpeg-quality 75
```

Resize images to 50% of their original size and convert to grayscale:

```shell
python epub-shrink.py input.epub output.epub --image-resize-percent 50 --grayscale
```

Set log level to DEBUG for verbose output:

```shell
python epub-shrink.py input.epub output.epub --log-level DEBUG
```

## How It Works

The script reads the input EPUB file, compresses and optionally resizes and converts images to grayscale based on the provided arguments, and then writes the optimized content to a new EPUB file. It uses maximum ZIP compression for the output file to ensure the file size is as small as possible.

## Contributing

Contributions to improve epub-shrink are welcome. Feel free to fork the repository, make changes, and submit a pull request.
