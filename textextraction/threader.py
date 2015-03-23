import os
import logging
import threading
from .extractors import PDFTextExtraction, TextExtraction
from time import sleep

"""
This uses threading, which allow multiple instances to textextractor to
run in parallel
"""


class AsyncConvert(threading.Thread):

    def __init__(self, path, instance_id='', force_convert=False):
        threading.Thread.__init__(self)
        self.instance_id = instance_id
        self.doc_path = path
        self.force_convert = force_convert

    def run(self):
        """
        Checks if document has been converted and sends file to appropriate
        converter
        """
        if self.instance_id:
            logging.info("Running instance - %s", self.instance_id)
        root, extension = os.path.splitext(self.doc_path)
        if not os.path.exists(root + ".txt") or self.force_convert:
            if extension == '.pdf':
                extractor = PDFTextExtraction(self.doc_path)
            else:
                extractor = TextExtraction(self.doc_path)
            extractor.extract()

    @classmethod
    def extractor_factory(cls, file_iterator, force_convert=False,
                          use_join=False, max_threads=4):
        """
        Converts files returned by file iterator. `use_join` prevents running
        a new thread until previous thread is terminated
        """

        for file_path in file_iterator:

            task = cls(file_path, force_convert=force_convert)
            task.daemon = True
            task.start()

            time_sleep = 1.0
            while threading.active_count() > max_threads:
                logging.info("Seeping %s seconds", time_sleep)
                sleep(time_sleep)
                time_sleep += 0.1

            if use_join == 0:
                task.join()
