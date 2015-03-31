## About
This example script uses celery, which allow multiple instances to
textextractor to run in parallel.

## Running:

### Server for extracting metadata
java -jar tika-app-1.7.jar --server --json --port 8887

### Server for extracting text
java -jar tika-app-1.7.jar --server --text --port 9998

### Redis for caching tasks
redis-server

### Celery workers for distributing tasks
celery -A sample_celery_tasks worker --loglevel=INFO  -n worker1.%h
celery -A sample_celery_tasks worker --loglevel=INFO  -n worker2.%h
celery -A sample_celery_tasks worker --loglevel=INFO  -n worker3.%h
etc...

### Running script
python sample_convert_docs.py
