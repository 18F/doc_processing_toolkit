import os
import moto
import boto

from boto.s3.key import Key
from unittest import TestCase, main
from textextraction.extractors import (TextExtraction, PDFTextExtraction,
                                       TextExtractionS3, PDFTextExtractionS3,
                                       text_extractor)

LOCAL_PATH = os.path.dirname(os.path.realpath(__file__))


def file_iterator(base_files, extensions=['']):
    """
    Iterates through a list of base_files with each extension given
    """
    for base_file in base_files:
        for extension in extensions:
            yield os.path.join(LOCAL_PATH, 'fixtures', base_file + extension)


def delete_files():
    """
    Deletes files between tests
    """
    items_to_delete = [
        'record_text',
        'record_no_text',
        'excel_spreadsheet',
        'record_some_text'
    ]
    extensions = ['_metadata.json', '_001.png', '.txt']
    for item_path in file_iterator(items_to_delete, extensions):
        if os.path.isfile(item_path):
            os.remove(item_path)


class TestTextExtraction(TestCase):

    def tearDown(self):
        """
        Removes file created during the test
        """
        delete_files()

    def test_extract_metadata(self):
        """
        Check if meta data is properly created
        """
        extractor = TextExtraction(
            doc_path=os.path.join(LOCAL_PATH, 'fixtures/record_text.pdf'))
        extractor.extract_metadata()
        self.assertTrue(os.path.isfile(
            os.path.join(LOCAL_PATH, 'fixtures/record_text_metadata.json')))

    def test_doc_to_text(self):
        """
        Check if document text is properly extracted, when possible
        """
        extractor = TextExtraction(
            doc_path=os.path.join(LOCAL_PATH, 'fixtures/record_text.pdf'))
        doc = extractor.doc_to_text()
        self.assertTrue(
            'Cupcake ipsum dolor sit' in doc.stdout.read().decode('utf-8'))

        extractor = TextExtraction(
            doc_path=os.path.join(LOCAL_PATH, 'fixtures/record_no_text.pdf'))
        doc = extractor.doc_to_text()
        self.assertEqual(doc.stdout.read().decode('utf-8').strip('\n'), '')

    def test_extract(self):
        """
        Check if TextExtractor correctly extracts text from xlsx and pdf
        document without checking for text
        """
        items_to_convert = [
            'record_text.pdf',
            'record_no_text.pdf',
            'excel_spreadsheet.xlsx'
        ]
        for item_path in file_iterator(items_to_convert):
            extractor = TextExtraction(doc_path=item_path)
            extractor.extract()
            self.assertTrue(os.path.isfile(extractor.root + '.txt'))
            self.assertTrue(os.path.isfile(extractor.root + '_metadata.json'))
            self.assertFalse(os.path.isfile(extractor.root + '_001.png'))


class TestPDFTextExtraction(TestCase):

    def tearDown(self):
        """
        Removes file created during the test
        """
        delete_files()

    def test_meets_len_threshold(self):
        """
        Tests to ensure that doc length function only captures words with
        over 3 characters
        """

        extractor = PDFTextExtraction(doc_path='', word_threshold=3)

        text = "word words more words"
        self.assertEqual(extractor.meets_len_threshold(text), True)

        text = "12323 word w a9s90s"
        self.assertEqual(extractor.meets_len_threshold(text), None)

    def test_has_text(self):
        """
        Check if check_for_text returns True when document contains text
        """

        doc_path = os.path.join(LOCAL_PATH, "fixtures/record_text.pdf")
        extractor = PDFTextExtraction(doc_path=doc_path)
        self.assertTrue(extractor.has_text())

        doc_path = os.path.join(LOCAL_PATH, "fixtures/record_no_text.pdf")
        extractor = PDFTextExtraction(doc_path=doc_path)
        self.assertFalse(extractor.has_text())

    def test_pdf_to_img_and_img_to_text(self):
        """
        Check if pdf docs can be converted to images and then to text
        """
        extractor = PDFTextExtraction(
            doc_path=os.path.join(LOCAL_PATH, 'fixtures/record_no_text.pdf'))
        extractor.pdf_to_img()
        extractor.img_to_text()
        self.assertTrue(os.path.isfile(
            os.path.join(LOCAL_PATH, 'fixtures/record_no_text.pdf')))

    def test_extract(self):
        """
        Check if PDFTextExtractor correctly extracts text from PDF document
        and reverts to ORC when extraction fails
        """
        # Run extraction
        extractor = PDFTextExtraction(
            doc_path=os.path.join(LOCAL_PATH, 'fixtures/record_text.pdf'))
        extractor.extract()

        extractor = PDFTextExtraction(
            doc_path=os.path.join(LOCAL_PATH, 'fixtures/record_no_text.pdf'))
        extractor.extract()

        # Check for image file, when no text
        self.assertTrue(os.path.isfile(
            os.path.join(LOCAL_PATH, 'fixtures/record_text.txt')))
        self.assertFalse(os.path.isfile(
            os.path.join(LOCAL_PATH, 'fixtures/record_text_001.png')))
        self.assertTrue(os.path.isfile(
            os.path.join(LOCAL_PATH, 'fixtures/record_text_metadata.json')))

        self.assertTrue(os.path.isfile(
            os.path.join(LOCAL_PATH, 'fixtures/record_no_text.txt')))
        self.assertTrue(os.path.isfile(
            os.path.join(LOCAL_PATH, 'fixtures/record_no_text_001.png')))
        self.assertTrue(os.path.isfile(os.path.join(
            LOCAL_PATH, 'fixtures/record_no_text_metadata.json')))


