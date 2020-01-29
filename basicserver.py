import socket
import mylogger
import pickle
import platform
import time

#CONSTANTS
IPV4 = socket.AF_INET
TCP = socket.SOCK_STREAM
PORT = 1234


#pickle msg
d= platform.uname()  # returns tuple of machine information
msg = pickle.dumps(d)  # pickles tuple

#logging setup
logger = mylogger.init_logging(name='basic_server', loglevel=mylogger.DEBUG)

s = socket.socket(IPV4, TCP)  # create socket object
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # allows reuse of address and port
try:
    print 'Server started...\nPress ctrl+c to exit'
    s.bind(('0.0.0.0', PORT))  # Binding to '0.0.0.0' or '' allows connections from any IP address:
    s.listen(5)  # queue of 5
    logger.debug('Socket is listening.')

    clientsocket, address = s.accept()  # accept connection from client
    logger.debug('Connection accepted from %s port %s', address, PORT)
    #clientsocket.send(bytes(msg, "utf-8"))  # send message
    while True:
        clientsocket.send(msg)  # send message
        logger.debug('Message sent to client.')
        time.sleep(2)  #2 sec delay
except socket.error as e:
    print "Socket Error: %s" % e
    logger.debug("Socket Error: %s" % e)
except KeyboardInterrupt as e:
    print("KeyboardInterrupt has been caught.")
    logger.debug("Keyboard Error: %s" % e)
except Exception as e:
    print "Generic error: %s" %e
    logger.debug("Generic Error: %s" % e)
finally:
    s.close()
    logger.debug('Socket closed')
