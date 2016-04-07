from distutils.core import setup

readme = open('README.md').read()

with open('requirements.txt') as requirements_file:
    requirements = requirements_file.read().splitlines(False)

setup(
    name="TextExtraction",
    version="0.0",
    packages=['textextraction',],
    description="Extract or OCR text from a PDF document",
    license="Public Domain",
    long_description=readme,
    install_requires=requirements,
)
