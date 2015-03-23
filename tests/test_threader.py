import os
from unittest import TestCase, skipUnless
from .test_extraction import file_iterator, delete_files
from textextraction.threader import AsyncConvert


ALL_INSTALLED = os.getenv("ALL_INSTALLED")

LOCAL_PATH = os.path.dirname(os.path.realpath(__file__))


class TestThreader(TestCase):
    def tearDown(self):
        """
        Removes file created during the test
        """
        delete_files()

    @skipUnless(ALL_INSTALLED == "True", 'Installation is ready')
    def test_textextractor(self):
        """
        Verify that the threader sends file to correct extractor
        """
        docs_to_convert = [
            'record_text.pdf',
            'excel_spreadsheet.xlsx',
            'record_no_text.pdf',
            'record_some_text.pdf',
        ]

        AsyncConvert.extractor_factory(
            file_iterator=file_iterator(docs_to_convert), use_join=True)

        # Check if conversions exist
        for doc_path in file_iterator(docs_to_convert):
            root, extension = os.path.splitext(doc_path)
            self.assertTrue(os.path.isfile(root + '.txt'))
            self.assertTrue(os.path.isfile(root + '_metadata.json'))

        # Check that only doc with no text used OCR
        self.assertTrue(
            os.path.isfile(LOCAL_PATH + '/fixtures/record_no_text.tiff'))
        self.assertTrue(
            os.path.isfile(LOCAL_PATH + '/fixtures/record_some_text.tiff'))
        self.assertFalse(
            os.path.isfile(LOCAL_PATH + '/fixtures/record_text.tiff'))
        self.assertFalse(
            os.path.isfile(LOCAL_PATH + '/fixtures/excel_spreadsheet.tiff'))
