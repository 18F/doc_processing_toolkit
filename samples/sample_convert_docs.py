import os
import json
import logging
from celery import group
from sample_celery_tasks import convert_file


def extractor_factory(file_iterator, force_convert=False):
    """
    Converts multiple files in parallel using celery
    """

    jobs = group(
        convert_file.s(
            file_path, force_convert) for file_path in file_iterator
    )
    jobs.apply_async()


def file_iterator():
    """ Iterate across files to convert """
    for root, dirs, files in os.walk("."):
        data = {}
        if 'record.json' in files:
            base = 'record.'
            data = json.load(open(os.path.join(root, 'record.json'), 'r'))
        elif 'document.json' in files:
            data = json.load(open(os.path.join(root, 'document.json'), 'r'))
            base = 'document.'
        file_type = data.get('file_type')
        if file_type and file_type != 'zip':
            file_path = os.path.join(root, base + file_type)
            if os.path.exists(file_path):
                yield file_path.replace(" ", "\ ")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    extractor_factory(file_iterator=file_iterator())
