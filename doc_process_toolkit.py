import glob
import time
import re
import subprocess


WORDS = re.compile('[A-Za-z]{3,}')


def check_server(port=9998):
    """ Callback type function to let user know server status """

    pid = get_pid(port=port)
    if pid:
        print("Server running on port {0} with pid of {1}".format(port, pid))
    else:
        print("Server not running on port {}".format(port))


def get_pid(port=9998):
    """ Checks Tika server's PID """

    server_pid = subprocess.Popen(
        args=['lsof -i :%s -t' % port],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=True
    )
    return server_pid.communicate()[0]


def server_setup_timer(port=9998):
    """ Checks for server to start with a loop """

    for i in range(10):
        time.sleep(1)
        if get_pid(port):
            print("Server Started !")
            break
        else:
            print("Waited %s second(s)" % i)


def stat_tika_server(port=9998):
    """ Starts Tika server """

    pid = get_pid(port)
    if pid:
        print("Process already running on port %s" % port)
        return
    subprocess.Popen(
        args=['java -jar tika-app-1.7.jar --server --text --port %s' % port],
        shell=True)
    server_setup_timer(port)


def stop_tika_server(port=9998):
    """ Kills Tika server """

    pid = get_pid(port)
    if pid:
        subprocess.Popen(
            args=['kill -9 %s' % pid],
            stderr=subprocess.STDOUT,
            shell=True)
    else:
        print("Server not running on port %s" % port)


def save_document(document, export_path):
    """ saves the document, maybe add a pip instead of reading with python """

    with open(export_path, 'w') as f:
        f.write(document.stdout.read())


def convert_documents(doc_paths, port=9998):
    """ Converts a document """

    if type(doc_paths) == list:

        for doc_path in doc_paths:
            document = subprocess.Popen(
                args=['nc localhost {0} < {1}'.format(port, doc_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                shell=True)
            yield document, doc_path


def get_doc_length(document):
    """ Return the length of a document -- note piping to wc might be faster"""

    return len(tuple(WORDS.finditer(document)))


if __name__ == '__main__':
    # Testing the script
    stat_tika_server()
    check_server()
    document_paths = glob.glob("test_docs/*/*.pdf")
    documents = convert_documents(document_paths)
    for document, doc_path in documents:
        save_document(document, doc_path.replace(".pdf", ".txt"))
        print("%s converted" % doc_path)

    stop_tika_server()
