import glob
import logging
import os
import re
import subprocess
import tempfile
import urllib


"""
The functions below are minimal Python wrappers around Ghostscript, Tika, and
Tesseract. They are intended to simplify converting pdf files into usable text.
"""


class TextExtraction:
    """ The TextExtraction class contains functions for extracting and saving
    metadata and text from all files compatible with Apache Tika"""

    def __init__(self, doc_path, tika_port=9998, host='localhost'):

        self.doc_path = doc_path
        self.root, self.extension = os.path.splitext(doc_path)
        self.tika_port = tika_port
        self.text_arg_str = 'curl -T {0} http://' + host + ':{1}/tika '
        self.text_arg_str += '-s --header "Accept: text/plain"'
        self.metadata_arg_str = 'curl -T {0} http://' + host + ':{1}/meta '
        self.metadata_arg_str += '-s --header "Accept: application/json"'

    def save(self, document, ext):
        """ Save document to root location """

        export_path = self.root + ext

        with open(export_path, 'w') as f:
            f.write(document)

    def doc_to_text(self):
        """ Converts a document to text using the Tika server """

        document = subprocess.Popen(
            args=[self.text_arg_str.format(self.doc_path, self.tika_port)],
            stdout=subprocess.PIPE,
            shell=True
        )
        logging.info("%s converted to text from pdf", self.doc_path)
        return document

    def extract_metadata(self):
        """
        Extracts metadata using Tika into a json file
        """

        metadata = subprocess.Popen(
            args=[
                self.metadata_arg_str.format(
                    self.doc_path, self.tika_port)],
            stdout=subprocess.PIPE,
            shell=True
        )
        self.save(metadata.stdout.read().decode('utf-8'), ext='_metadata.json')

    def extract(self):
        """
        Converts and extracts metadata for any document type compatiable
        with Tika, (http://tika.apache.org/1.7/formats.html) but does not
        check if extraction produces text.
        """
        self.extract_metadata()
        self.save(self.doc_to_text().stdout.read().decode('utf-8'), ext='.txt')


class PDFTextExtraction(TextExtraction):
    """ PDFTextExtraction adds OCR functionality to TextExtraction. The ORC
    functionality is triggered only if a PDF document is not responsive or
    if Tika fails to extract text """

    def __init__(self, doc_path, tika_port=9998,
                 host='localhost', word_threshold=10):

        super().__init__(doc_path, tika_port, host)
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
            ['pdffonts', self.doc_path],
            stdout=subprocess.PIPE,
        )
        if pdffonts_output.communicate()[0].decode("utf-8").count("\n") > 2:
            return True

    def cat_and_clean(self, out_file):
        """ Concatenates file to main text file and removes individual file """

        out_file = out_file + '.txt'
        cat_arg = 'cat {0} >> {1}'.format(out_file, self.root + '.txt')
        subprocess.check_call(args=[cat_arg], shell=True)
        os.remove(out_file)

    def img_to_text(self):
        """ Uses Tesseract OCR to convert png image to text file """

        for png in sorted(glob.glob('%s_*.png' % self.root)):
            out_file = png[:-4]
            args = ['tesseract', png, out_file, '-l', 'eng']
            doc_process = subprocess.Popen(
                args=args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            doc_process.communicate()
            self.cat_and_clean(out_file)

        logging.info("%s converted to text from image", self.root + '.png')

    def pdf_to_img(self):
        """ Converts and saves pdf file to png image using Ghostscript"""

        export_path = self.root + "_%03d.png"
        args = [
            'gs', '-dNOPAUSE', '-dBATCH', '-sDEVICE=pnggray',
            '-dINTERPOLATE', '-r300', '-dNumRenderingThreads=8',
            '-sOutputFile={0}'.format(export_path), self.doc_path
        ]
        process = subprocess.Popen(
            args=args, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
        process.communicate()
        logging.info("%s converted to png images", self.doc_path)
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
                self.save(doc_text, ext='.txt')
            else:
                needs_ocr = True
        if needs_ocr:
            self.pdf_to_img()
            self.img_to_text()


class TextExtractionS3(TextExtraction):

    def __init__(self, url, tika_port=9998, host='localhost'):
        file_name = url.split('/')[-1]
        self.temp = tempfile.TemporaryDirectory()
        doc_path, message = urllib.request.urlretrieve(
            url, os.path.join(self.temp.name, file_name))
        super().__init__(doc_path, tika_port, host)


class PDFTextExtractionS3(TextExtractionS3, PDFTextExtraction):

    def __init__(self, url, tika_port=9998, host='localhost',
                 word_threshold=10):

        # Don't user super because it follows a different inheritance line
        TextExtractionS3.__init__(self, url, tika_port, host)
        self.WORDS = re.compile('[A-Za-z]{3,}')
        self.word_threshold = word_threshold


def text_extractor(doc_path, force_convert=False):
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
