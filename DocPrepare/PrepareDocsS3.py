from PrepareDocs import PrepareDocs
from boto.s3.key import Key

import os
import json
import yaml


class PrepareDocsS3(PrepareDocs):

    def open_metadata_file(self, metadata_file):
        """ Opens a file """

        k = Key(self.s3_bucket)
        k.key = metadata_file
        contents = k.get_contents_as_string()
        try:
            metadata = json.loads(contents.decode())
        except:
            metadata = {}
        return metadata

    def create_manifest(self, directory_path):
        """ Generates a document manifest for a specific folder """

        manifest = []
        for document_dir in self.s3_bucket.list(directory_path, '/'):
            files = list(self.s3_bucket.list(document_dir.name))
            metadata_files = filter(
                lambda f: '_metadata.json' in f.name, files)
            for metadata_file in metadata_files:
                base_file = metadata_file.name.replace('_metadata.json', '')
                metadata = self.prep_metadata(root='', base_file=base_file)
                self.prepare_file_location(
                    metadata, root='', base_file=base_file)
                manifest.append(metadata)

        # Write manifest
        k = Key(self.s3_bucket)
        k.key = os.path.join(directory_path, 'manifest.yaml')
        k.set_contents_from_string(yaml.dump(
            manifest, default_flow_style=False, allow_unicode=True))

    def prepare_documents(self):
        """ Looks for time-stamped directories inside the given s3 bucket"""

        for item in self.s3_bucket.list(self.agency_directory, '/'):
            location = item.name.replace(self.agency_directory, '').strip('/')
            if location.isdigit():
                self.create_manifest(directory_path=item.name)

if __name__ == "__main__":
    preparer = PrepareDocsS3(
        agency_directory='department-of-commerce/',
        s3_bucket="18f-foia-doc-storage")
    preparer.prepare_documents()
