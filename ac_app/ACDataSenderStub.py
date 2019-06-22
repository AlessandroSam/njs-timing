try:
    import socket
except ImportError as e:
    postLogMessage("Cannot import socket")
import threading
import sys
import queue
import time

data = ""
SERVER_ADDR = "localhost"
SERVER_PORT = 8080
APP_URL = "/ACTiming2/live"
SEND_INTERVAL = 1  # интервал передачи в секундах, в общем случае должен совпадать с интервалом отдачи данных в корсовском приложении
DEFAULT_FILENAME = 'C:\\Data\\njs-timing\\ac_app\\leaderboard.json' # vscode, wtf?


def postLogMessage(message):
    print(message);

class HTTPPostThread(threading.Thread):
    """
    Реализует отправку HTTP POST запросов в отдельном потоке, не блокируя игру.
    """
    def __init__(self):
        super().__init__()
        self.data = ""
        self.queue = queue.Queue()
        self.stop = False
        self.isRunning = False

    def put(self, packet):
        self.queue.put(packet)

    def start(self):
        # postLogMessage("HTTP sender thread started")
        if (self.isRunning):
            return
        self.isRunning = True
        return super().start()

    def is_running(self):
        return self.isRunning

    def run(self):
        httpconn = None
        # Модуль http отказывается работать в AC по неясным причинам. Пошлём POST руками.
        # Да, здесь не AC. Это копипаста.
        try:
            httpconn = socket.socket()
            # postLogMessage("Socket created")
            httpconn.connect((SERVER_ADDR, SERVER_PORT))
            # postLogMessage("Connected to web server")
            # postLogMessage("Data:" + self.data)
            packetsSent = 0
            while True:
                try:
                    data = self.queue.get()
                    httpconn.sendall(bytes(data[:], 'UTF-8'))
                    packetsSent = packetsSent + 1
                    print("Packets sent: " + str(packetsSent) + " || Queue size: " + str(self.queue.qsize()) + "\t")
                    time.sleep(SEND_INTERVAL);
                    if (self.stop):
                        return
                except queue.Empty:
                    self.isRunning = false
                    return
                except KeyboardInterrupt:
                    return
            # postLogMessage("Send OK")
        except Exception as e:
            postLogMessage("Cannot post data to server" + repr(e))
        finally:
            httpconn.close()


if __name__ == '__main__':
    filename = DEFAULT_FILENAME
    if (len(sys.argv) == 2):
        filename = sys.argv[1]
        print("Using file " + filename)
    else:
        print("No input file specified, using " + DEFAULT_FILENAME + " by default.")
    infile = open(filename, 'r')
    httpThread = HTTPPostThread()
    httpThread.start()
    try:
        for line in infile:
            header = "POST /ACTiming2/live HTTP/1.1\r\nHost: {}:{}\r\nAccept-Encoding: identity\r\nContent-Length: {}\r\nContent-type: application/json\r\n\r\n"\
                .format(SERVER_ADDR, str(SERVER_PORT), str(len(line)))
            # postLogMessage(header)
            message = header + line
            httpThread.put(message)
            # exit by Ctrl+C
        while (httpThread.isRunning):
            continue
    except KeyboardInterrupt: # один фиг не работает, отлаживать влом, не так важно
        httpThread.stop = True
        httpThread.join() 