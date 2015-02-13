import logging
import subprocess

"""
The functions below are minimal Python wrappers Ghostscript, Tika, and
Tesseract. They are intended to simplify converting pdf files into usable text.
"""


def save_text(document, export_path):
    """ Reads document text and saves it to specified export path """

    with open(export_path, 'w') as f:
        f.write(document.stdout.read())


def img_to_text(img_path, export_path=None):
    """ Uses Tesseract OCR to convert tiff image to text file """

    if not export_path:
        export_path = img_path.replace(".tiff", "_new")

    document = subprocess.Popen(
        args=['tesseract', img_path, export_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    document.communicate()
    logging.info("%s converted to text from image", img_path)
    return export_path


def pdf_to_img(doc_path, export_path=None):
    """ Converts and saves pdf file to tiff image using Ghostscript"""

    if not export_path:
        export_path = doc_path.replace(".pdf", ".tiff")

    args = 'gs -dNOPAUSE -dBATCH -sDEVICE=tiffg4 -sOutputFile={0} {1}'
    args = args.format(export_path, doc_path)
    process = subprocess.Popen(
        args=[args],
        shell=True,
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE
    )
    process.communicate()
    logging.info("%s converted to tiff image", doc_path)
    return export_path


def pdf_to_text(doc_path, port=9998):
    """ Converts a document to text using the Tika server """

    document = subprocess.Popen(
        args=['nc localhost {0} < {1}'.format(port, doc_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=True)
    logging.info("%s converted to text from pdf", doc_path)
    return document, doc_path


def pdf_to_text_itterator(doc_paths, port=9998):
    """ Converts a series of pdf to documents """

    for doc_path in doc_paths:
        yield pdf_to_text(doc_path=doc_path, port=port)