class Testtextextractor(TestCase):

    def tearDown(self):
        """
        Removes file created during the test
        """
        delete_files()

    def test_text_extractor(self):
        """
        Verify that the threader sends file to correct extractor
        """
        docs_to_convert = [
            'record_text.pdf',
            'excel_spreadsheet.xlsx',
            'record_no_text.pdf',
            'record_some_text.pdf',
        ]

        # Convert and check if conversions exist
        for doc_path in file_iterator(docs_to_convert):
            text_extractor(doc_path)
            root, extension = os.path.splitext(doc_path)
            self.assertTrue(os.path.isfile(root + '.txt'))
            self.assertTrue(os.path.isfile(root + '_metadata.json'))

        # Check that only doc with no text used OCR
        self.assertTrue(os.path.isfile(
            os.path.join(LOCAL_PATH, 'fixtures/record_no_text_001.png')))
        self.assertTrue(os.path.isfile(
            os.path.join(LOCAL_PATH, 'fixtures/record_some_text_001.png')))
        self.assertFalse(os.path.isfile(
            os.path.join(LOCAL_PATH, 'fixtures/record_text_001.png')))
        self.assertFalse(os.path.isfile(
            os.path.join(LOCAL_PATH, 'fixtures/excel_spreadsheet_001.png')))


class TestTextExtractionS3(TestCase):

    @moto.mock_s3
    def test_init(self):
        """ Test that TextExtractionS3 correctly initalizes and saves
        document from s3 to local temp repo and vice versa """

        # Create mock connection to s3 and add pdf
        conn = boto.connect_s3()
        conn.create_bucket('testbucket')
        s3_bucket = conn.get_bucket('testbucket')
        k = Key(s3_bucket)
        k.key = 'testfile.pdf'
        k.set_contents_from_filename(
            os.path.join(LOCAL_PATH, 'fixtures/record_no_text.pdf'))
        returned_file = conn.get_bucket('testbucket').get_key('testfile.pdf')
        self.assertEqual('testfile.pdf', returned_file.name)

        # Init TextExtractionS3 and assert that s3 file was downloaded
        self.extractor = TextExtractionS3(
            file_key='testfile.pdf', s3_bucket=s3_bucket)
        self.assertTrue(os.path.exists(self.extractor.doc_path))

        self.extractor.extract_metadata()
        item = list(self.extractor.s3_bucket.list('testfile_metadata.json'))
        self.assertEqual(item[0].name, 'testfile_metadata.json')


class TestPDFTextExtractionS3(TestCase):

    # PDFTextExtractionS3
    @moto.mock_s3
    def test_init(self):
        """ Test that PDFTextExtractionS3 correctly initalizes and saves
        document from s3 after OCR """

        # Create mock connection to s3 and add pdf
        conn = boto.connect_s3()
        conn.create_bucket('testbucket')
        s3_bucket = conn.get_bucket('testbucket')
        k = Key(s3_bucket)
        k.key = 'testfile.pdf'
        k.set_contents_from_filename(
            os.path.join(LOCAL_PATH, 'fixtures/record_no_text.pdf'))

        # Init PDFTextExtractionS3 and assert that s3 file was downloaded
        self.extractor = PDFTextExtractionS3(
            file_key='testfile.pdf', s3_bucket=s3_bucket)
        self.assertTrue(os.path.exists(self.extractor.doc_path))

        # Convert document with OCR and test if files are in the s3 bucket
        self.extractor.extract()
        item = list(self.extractor.s3_bucket.list('testfile.txt'))
        self.assertEqual(item[0].name, 'testfile.txt')
        item = list(self.extractor.s3_bucket.list('testfile_metadata.json'))
        self.assertEqual(item[0].name, 'testfile_metadata.json')

if __name__ == '__main__':
    main()
