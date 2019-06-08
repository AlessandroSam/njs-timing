import http.client
import time
import sys
import socket

SERVER_ADDR = "localhost"
SERVER_PORT = 8080
APP_URL = "/ACTiming2/live"
SEND_INTERVAL = 1

def postLogMessage(msg):
    print(msg)

def doHttpPost(json):
    header = "POST /ACTiming2/live HTTP/1.1\r\nHost: {}:{}\r\nAccept-Encoding: identity\r\nContent-Length: {}\r\nContent-type: application/json\r\n\r\n".format(SERVER_ADDR, str(SERVER_PORT), str(len(json)))
    #    postLogMessage(header)
    message = header + json
    size = len(message)
    totalsent = 0
    httpconn = socket.socket()
    httpconn.connect((SERVER_ADDR, SERVER_PORT))
    try:
        while totalsent < size:
            sent = httpconn.send(bytes(message[totalsent:], 'UTF-8'))
            if sent == 0:
                raise RuntimeException("cannot post data to server")
            totalsent = totalsent + sent
    except Exception as e:
        postLogMessage("Cannot post data to server: " + repr(e))
    finally:
        httpconn.close()

if __name__ == "__main__":
    filename = 'leaderboard.json'
    if len(sys.argv) == 2:
        filename = sys.argv[1]
    print('Using JSON file ' + filename)
    fo = None
    fo = open(filename, 'r')
    for jsonstr in fo:
        conn = None
        try:
            doHttpPost(jsonstr)
#            conn = http.client.HTTPConnection(SERVER_ADDR, SERVER_PORT)
#            conn.request("POST", APP_URL, jsonstr, {"Content-type": "application/json"})
#            resp = conn.getresponse()
#            if resp.status != http.client.OK:
#                postLogMessage("Web server returned error: " + str(resp.status) + " " + resp.reason)
        except Exception as e:
            postLogMessage("Unable to post data to web server:" + repr(e))
        finally:
            pass
#            conn.close()
        time.sleep(SEND_INTERVAL)
    fo.close()    
