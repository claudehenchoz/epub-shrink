import argparse
import os
import io
import logging
import zipfile
import mimetypes
from PIL import Image
import pandas as pd
from rich.console import Console
from rich.table import Table
from rich import box

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('in_epub_filepath', help='Input EPUB file path')
    parser.add_argument('out_epub_filepath', help='Output EPUB file path')
    parser.add_argument('-l', '--log-level', help='Set the logging level')
    parser.add_argument('--jpeg-quality', type=int, default=75, help='JPEG compression quality')
    parser.add_argument('--image-resize-percent', type=int, help='Percentage to resize images')
    parser.add_argument('--image-resize-resample', help='Resampling method when resizing images')
    parser.add_argument('--image-resize-maxwidth', type=int, help='Maximum width for images')
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
    df = pd.DataFrame(columns=['filename', 'in_size', 'out_size'])
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
            row = {
                'filename': in_book.getinfo(item).filename, 
                'in_size':  in_book.getinfo(item).compress_size, 
                'out_size': out_book.getinfo(item).compress_size
            }
            row_df = pd.DataFrame(row, index=[0])
            df = pd.concat([df, row_df], ignore_index=True)
    return df

def compress_and_resize_image(content, subtype, args):
    if subtype not in {'jpeg', 'jpg', 'png'}:
        return content

    img = Image.open(io.BytesIO(content))
    if args.image_resize_percent:
        img = resize_image(img, args.image_resize_percent, args.image_resize_resample)
    if args.image_resize_maxwidth:
        width, height = img.size
        if width > args.image_resize_maxwidth:
            ratio = args.image_resize_maxwidth / width
            new_height = int(height * ratio)
            img.thumbnail((args.image_resize_maxwidth, new_height), Image.LANCZOS)

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

def format_bytes(size):
    is_negative = size < 0
    size = abs(float(size))
    suffixes = [' b', 'KB', 'MB']
    i = 0
    while size >= 1024 and i < len(suffixes)-1:
        size /= 1024.0
        i += 1
    formatted_size = "{:.2f} {}".format(size, suffixes[i])
    if is_negative:
        formatted_size = "-" + formatted_size
    return formatted_size

def report_file_sizes(df, args):
    df['filetype'] = df['filename'].apply(lambda x: os.path.splitext(x)[1][1:])
    totals_per_filetype = df.groupby('filetype')[['in_size', 'out_size']].sum().reset_index()
    totals_per_filetype['size_diff'] = totals_per_filetype['out_size'] - totals_per_filetype['in_size']
    
    totals_per_filetype['percent_diff'] = (totals_per_filetype['size_diff'] / totals_per_filetype['in_size']) * 100
    totals_per_filetype_sorted = totals_per_filetype.sort_values(by='percent_diff', ascending=True, ignore_index=True)

    # Create a console object
    console = Console()

    console.print("")
    console.print("epub-shrink")
    console.print("-----------")
    console.print("")
    console.print(f" Input  EPUB: {args.in_epub_filepath}")
    console.print(f" Output EPUB: {args.out_epub_filepath}", style="bold")

    # Create a table
    table = Table(show_header=True)
    table.add_column("Filetype", width=12)
    table.add_column("In Size", justify="right")
    table.add_column("Out Size", justify="right")
    table.add_column("Size Diff", justify="right")
    table.add_column("Percent Diff", justify="right")

    # Fill the table with data from the DataFrame
    for index, row in totals_per_filetype_sorted.iterrows():
        table.add_row(
            row['filetype'],
            str(format_bytes(row['in_size'])),
            str(format_bytes(row['out_size'])),
            str(format_bytes(row['size_diff'])),
            f"{row['percent_diff']:.2f}%"
        )

    table.add_row(end_section=True)

    total_percentage = totals_per_filetype_sorted['size_diff'].sum() / totals_per_filetype_sorted['in_size'].sum() * 100
    formatted_total_percentage = f"{total_percentage:.2f}%"

    table.add_row(
        'Total',
        str(format_bytes(totals_per_filetype_sorted['in_size'].sum())),
        str(format_bytes(totals_per_filetype_sorted['out_size'].sum())),
        str(format_bytes(totals_per_filetype_sorted['size_diff'].sum())),
        formatted_total_percentage, style="bold"
    )

    for box_style in [
            box.SQUARE,
            box.MINIMAL,
            box.SIMPLE,
            box.SIMPLE_HEAD,
        ]:
        table.box = box_style
    table.pad_edge = False

    # Print the table
    console.print(table)

def main():
    args = parse_arguments()
    configure_logging(args.log_level)
    out_path = validate_file_paths(args.in_epub_filepath, args.out_epub_filepath)
    if args.image_resize_percent:
        args.image_resize_percent = adjust_image_resize_percent(args.image_resize_percent)
    report_data = process_epub_files(args.in_epub_filepath, out_path, args)
    report_file_sizes(report_data, args)

if __name__ == '__main__':
    main()
