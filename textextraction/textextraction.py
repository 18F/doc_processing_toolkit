import logging
import os
import re
import subprocess

"""
The functions below are minimal Python wrappers Ghostscript, Tika, and
Tesseract. They are intended to simplify converting pdf files into usable text.
"""


class TextExtraction:

    def __init__(self, doc_path, text_port=9998, data_port=8887):

        self.doc_path = doc_path
        self.root, self.extension = os.path.splitext(doc_path)
        self.text_port = text_port
        self.data_port = data_port

    def save_text(self, document):
        """ Reads document text and saves it to specified export path """

        export_path = self.root + ".txt"

        with open(export_path, 'w') as f:
            f.write(document)

    def doc_to_text(self):
        """ Converts a document to text using the Tika server """

        document = subprocess.Popen(
            args=['nc localhost {0} < {1}'.format(
                self.text_port, self.doc_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True
        )
        logging.info("%s converted to text from pdf", self.doc_path)
        return document

    def extract_metadata(self):
        """
        Extracts metadata using Tika into a json file
        """

        metadata_path = self.root + '_metadata.json'
        subprocess.call(
            args=['nc localhost {0} < {1} > {2}'.format(
                self.data_port, self.doc_path, metadata_path)],
            shell=True
        )

    def extract(self):
        """
        Converts and extracts metadata for any document type compatiable
        with Tika, (http://tika.apache.org/1.7/formats.html) but does not
        check if extraction produces text.
        """
        self.extract_metadata()
        self.save_text(self.doc_to_text().stdout.read().decode('utf-8'))


class PDFTextExtraction(TextExtraction):

    def __init__(self, doc_path, text_port=9998, data_port=8887,
                 word_threshold=10):

        super(self.__class__, self).__init__(
            doc_path, text_port, data_port)
        self.WORDS = re.compile('[A-Za-z]{3,}')
        self.word_threshold = word_threshold

    def meets_len_threshold(self, doc_text):
        """
        Return True if number of words in text are more than the threshold
        """

        if len(tuple(self.WORDS.finditer(doc_text))) > self.word_threshold:
            return True

    def has_text(self):
        """
        Using `pdffonts` returns True if document has fonts, which in
        essence means it has text. If a document is not a pdf
        automatically returns True.
        """

        pdffonts_output = subprocess.Popen(
            ['pdffonts %s' % self.doc_path],
            shell=True,
            stdout=subprocess.PIPE,
        )
        if pdffonts_output.communicate()[0].decode("utf-8").count("\n") > 2:
            return True

    def img_to_text(self):
        """ Uses Tesseract OCR to convert tiff image to text file """

        document = subprocess.Popen(
            args=['tesseract', self.root + '.tiff', self.root],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        document.communicate()
        logging.info("%s converted to text from image", self.root + '.tiff')

    def pdf_to_img(self):
        """ Converts and saves pdf file to tiff image using Ghostscript"""

        export_path = self.root + ".tiff"

        args = 'gs -dNOPAUSE -dBATCH -sDEVICE=tiffg4 -sOutputFile={0} {1}'
        args = args.format(export_path, self.doc_path)
        process = subprocess.Popen(
            args=[args],
            shell=True,
            stderr=subprocess.STDOUT,
            stdout=subprocess.PIPE
        )
        process.communicate()
        logging.info("%s converted to tiff image", self.doc_path)
        return export_path

    def extract(self):
        """
        Converts pdfs to text and extracts metadata. Uses OCR if the
        initial attempt fails.
        """

        self.extract_metadata()
        needs_ocr = False
        # Determine if PDF has text
        if not self.has_text():
            needs_ocr = True
        else:
            doc_text = self.doc_to_text().stdout.read().decode('utf-8')
            # Determine if extraction suceeded
            if self.meets_len_threshold(doc_text):
                self.save_text(doc_text)
            else:
                needs_ocr = True
        if needs_ocr:
            self.pdf_to_img()
            self.img_to_text()


def textextractor(doc_path, force_convert=False):
    """
    Checks if document has been converted and sends file to appropriate
    converter
    """
    root, extension = os.path.splitext(doc_path)
    if not os.path.exists(root + ".txt") or force_convert:
        if extension == '.pdf':
            extractor = PDFTextExtraction(doc_path)
        else:
            extractor = TextExtraction(doc_path)
        extractor.extract()
