from boto.s3.connection import S3Connection
from boto.s3.key import Key
import os
import json
import yaml


class PrepareDocs:

    def __init__(self, agency_directory, custom_parser=None, s3_bucket=None):
        """
        agency_directory: directory of a specific office or agency
        custom_parser: optional parser function for document metadata
        not extracted with Tika
        """
        self.agency_directory = agency_directory
        self.custom_parser = custom_parser

        if s3_bucket:
            self.s3_bucket = S3Connection().get_bucket(s3_bucket)
        else:
            self.s3_bucket = None

    def parse_date(self, date):
        """ Given string in ISO 8601 format like this: 2013-03-20T17:11:17Z
        returns date in format YYYY-MM-DD"""

        if date:
            return date.split('T')[0]

    def clean_tika_file_type(self, file_type):
        """ Cleans file_type to attempt to get usable extension """

        if type(file_type) == list:
            file_type = file_type[0]

        return file_type.replace('application/', '').split(';')[0].strip()

    def open_metadata_file(self, metadata_file):
        """ Opens a meta data file and converts to a dict """

        with open(metadata_file, 'r') as f:
            try:
                tika_metadata = json.loads(f.read())
            except:
                tika_metadata = {}
        return tika_metadata

    def parse_tika_metadata(self, metadata_file):
        """ Parses metadata created by Tika and returns a dictionary
         containing file_type, date_released, title, pages, and date_created
        """

        metadata = {}
        tika_metadata = self.open_metadata_file(metadata_file)
        metadata['file_type'] = self.clean_tika_file_type(
            tika_metadata.get('dc:format', ''))
        metadata['date_released'] = self.parse_date(
            tika_metadata.get('Last-Save-Date'))
        metadata['title'] = tika_metadata.get('title')
        metadata['pages'] = tika_metadata.get('xmpTPg:NPages')
        metadata['date_created'] = self.parse_date(
            tika_metadata.get('meta:creation-date'))

        return metadata

    def prep_metadata(self, root, base_file):
        """ Prepares metadata from Tika metadata file and applies a unique
        parser to the data if available """

        metadata = self.parse_tika_metadata(
            metadata_file=os.path.join(root, base_file + "_metadata.json"))
        if self.custom_parser:
            metadata = self.custom_parser(
                metadata_file=os.path.join(root, base_file + ".json"),
                tika_metadata=metadata
            )
        return metadata

    def upload_file_to_s3(self, rel_file_loc, upload_file_loc):
        """ Uploads individual document to s3 """

        k = Key(self.s3_bucket)
        k.key = upload_file_loc
        k.set_contents_from_filename(rel_file_loc, replace=True)

    def upload_doc_to_s3(self, rel_doc_root, upload_doc_loc, doc_ext):
        """ Uploads an individual document and text file to s3 """

        text_location = rel_doc_root + '.txt'

        if os.path.exists(text_location):
            # Upload text
            self.upload_file_to_s3(
                rel_file_loc=text_location,
                upload_file_loc=upload_doc_loc + '.txt')
            # Upload file
            self.upload_file_to_s3(
                rel_file_loc=rel_doc_root + doc_ext,
                upload_file_loc=upload_doc_loc + doc_ext)

    def upload_folder_to_s3(self, manifest, directory_path):
        """ Uploads manifest to s3 and then iterates over documents in the
        manifest and uploads each to s3 """

        upload_dir = os.path.join(
            os.path.split(self.agency_directory)[-1],
            os.path.split(directory_path)[-1])

        # Upload manifest
        self.upload_file_to_s3(
            rel_file_loc=os.path.join(directory_path, 'manifest.yaml'),
            upload_file_loc=os.path.join(upload_dir, 'manifest.yaml'))

        # Upload documents
        for metadata in manifest:
            doc_root, doc_ext = os.path.splitext(metadata.get('doc_location'))
            rel_doc_root = os.path.join(directory_path, doc_root)
            self.upload_doc_to_s3(
                rel_doc_root=rel_doc_root,
                upload_doc_loc=os.path.join(upload_dir, doc_root),
                doc_ext=doc_ext)

    def prepare_file_location(self, metadata, root, base_file):
        """ Adds file location to metadata so that manifest can correctly
        display it """

        f_dir = os.path.split(root)[-1]
        doc_location = os.path.join(
            f_dir, base_file + "." + metadata['file_type'])
        metadata['doc_location'] = doc_location

    def write_manifest(self, manifest, directory_path):
        """ Writes manifest files """

        with open(os.path.join(directory_path, "manifest.yaml"), 'w') as f:
            f.write(yaml.dump(
                manifest,
                default_flow_style=False, allow_unicode=True))

    def create_manifest(self, directory_path):
        """ Generates a document manifest for a specific folder """

        manifest = []
        for root, dirs, files in os.walk(directory_path):
            metadata_files = filter(lambda f: '_metadata.json' in f, files)
            for metadata_file in metadata_files:
                base_file = metadata_file.replace('_metadata.json', '')
                metadata = self.prep_metadata(root=root, base_file=base_file)
                self.prepare_file_location(metadata, root, base_file)
                manifest.append(metadata)

        self.write_manifest(manifest=manifest, directory_path=directory_path)
        if self.s3_bucket:
            self.upload_folder_to_s3(
                manifest=manifest, directory_path=directory_path)

    def prepare_documents(self):
        """ Looks for time-stamped directories inside an agency directory and
        generates manifest files"""

        directory_files = os.listdir(self.agency_directory)
        for item in directory_files:
            if item.isdigit():
                self.create_manifest(
                    directory_path=os.path.join(self.agency_directory, item)
                )
