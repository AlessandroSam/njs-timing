try:
    import socket
except ImportError as e:
    postLogMessage("Cannot import socket")

data = ""
SERVER_ADDR = "localhost"
SERVER_PORT = 8080
APP_URL = "/ACTiming2/live"

def postLogMessage(message):
    print(message);

class HTTPPostThread(threading.Thread):
    """
    Реализует отправку HTTP POST запросов в отдельном потоке, не блокируя игру.
    """
    def __init__(self):
        super().__init__()
        self.data = ""
        # self.queue = queue.Queue()
        self.stop = False

    def put(self, packet):
        self.data = packet

    def start(self):
        # postLogMessage("HTTP sender thread started")
        return super().start()

    def run(self):
        httpconn = None
        # Модуль http отказывается работать в AC по неясным причинам. Пошлём POST руками.
        try:
            httpconn = socket.socket()
            # postLogMessage("Socket created")
            httpconn.connect((SERVER_ADDR, SERVER_PORT))
            # postLogMessage("Connected to web server")
            # postLogMessage("Data:" + self.data)
            httpconn.sendall(bytes(self.data[:], 'UTF-8'))
            # postLogMessage("Send OK")
        except Exception as e:
            postLogMessage("Cannot post data to server" + repr(e))
        finally:
            httpconn.close()


if __name__ == '__main__':
    filename = sys.argv[1]
    if filename == '':
        print("No input file specified.")
    else:
        print("Using file " + filename)
        infile = open(filename, 'r')
        
        for (line in infile):
            header = "POST /ACTiming2/live HTTP/1.1\r\nHost: {}:{}\r\nAccept-Encoding: identity\r\nContent-Length: {}\r\nContent-type: application/json\r\n\r\n"\
                .format(SERVER_ADDR, str(SERVER_PORT), str(len(json)))
            # postLogMessage(header)
            message = header + line
            httpThread = HTTPPostThread()
            httpThread.put(message)
            httpThread.start()        # TODO Реализовать через очередь