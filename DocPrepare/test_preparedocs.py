from unittest import TestCase, main

import os
import json
import PrepareDocs

LOCAL_PATH = os.path.dirname(os.path.realpath(__file__))

expected_metadata = {
    'file_type': 'pdf; version=1.6',
    'date_created': '2014-04-15',
    'pages': '79',
    'title': None,
    'date_released': '2015-01-21'
}


def parse_foiaonline_metadata(metadata_file):
    with open((metadata_file), 'r') as f:
        metadata = json.loads(f.read())
    return {
        'title': metadata.get('title'),
        'date_released': metadata.get('released_on'),
        'file_type': metadata.get('file_type', '')}


class TestPrepareDocs(TestCase):

    @classmethod
    def setUpClass(cls):
        cls._connection = PrepareDocs.PrepareDocs(os.path.join(
            LOCAL_PATH,
            'DocPrepare/fixtures/national-archives-and-records-administration')
        )

    def test_parse_date(self):
        """ Verify that dates are parsed correctly from ISO 8601 format"""

        clean_date = self._connection.parse_date('2013-03-20T17:11:17Z')
        self.assertEqual(clean_date, '2013-03-20')

    def test_parse_tika_metadata(self):
        """ Test that tika metadata is extracted correctly """

        # Given no previous data
        metadata_file_loc = 'DocPrepare/fixtures/' + \
            'national-archives-and-records-administration/20150331/' + \
            '090004d2805baaa4/record_metadata.json'
        metadata = self._connection.parse_tika_metadata(
            metadata_file=metadata_file_loc, metadata={})
        self.assertEqual(expected_metadata, metadata)

        # Given data, test that blanks are filled in without overwriting
        del metadata['pages']
        metadata['date_released'] = '2010-01-21'
        new_metadata = self._connection.parse_tika_metadata(
            metadata_file=metadata_file_loc, metadata=metadata)
        self.assertEqual(new_metadata['pages'], '79')
        self.assertEqual(new_metadata['date_released'], '2010-01-21')

    def test_prep_metadata(self):
        """ Verify that data are extracted without custom parser
        and data are correctly merged with custom parser """

        # Without custom parser
        root = 'DocPrepare/fixtures/national-archives-and-records-' + \
            'administration/20150331/090004d2805baaa4'
        base_file = 'record'
        metadata = self._connection.prep_metadata(
            root=root, base_file=base_file)
        self.assertEqual(metadata, expected_metadata)

        # Custom parser, supersedes tika metadata
        self._connection.custom_parser = parse_foiaonline_metadata
        metadata = self._connection.prep_metadata(
            root=root, base_file=base_file)
        self.assertEqual(metadata['date_released'], '2015-02-13')
        self.assertEqual(metadata['file_type'], 'pdf')
        self.assertEqual(metadata['title'], 'FY2006-12')
        self._connection.custom_parser = None

    def test_prepare_file_location(self):
        """ Validate that file location is correctly appended to metadata """

        root = 'DocPrepare/fixtures/national-archives-and-records-' + \
            'administration/20150331/090004d2805baaa4'
        base_file = 'record'
        metadata = {'file_type': 'pdf'}
        self._connection.prepare_file_location(
            metadata=metadata, root=root, base_file=base_file)
        self.assertEqual(
            metadata['doc_location'], '090004d2805baaa4/record.pdf')


if __name__ == '__main__':
    main()
