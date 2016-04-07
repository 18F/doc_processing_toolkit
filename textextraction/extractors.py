import glob
import logging
import os
import re
import subprocess
import tempfile

from boto.s3.key import Key
from boto.s3.connection import S3Connection


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

        document = subprocess.check_output(
            args=[self.text_arg_str.format(self.doc_path, self.tika_port)],
            shell=True
        )
        logging.info("%s converted to text from pdf", self.doc_path)
        return document

    def extract_metadata(self):
        """
        Extracts metadata using Tika into a json file
        """

        metadata = subprocess.check_output(
            args=[
                self.metadata_arg_str.format(
                    self.doc_path, self.tika_port)],
            shell=True
        )
        self.save(metadata.decode('utf-8'), ext='_metadata.json')

    def extract(self):
        """
        Converts and extracts metadata for any document type compatiable
        with Tika, (http://tika.apache.org/1.7/formats.html) but does not
        check if extraction produces text.
        """
        self.extract_metadata()
        self.save(self.doc_to_text().decode('utf-8'), ext='.txt')


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

        args = ['pdffonts', self.doc_path]
        pdffonts_output = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
        )
        result = None
        if pdffonts_output.communicate()[0].decode("utf-8").count("\n") > 2:
            result = True
        retcode = pdffonts_output.returncode
        if retcode:
            raise subprocess.CalledProcessError(retcode, args)
        if result:
            return result

    def cat_and_clean(self, out_file, main_text_file):
        """ Concatenates file to main text file and removes individual file """

        out_file = out_file + '.txt'
        cat_arg = 'cat {0} >> {1}'.format(out_file, main_text_file)
        subprocess.check_call(args=[cat_arg], shell=True)
        os.remove(out_file)

    def img_to_text(self):
        """ Uses Tesseract OCR to convert png image to text file """

        main_text_file = self.root + '.txt'
        for png in sorted(glob.glob('%s_*.png' % self.root)):
            out_file = png[:-4]
            args = ['tesseract', png, out_file, '-l', 'eng']
            doc_process = subprocess.Popen(
                args=args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            doc_process.communicate()
            if doc_process.returncode:
                raise subprocess.CalledProcessError(doc_process.returncode,
                                                    args)
            self.cat_and_clean(out_file, main_text_file)

        logging.info("%s converted to text from image", self.root + '.png')
        return main_text_file

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
            doc_text = self.doc_to_text().decode('utf-8')
            # Determine if extraction suceeded
            if self.meets_len_threshold(doc_text):
                self.save(doc_text, ext='.txt')
            else:
                needs_ocr = True
        if needs_ocr:
            self.pdf_to_img()
            self.img_to_text()


class TextExtractionS3(TextExtraction):

    def __init__(self, file_key, s3_bucket, tika_port=9998, host='localhost'):
        """ Connects to s3 bucket and downloads file into a temp dir
        before using super to initalize like TextExtraction """

        self.file_key = file_key
        self.s3_bucket = s3_bucket

        self.temp = tempfile.TemporaryDirectory()
        doc_path = os.path.join(self.temp.name, os.path.basename(file_key))

        k = Key(self.s3_bucket)
        k.key = self.file_key
        k.get_contents_to_filename(doc_path)

        super().__init__(doc_path, tika_port, host)

    def save(self, document, ext):
        """ Save document to s3 """

        root, old_ext = os.path.splitext(self.file_key)
        s3_path = root + ext

        k = Key(self.s3_bucket)
        k.key = s3_path
        k.set_contents_from_string(str(document))


class PDFTextExtractionS3(TextExtractionS3, PDFTextExtraction):

    def __init__(self, file_key, s3_bucket, tika_port=9998, host='localhost',
                 word_threshold=10):

        TextExtractionS3.__init__(self, file_key, s3_bucket, tika_port, host)
        self.WORDS = re.compile('[A-Za-z]{3,}')
        self.word_threshold = word_threshold

    def img_to_text(self):
        """ Extends img_to_text from PDFTextExtraction and adds a s3 save
        function """

        main_text_file = super().img_to_text()
        local_base, text_file_name = os.path.split(main_text_file)
        s3_base, s3_doc_name = os.path.split(self.file_key)

        k = Key(self.s3_bucket)
        k.key = os.path.join(s3_base, text_file_name)
        k.set_contents_from_filename(main_text_file)


def text_extractor(doc_path, force_convert=False):
    """Checks if document has been converted and sends file to appropriate
    converter"""

    root, extension = os.path.splitext(doc_path)
    if not os.path.exists(root + ".txt") or force_convert:
        if extension == '.pdf':
            extractor = PDFTextExtraction(doc_path)
        else:
            extractor = TextExtraction(doc_path)
        extractor.extract()


def text_extractor_s3(file_key, s3_bucket, force_convert=True):
    """ Checks if document has been converted in s3 bucket and and sends file
    to appropriate converter"""

    root, extension = os.path.splitext(file_key)
    if not force_convert:
        if len(list(s3_bucket.list(root + '.txt'))) > 0:
            logging.info("%s has already been converted", file_key)
            return
    if extension == ".pdf":
        extractor = PDFTextExtractionS3(file_key, s3_bucket)
    else:
        extractor = TextExtractionS3(file_key, s3_bucket)
    logging.info("%s is being converted", file_key)
    extractor.extract()
