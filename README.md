### Document Processing Toolkit

[![Coverage Status](https://coveralls.io/repos/18F/doc_processing_toolkit/badge.png)](https://coveralls.io/r/18F/doc_processing_toolkit)

##### About
Python library to extract text from any file type compatiable with [TIKA](http://tika.apache.org/). It defaults to OCR when text extraction of a PDF file fails.

##### Dependencies
- [Apache Tika](http://tika.apache.org/)
- [Ghostscript](http://www.ghostscript.com/)
- [Tesseract](https://code.google.com/p/tesseract-ocr/)

##### Installation
1. Download tika-app-1.7.jar from [Apache Tika](http://tika.apache.org/)
2. Mac: `brew install ghostscripts` Ubuntu: `sudo apt-get install ghostscript`
3. `brew install tesseract` Ubuntu: `sudo apt-get install tesseract-ocr`

##### Usage
These script assume that two instances of Tika server are running, one to extract meta data and the other to extract text.
Starting Tika Servers
`java -jar tika-app-1.7.jar --server --json --port 9998`
`java -jar tika-app-1.7.jar --server --text --port 8887`

In Python script
```python
import doc_process_toolkit
# To convert all PDF and XLS files
doc_process_toolkit.process_documents(["glob path/*.pdf", "glob path/*.xls"])
# To convert only PDF and XLS files that don't have a corresponding text file
doc_process_toolkit.process_documents(
    ["glob path/*.pdf", "glob path/*.xls"], skip_converted=True)
```
