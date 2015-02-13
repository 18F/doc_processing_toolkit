import unittest
import doc_process_toolkit as dpt


class TestDocProcessToolkit(unittest.TestCase):

    def test_get_doc_length(self):
        """
        Tests to ensure that doc length function only captures words with
        over 3 chars
        """

        text = "word words more words"
        self.assertEqual(dpt.get_doc_length(text), 4)

        text = "12323 word w a9s90s"
        self.assertEqual(dpt.get_doc_length(text), 1)


if __name__ == '__main__':
    unittest.main()
