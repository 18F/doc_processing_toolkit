from boto.s3.connection import S3Connection
from boto.s3.key import Key
import os
import json
import yaml


class PrepareDocs:

    def __init__(self, agency_directory, unique_parser=None,
                 s3_bucket_name=None):
        """
        agency_directory: directory of a specific office or agency
        unique_parser: optional parser function for document metadata
        not extracted with Tika
        """
        self.agency_directory = agency_directory
        self.unique_parser = unique_parser

        if s3_bucket_name:
            self.s3_bucket = S3Connection().get_bucket(s3_bucket_name)
        else:
            self.s3_bucket = None

    def parse_date(self, date):
        """ Given string like this: 2013-03-20T17:11:17Z returns date in
        format YYYY-MM-DD"""

        if date:
            return date.split('T')[0]

    def parse_tika_metadata(self, metadata_file, metadata):
        """ Parses metadata from created by Tika """

        with open(os.path.join(metadata_file), 'r') as f:
            try:
                tika_metadata = json.loads(f.read())
            except:
                tika_metadata = {}

            if not metadata.get('file_type'):
                metadata['file_type'] = tika_metadata.get(
                    ['dc:format'], '').replace('application/', '')
            if not metadata.get('date_released'):
                metadata['date_released'] = self.parse_date(
                    tika_metadata.get('Last-Save-Date'))
            if not metadata.get('title'):
                metadata['title'] = tika_metadata.get('title')

            metadata['pages'] = tika_metadata.get('xmpTPg:NPages')
            metadata['date_created'] = self.parse_date(
                tika_metadata.get('meta:creation-date'))

            return metadata

    def prepare_metadata(self, root, base_file):
        """ Prepares metadata from Tika metadata file, the file location,
        and unique parser if available """

        if self.unique_parser:
            metadata = self.unique_parser(
                os.path.join(root, base_file + ".json"))
        else:
            metadata = {}

        metadata = self.parse_tika_metadata(
            os.path.join(root, base_file + "_metadata.json"),
            metadata=metadata)

        return metadata

    def prepare_file_location(self, metadata, root, base_file):
        """ Adds file location to metadata """

        if self.s3_bucket:

            # Upload pdf
            doc_location = os.path.join(
                root, base_file + "." + metadata['file_type'])

            k = Key(self.s3_bucket)
            k.key = doc_location
            k.set_contents_from_filename(doc_location, replace=True)

            # Upload text
            text_location = os.path.join(root, base_file + ".txt")
            if os.path.exists(text_location):
                k = Key(self.s3_bucket)
                k.key = text_location
                k.set_contents_from_filename(text_location, replace=True)

        else:
            f_dir = os.path.split(root)[-1]
            doc_location = os.path.join(
                f_dir, base_file + "." + metadata['file_type'])
            metadata['doc_location'] = doc_location

    def write_manifest(self, manifest, directory_path):
        """ Writes manifest files """

        manifest_location = os.path.join(directory_path, "manifest.yaml")

        if self.s3_bucket:
            k = Key(self.s3_bucket)
            k.key = manifest_location
            k.set_contents_from_filename(manifest_location, replace=True)
        else:
            with open(manifest_location, 'w') as f:
                f.write(yaml.dump(
                    manifest, default_flow_style=False, allow_unicode=True))

    def create_manifest(self, directory_path):
        """ Generates a file manifest for a specific time stamped folder """

        manifest = []
        for root, dirs, files in os.walk(directory_path):
            for item in files:
                if "_metadata.json" in item:
                    base_file = item.replace('_metadata.json', '')
                    metadata = self.prepare_metadata(
                        root=root, base_file=base_file
                    )
                    self.prepare_file_location(metadata, root, base_file)
                    if metadata.get('file_type') != 'mystery':
                        manifest.append(metadata)
        self.write_manifest(manifest=manifest, directory_path=directory_path)

    def prepare(self):
        """ Look for time stamped directories inside an agency directory to
        generate manifest """

        directory_files = os.listdir(self.agency_directory)
        for item in directory_files:
            if item.isdigit():
                self.create_manifest(
                    directory_path=os.path.join(self.agency_directory, item)
                )
