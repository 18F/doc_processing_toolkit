import glob
import logging
import os
import re
import subprocess

"""
The functions below are minimal Python wrappers Ghostscript, Tika, and
Tesseract. They are intended to simplify converting pdf files into usable text.
"""

WORDS = re.compile('[A-Za-z]{3,}')


def get_doc_length(doc_text):
    """ Return the length of a document and doc text """

    return len(tuple(WORDS.finditer(doc_text)))


def check_for_text(doc_path, extension):
    """
    Using `pdffonts` returns True if document has fonts, which in essence
    means it has text. If a document is not a pdf automatically returns True.
    """
    has_text = False
    if extension == '.pdf':
        pdffonts_output = subprocess.Popen(
            ['pdffonts %s' % doc_path],
            shell=True,
            stdout=subprocess.PIPE,
        )
        if pdffonts_output.communicate()[0].decode("utf-8").count("\n") > 2:
            has_text = True
    else:
        has_text = True
    return has_text


def save_text(document, export_path=None):
    """ Reads document text and saves it to specified export path """

    with open(export_path, 'w') as f:
        f.write(document)


def img_to_text(img_path, export_path=None):
    """ Uses Tesseract OCR to convert tiff image to text file """

    if not export_path:
        export_path = img_path.replace(".tiff", '')

    document = subprocess.Popen(
        args=['tesseract', img_path, export_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    document.communicate()
    logging.info("%s converted to text from image", img_path)
    return export_path


def pdf_to_img(doc_path):
    """ Converts and saves pdf file to tiff image using Ghostscript"""

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


def doc_to_text(doc_path, port=9998):
    """ Converts a document to text using the Tika server """

    document = subprocess.Popen(
        args=['nc localhost {0} < {1}'.format(port, doc_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=True
    )
    logging.info("%s converted to text from pdf", doc_path)
    return document


def extract_metadata(doc_path, extension, port=8887):
    """
    Extracts metadata using Tika into a json file
    """

    m_path = doc_path.replace(extension, '_metadata.json')
    subprocess.call(
        args=['nc localhost {0} < {1} > {2}'.format(port, doc_path, m_path)],
        shell=True
    )


def DocTextExtractor(glob_path, skip_converted=True,
                     text_port=9998, data_port=8887):
    """
    Converts and produces metadata for any document type compatiable with
    Tika, (http://tika.apache.org/1.7/formats.html) but does not check
    if extraction produces text.
    """
    for doc_path in glob.iglob(glob_path):
        root, extension = os.path.splitext(doc_path)
        if os.path.exists(doc_path.replace(extension, '.txt')) and \
                skip_converted:
            logging.info("%s: has already been converted", doc_path)
        else:
            # Extract Metadata
            extract_metadata(
                doc_path=doc_path, extension=extension, port=data_port)
            doc = doc_to_text(doc_path=doc_path, port=text_port)
            doc_text = doc.stdout.read().decode('utf-8')
            save_text(doc_text, doc_path.replace(extension, ".txt"))


def PDFTextExtractor(glob_path, skip_converted=True,
                     text_port=9998, data_port=8887):
    """
    Produces metadata and converts pdfs to text. Uses OCR if the initial
    attempt fails
    """

    for doc_path in glob.iglob(glob_path):
        root, extension = os.path.splitext(doc_path)
        if os.path.exists(doc_path.replace(extension, '.txt')) and \
                skip_converted:
            logging.info("%s: has already been converted", doc_path)
        else:
            extraction_succeeded = False
            # Extract Metadata
            extract_metadata(
                doc_path=doc_path, extension=extension, port=data_port)
            # Check if the document has text
            if check_for_text(doc_path, extension):
                doc = doc_to_text(doc_path=doc_path, port=text_port)
                doc_text = doc.stdout.read().decode('utf-8')
                # Check if text extraction succeeded
                if get_doc_length(doc_text) > 10:
                    extraction_succeeded = True
            # If extraction fails use ORC
            if extraction_succeeded:
                save_text(doc_text, doc_path.replace(extension, ".txt"))
            else:
                img_path = pdf_to_img(doc_path)
                img_to_text(img_path)
