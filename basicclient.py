import socket
import mylogger
import pickle

IPV4 = socket.AF_INET
TCP = socket.SOCK_STREAM
PORT = 1234
#IPADDRESS = 'dbelab04'
IPADDRESS = 'localhost' # localhost or 127.0.0.1
#logging setup
logger = mylogger.init_logging(name='basic_client', loglevel=mylogger.DEBUG)

s = socket.socket(IPV4, TCP)  # create socket object

try:
    s.connect((IPADDRESS, PORT))  # attempt connection to server
    logger.debug('Connected to server.')
    while True:
        msg = s.recv(1024)  # buffer size 1024 bytes for incoming message
        if not msg: #If conn.recv() returns an empty bytes object, b'', then the client closed the connection and the loop is terminated
            break
        msg_pickle = pickle.loads(msg)  # unpickle message
        print msg_pickle
except socket.error as e:
    print "Socket Error: %s" % e
    logger.debug("Socket Error: %s" % e)
finally:
    s.close()
    logger.debug('Socket closed.')


