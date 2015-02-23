### Document Processing Toolkit

[![Coverage Status](https://coveralls.io/repos/18F/doc_processing_toolkit/badge.png)](https://coveralls.io/r/18F/doc_processing_toolkit)

##### About
Python library to extract text from PDF, and default to OCR when text extraction fails.

##### Dependencies
- [Apache Tika](http://tika.apache.org/)
- [Ghostscript](http://www.ghostscript.com/)
- [Tesseract](https://code.google.com/p/tesseract-ocr/)

##### Installation
1. Download tika-app-1.7.jar from [Apache Tika](http://tika.apache.org/)
2. Mac: `brew install ghostscripts` Ubuntu: `sudo apt-get install ghostscript`
3. `brew install tesseract` Ubuntu: `sudo apt-get install tesseract-ocr`

##### Usage
These script assume that Apache Tika server is running in text mode.
Start Tika Server
`java -jar tika-app-1.7.jar --server --text --port 9998`

In Python script
```python
import doc_process_toolkit
# To convert all pdfs
doc_process_toolkit.process_documents("<<Document directory>>")
# To convert only pdfs that don't have a text file
doc_process_toolkit.process_documents("<<Document directory>>", skip_finished=True)
```
