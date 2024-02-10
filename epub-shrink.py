import argparse
import os
import io
import logging
import zipfile
import mimetypes
from PIL import Image

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('in_epub_filepath', help='Input EPUB file path')
    parser.add_argument('out_epub_filepath', help='Output EPUB file path')
    parser.add_argument('-l', '--log-level', help='Set the logging level')
    parser.add_argument('--jpeg-quality', type=int, default=75, help='JPEG compression quality')
    parser.add_argument('--image-resize-percent', type=int, help='Percentage to resize images')
    parser.add_argument('--image-resize-resample', help='Resampling method when resizing images')
    parser.add_argument('--grayscale', action='store_true', help='Make images grayscale')
    return parser.parse_args()

def configure_logging(level):
    if level:
        log_level = getattr(logging, level.upper(), None)
        if not isinstance(log_level, int):
            raise ValueError(f'Invalid log level: {level}')
        logging.basicConfig(level=log_level)

def validate_file_paths(in_path, out_path):
    if not os.path.isfile(in_path):
        raise FileNotFoundError(in_path)
    if os.path.isdir(out_path):
        return os.path.join(out_path, os.path.basename(in_path))
    if out_path == in_path:
        raise FileExistsError(out_path)
    return out_path

def adjust_image_resize_percent(percent):
    return percent / 100.0 if percent else None

def process_epub_files(in_path, out_path, args):
    with zipfile.ZipFile(in_path, 'r') as in_book, \
            zipfile.ZipFile(out_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as out_book:
        for item in in_book.namelist():
            with in_book.open(item) as in_file:
                content = in_file.read()
                mime_type, _ = mimetypes.guess_type(item)
                if mime_type and mime_type.startswith('image/'):
                    _, subtype = mime_type.split('/')
                    content = compress_and_resize_image(content, subtype, args)
                out_book.writestr(item, content)

def compress_and_resize_image(content, subtype, args):
    if subtype not in {'jpeg', 'jpg', 'png'}:
        return content

    img = Image.open(io.BytesIO(content))
    if args.image_resize_percent:
        img = resize_image(img, args.image_resize_percent, args.image_resize_resample)
    if args.grayscale:
        img = img.convert('L')
    format_, params = determine_image_format_and_params(subtype, args)
    return save_image_to_buffer(img, format_, params)

def resize_image(img, resize_percent, resample_method):
    new_size = [int(dimension * resize_percent) for dimension in img.size]
    resample = getattr(Image, resample_method.upper(), None) if resample_method else None
    logging.info(f'Resizing image from {img.size} to {new_size}')
    return img.resize(new_size, resample)

def determine_image_format_and_params(subtype, args):
    params = {'optimize': True}
    if subtype in {'jpeg', 'jpg'}:
        return 'JPEG', {**params, 'quality': args.jpeg_quality}
    elif subtype == 'png':
        return 'PNG', params

def save_image_to_buffer(img, format_, params):
    buffer = io.BytesIO()
    img.save(buffer, format=format_, **params)
    return buffer.getvalue()

def report_file_sizes(in_path, out_path):
    in_size = os.path.getsize(in_path)
    out_size = os.path.getsize(out_path)
    reduction_percent = (1 - (out_size / in_size)) * 100
    print(f"Original file size: {in_size} bytes")
    print(f"Output file size: {out_size} bytes")
    print(f"Reduction in file size: {reduction_percent:.2f}%")

def main():
    args = parse_arguments()
    configure_logging(args.log_level)
    out_path = validate_file_paths(args.in_epub_filepath, args.out_epub_filepath)
    if args.image_resize_percent:
        args.image_resize_percent = adjust_image_resize_percent(args.image_resize_percent)
    process_epub_files(args.in_epub_filepath, out_path, args)
    report_file_sizes(args.in_epub_filepath, out_path)

if __name__ == '__main__':
    main()
