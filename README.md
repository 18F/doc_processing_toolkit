### Document Processing Toolkit

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

