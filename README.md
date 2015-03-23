### Document Processing Toolkit

[![Coverage Status](https://coveralls.io/repos/18F/doc_processing_toolkit/badge.png)](https://coveralls.io/r/18F/doc_processing_toolkit)

##### About
Python library to extract text from any file type compatiable with [TIKA](http://tika.apache.org/). It defaults to OCR when text extraction of a PDF file fails.

##### Dependencies
- [Apache Tika](http://tika.apache.org/)
- [Ghostscript](http://www.ghostscript.com/)
- [Tesseract](https://code.google.com/p/tesseract-ocr/)
- [Xpdf](http://www.foolabs.com/xpdf/)

##### Installation
1. Download tika-app-1.7.jar from [Apache Tika](http://tika.apache.org/)
2. Mac: `brew install ghostscripts` Ubuntu: `sudo apt-get install ghostscript`
3. Mac: `brew install tesseract` Ubuntu: `sudo apt-get install tesseract-ocr`
4. Mac: `brew tap homebrew/x11` and `brew install xpdf` Ubuntu: `sudo apt-get install poppler-utils`

##### Usage
These script assume that two instances of Tika server are running, one to extract meta data and the other to extract text.
Starting Tika Servers
`java -jar tika-app-1.7.jar --server --text --port 9998`
`java -jar tika-app-1.7.jar --server --json --port 8887`

In Python script
```python
from textextraction.threader import AsyncConvert
AsyncConvert.extractor_factory(file_iterator=iglob("test_docs/*/*.pdf"))
```

##### Tests
In order to run tests:
1. All requirements must be installed
2. Both Tika servers need to be running
3. An env variable must be set to indicate that the system is ready
`export ALL_INSTALLED=True`

Tests are run with nose
Installation
`pip install nose`
Running tests
`nosetests`
