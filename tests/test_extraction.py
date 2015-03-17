import os
import time
from unittest import TestCase, skipUnless, main
from textextraction import doc_process_toolkit as dpt

ALL_INSTALLED = os.getenv("ALL_INSTALLED")

LOCAL_PATH = os.path.dirname(os.path.realpath(__file__))


def file_itterator(base_files, extensions):
    """
    Itterates through a list of base_files with each extension given
    """
    local_path = os.path.dirname(os.path.realpath(__file__))
    for base_file in base_files:
        for extension in extensions:
            yield local_path + '/fixtures/' + base_file + extension


class TestDocProcessToolkit(TestCase):

    @skipUnless(ALL_INSTALLED == "True", 'Installation is ready')
    def tearDown(self):
        """
        Removes file created during the test
        """
        items_to_delete = [
            'record_text',
            'record_no_text',
            'excel_spreadsheet'
        ]
        extensions = ['_metadata.json', '.tiff', '.txt']
        for item_path in file_itterator(items_to_delete, extensions):
            if os.path.isfile(item_path):
                os.remove(item_path)

    def test_get_doc_length(self):
        """
        Tests to ensure that doc length function only captures words with
        over 3 characters
        """

        text = "word words more words"
        self.assertEqual(dpt.get_doc_length(text), 4)

        text = "12323 word w a9s90s"
        self.assertEqual(dpt.get_doc_length(text), 1)

    def test_check_for_text(self):
        """
        Check if check_for_text returns True when document contains text
        """

        doc_path = "tests/fixtures/record_text.pdf"
        self.assertTrue(dpt.check_for_text(doc_path, '.pdf'))

        doc_path = "tests/fixtures/record_no_text.pdf"
        self.assertFalse(dpt.check_for_text(doc_path, '.pdf'))

    @skipUnless(ALL_INSTALLED == "True", 'Installation is ready')
    def test_doc_to_text(self):
        """
        Check if document text is properly extracted, when possible
        """
        doc = dpt.doc_to_text(LOCAL_PATH + '/fixtures/record_text.pdf')

        self.assertTrue(
            'Cupcake ipsum dolor sit' in doc.stdout.read().decode('utf-8'))
        doc = dpt.doc_to_text(LOCAL_PATH + '/fixtures/excel_spreadsheet.xlsx')
        self.assertTrue(
            'in a list of numbers' in doc.stdout.read().decode('utf-8'))

        doc = dpt.doc_to_text(LOCAL_PATH + '/fixtures/record_no_text.pdf')
        self.assertTrue('' in doc.stdout.read().decode('utf-8'))

    @skipUnless(ALL_INSTALLED == "True", 'Installation is ready')
    def test_pdf_to_img_and_img_to_text(self):
        """
        Check if pdf docs can be converted to images and then to text
        """
        dpt.pdf_to_img(LOCAL_PATH + '/fixtures/record_no_text.pdf')
        dpt.img_to_text(LOCAL_PATH + '/fixtures/record_no_text.tiff')
        self.assertTrue(
            os.path.isfile(LOCAL_PATH + '/fixtures/record_no_text.txt'))
        # Currently, this isn't working with the example pdf

    @skipUnless(ALL_INSTALLED == "True", 'Installation is ready')
    def test_extract_metadata(self):
        """
        Check if meta data is properly created
        """

        dpt.extract_metadata(
            LOCAL_PATH + '/fixtures/record_text.pdf', '.pdf')
        self.assertTrue(
            os.path.isfile(LOCAL_PATH + '/fixtures/record_text_metadata.json'))

        dpt.extract_metadata(
            LOCAL_PATH + '/fixtures/excel_spreadsheet.xlsx', '.xlsx')
        self.assertTrue(os.path.isfile(
            LOCAL_PATH + '/fixtures/excel_spreadsheet_metadata.json'))

    @skipUnless(ALL_INSTALLED == "True", 'Installation is ready')
    def test_process_documents_run_one(self):
        """
        Check if PDFTextExtractor correctly extracts text from PDF document and
        skip_converted parameter correctly skips documents that have
        been converted
        """
        # Test first run
        dir_path = "/fixtures/*.pdf"
        glob_path = LOCAL_PATH + dir_path
        dpt.PDFTextExtractor(glob_path, skip_converted=False)

        files = [
            'record_text',
            'record_no_text',
        ]
        extensions = ['_metadata.json', '.txt']
        for item_path in file_itterator(files, extensions):
            self.assertTrue(os.path.isfile(item_path))

        # File with text does not undergo transformation
        self.assertFalse(
            os.path.isfile(LOCAL_PATH + '/fixtures/record_text.tiff'))
        self.assertTrue(
            os.path.isfile(LOCAL_PATH + '/fixtures/record_no_text.tiff'))

        # Save creation times
        text_time = os.path.getmtime(
            LOCAL_PATH + '/fixtures/record_text.txt')
        no_text_time = os.path.getmtime(
            LOCAL_PATH + '/fixtures/record_no_text.txt')

        # Check if new files were created when skip converted is True
        dpt.PDFTextExtractor(glob_path, skip_converted=True)
        text_time_2 = os.path.getmtime(
            LOCAL_PATH + '/fixtures/record_text.txt')
        no_text_time_2 = os.path.getmtime(
            LOCAL_PATH + '/fixtures/record_no_text.txt')

        self.assertEqual(text_time, text_time_2)
        self.assertEqual(no_text_time, no_text_time_2)

        # Check if new files are created when skip converted is False
        dpt.PDFTextExtractor(glob_path, skip_converted=False)
        text_time_2 = os.path.getmtime(
            LOCAL_PATH + '/fixtures/record_text.txt')
        no_text_time_2 = os.path.getmtime(
            LOCAL_PATH + '/fixtures/record_no_text.txt')

        self.assertNotEqual(text_time, text_time_2)
        self.assertNotEqual(no_text_time, no_text_time_2)

    @skipUnless(ALL_INSTALLED == "True", 'Installation is ready')
    def test_process_documents(self):
        """
        Check that the DocTextExtractor function extract documents properly and
        skip_converted parameter correctly skips documents that have
        been converted
        """

        # Test first run
        dpt.DocTextExtractor(LOCAL_PATH + "/fixtures/*.xlsx")
        self.assertTrue(
            os.path.isfile(LOCAL_PATH + '/fixtures/excel_spreadsheet.txt'))
        self.assertTrue(os.path.isfile(
            LOCAL_PATH + '/fixtures/excel_spreadsheet_metadata.json'))
        with open(LOCAL_PATH + '/fixtures/excel_spreadsheet.txt', 'r') as f:
            data = f.read()
        self.assertTrue('Adds the cells' in data)

        # Save time
        stats_1 = os.path.getmtime(
            LOCAL_PATH + '/fixtures/excel_spreadsheet.txt')

        time.sleep(3)
        # Test second run
        dpt.DocTextExtractor(
            LOCAL_PATH + "/fixtures/*.xlsx", skip_converted=False)
        stats_2 = os.path.getmtime(
            LOCAL_PATH + '/fixtures/excel_spreadsheet.txt')
        self.assertNotEqual(stats_1, stats_2)

        # Test thrid run
        dpt.DocTextExtractor(
            LOCAL_PATH + "/fixtures/*.xlsx", skip_converted=True)
        stats_3 = os.path.getmtime(
            LOCAL_PATH + '/fixtures/excel_spreadsheet.txt')
        self.assertEqual(stats_2, stats_3)


if __name__ == '__main__':
    main()
