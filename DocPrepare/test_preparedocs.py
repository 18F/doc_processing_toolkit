from unittest import TestCase, main

import os
import boto
import moto
import json
import PrepareDocs

LOCAL_PATH = os.path.dirname(os.path.realpath(__file__))

expected_metadata = {
    'file_type': 'pdf',
    'date_created': '2014-04-15',
    'pages': '79',
    'title': None,
    'date_released': '2015-01-21'
}


def parse_foiaonline_metadata(metadata_file, tika_metadata):
    """ This is a custom metadata parser that extracts metadata from
    files, which come with the records. A user can choose to either
    overwrite the Tika metadata or keep it."""

    with open((metadata_file), 'r') as f:
        metadata = json.loads(f.read())
    tika_metadata['title'] = metadata.get('title')
    tika_metadata['date_released'] = metadata.get('released_on')
    tika_metadata['file_type'] = metadata.get('file_type')
    return tika_metadata


class TestPrepareDocs(TestCase):

    @classmethod
    def setUpClass(cls):
        cls._connection = PrepareDocs.PrepareDocs(os.path.join(
            LOCAL_PATH,
            'fixtures/national-archives-and-records-administration')
        )

    def test_parse_date(self):
        """ Verify that dates are parsed correctly from ISO 8601 format"""

        clean_date = self._connection.parse_date('2013-03-20T17:11:17Z')
        self.assertEqual(clean_date, '2013-03-20')

    def test_clean_tika_file_type(self):
        """ Verify that file type is cleaned from tika metadata """

        cleaned_data = self._connection.clean_tika_file_type(
            'application/pdf; version\1.6')
        self.assertEqual(cleaned_data, 'pdf')

    def test_parse_tika_metadata(self):
        """ Test that tika metadata are extracted correctly """

        # Given no previous data
        metadata_file_loc = 'fixtures/national-archives-and-records-'
        metadata_file_loc += 'administration/20150331/090004d2805baaa4/'
        metadata_file_loc += 'record_metadata.json'
        metadata_file_loc = os.path.join(LOCAL_PATH, metadata_file_loc)

        metadata = self._connection.parse_tika_metadata(
            metadata_file=metadata_file_loc)
        self.assertEqual(expected_metadata, metadata)

    def test_prep_metadata(self):
        """ Verify that data are extracted without custom parser
        and data are correctly merged with custom parser """

        # Without custom parser
        root = os.path.join(LOCAL_PATH, 'fixtures/national-archives')
        root += '-and-records-administration/20150331/090004d2805baaa4'
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

    def test_write_manifest(self):
        """ Checks to make sure manifest is written """

        directory_path = os.path.join(LOCAL_PATH, 'fixtures')
        print(directory_path)
        self._connection.write_manifest(
            manifest={'test': 'test'},
            directory_path=directory_path)
        manifest_file = directory_path + '/manifest.yaml'
        with open(manifest_file, 'r') as f:
            manifest = f.read()
        self.assertEqual(manifest, 'test: test\n')
        os.remove(manifest_file)

    def test_prepare_documents(self):
        """ Check to ensure document metadata is collected from all documents
        in the target folder and manifest contains the correct data """

        self._connection.custom_parser = parse_foiaonline_metadata
        self._connection.prepare_documents()
        manifest_file = os.path.join(
            self._connection.agency_directory, '20150331', 'manifest.yaml')
        with open(manifest_file, 'r') as f:
            manifest = f.read()
        self.assertTrue('090004d280039e4a' in manifest)
        self.assertTrue('090004d2804eb1ab' in manifest)
        self.assertTrue('090004d2805baaa4' in manifest)
        os.remove(manifest_file)


class TestPrepareDocsWithS3(TestCase):

    @classmethod
    def setUpClass(cls):
        cls._connection = PrepareDocs.PrepareDocs(os.path.join(
            LOCAL_PATH,
            'fixtures/national-archives-and-records-administration')
        )
        cls._connection.custom_parser = parse_foiaonline_metadata

    @moto.mock_s3
    def test_upload_one_file_to_s3(self):
        """ Verify that one file can be uploaded to correct s3 bucket
        and location """

        # Upload file
        metadata_file_loc = 'fixtures/national-archives-and-records-'
        metadata_file_loc += 'administration/20150331/090004d2805baaa4/'
        metadata_file_loc += 'record_metadata.json'

        # Open mock connection
        conn = boto.connect_s3()
        conn.create_bucket('testbucket')
        self._connection.s3_bucket = conn.get_bucket('testbucket')

        # Mock upload and check
        self._connection.upload_file_to_s3(
            rel_file_loc=metadata_file_loc, upload_file_loc='test.json')
        returned_file = conn.get_bucket('testbucket').get_key('test.json').\
            get_contents_as_string()
        self.assertTrue(returned_file.startswith(b'{"Content-Type"'))

    @moto.mock_s3
    def test_upload_all_files_to_s3(self):
        """ Verify that manifest and relevant files are uploaded to s3 a
        bucket """

        # Open mock connection
        conn = boto.connect_s3()
        conn.create_bucket('testbucket')
        self._connection.s3_bucket = conn.get_bucket('testbucket')

        # Upload folder and check
        self._connection.prepare_documents()
        for i, key in enumerate(self._connection.s3_bucket.list()):
            self.assertTrue('20150331' in key.name)
        self.assertEqual(i, 6)

        # Check if manifest is present
        manifest_name = 'national-archives-and-records-administration/'
        manifest_name += '20150331/manifest.yaml'
        returned_file = conn.get_bucket('testbucket').get_key(manifest_name)
        self.assertEqual(returned_file.name, manifest_name)

        manifest_file = os.path.join(
            self._connection.agency_directory, '20150331', 'manifest.yaml')
        os.remove(manifest_file)

if __name__ == '__main__':
    main()
