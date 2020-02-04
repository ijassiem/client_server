import socket
import mylogger
import pickle
import platform
import time

HEADERSIZE = 10

#CONSTANTS
IPV4 = socket.AF_INET
TCP = socket.SOCK_STREAM
PORT = 1234


#pickle msg
#d= platform.uname()  # returns tuple of machine information
#msg = pickle.dumps(d)  # pickles tuple

#logging setup
logger = mylogger.init_logging(name='basic_server', loglevel=mylogger.DEBUG)

s = socket.socket(IPV4, TCP)  # create socket object
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # allows reuse of address and port

s.bind(('0.0.0.0', PORT))  # Binding to '0.0.0.0' or '' allows connections from any IP address:
s.listen(5)  # queue of 5
logger.debug('Socket is listening.')

while True:
    clientsocket, address = s.accept()  # accept connection from client
    logger.debug('Connection accepted from %s port %s', address, PORT)

    #msg = "Welcome to the server!"
    d = {1:'hi', 2:'hello', 3:'kunjani'}
    msg = pickle.dumps(d)
    msg = '{0: <10}'.format(len(msg)) + msg #

    clientsocket.send(msg)  # send message
    logger.debug('Message sent: %s', msg)

    while True:
        time.sleep(4)
        #msg = 'This is the data message.'
        d = {
            'Colorado': 'Rockies',
            'Boston': 'Red Sox',
            'Minnesota': 'Twins',
            'Milwaukee': 'Brewers',
            'Seattle': 'Mariners'
        }
        msg = pickle.dumps(d)
        msg = '{0: <10}'.format(len(msg)) + msg  # combine len(msg) and message '25        This is the data message.'

        clientsocket.send(msg)  # send message
        logger.debug('Message sent: %s', msg)


