import unittest
import doc_process_toolkit as dpt


class TestDocProcessToolkit(unittest.TestCase):

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

        doc_path = "fixtures/record_text.pdf"
        self.assertTrue(dpt.check_for_text(doc_path))

        doc_path = "fixtures/record_no_text.pdf"
        self.assertFalse(dpt.check_for_text(doc_path))

if __name__ == '__main__':
    unittest.main()
