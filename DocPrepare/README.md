## PrepareDocs

PrepareDocs.py is script for converting building a document manifest based on metadata extracted from Tika and optionally, metadata that comes with each document.

# Usage Without S3
```python
from PrepareDocs import PrepareDocs

# Define a function for extracting metadata from file provided by foiaonline
def parse_foiaonline_metadata(metadata_file):
    with open((metadata_file), 'r') as f:
        metadata = json.loads(f.read())

    return {
        'title': metadata.get('title'),
        'date_released': metadata.get('released_on'),
        'file_type': metadata.get('file_type', '')}

# Define a function for extracting metadata from file provided by DOS
    def parse_state_metadata(metadata_file):
        with open((metadata_file), 'r') as f:
            metadata = json.loads(f.read())
        date_released = metadata.get('postedDate')
        if date_released:
            date_released = date_released.split('T')[0]
        return {
            'file_type': metadata.get('file_type'),
            'date_created': metadata.get('docDate'),
            'date_released': date_released,
            'title': metadata.get('subject')
        }

# Run the scripts
PrepareDocs(
    'department-of-state',
    unique_parser=parse_state_metadata).prepare()
PrepareDocs(
    'environmental-protection-agency',
    unique_parser=parse_foiaonline_metadata).prepare()

```

# Usage With S3

```bash
export AWS_ACCESS_KEY_ID=<<Your AWS Access Key ID>>
export AWS_SECRET_ACCESS_KEY=<<Your AWS Secret Access Key>>
```

```python
...(defining custom metadata parser)

# Set the s3 bucket
s3_bucket_name = "<<s3 bucket name>>"

# Run the scripts
PrepareDocs(
    'department-of-state',
    unique_parser=parse_state_metadata,
    s3_bucket_name=s3_bucket_name).prepare()
PrepareDocs(
    'environmental-protection-agency',
    unique_parser=parse_foiaonline_metadata,
    s3_bucket_name=s3_bucket_name).prepare()

```
