import celery
from textextraction.extractors import textextractor

app = celery.Celery('tasks', broker='redis://localhost:6379/0')


@app.task
def convert_file(doc_path, force_convert):
    """
    Checks if document has been converted and sends file to appropriate
    converter
    """
    textextractor(doc_path=doc_path, force_convert=force_convert)
