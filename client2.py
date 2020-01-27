import socket
import mylogger

#IPADDRESS = 'dbelab04'
IPADDRESS = 'localhost'
PORT = 1234

#logging setup
logger = mylogger.init_logging(name='server1', loglevel=mylogger.DEBUG)

while True:
    x = raw_input("Connect to server? 'y' or 'no':\n")
    if x == 'n':
        logger.debug('Exiting.')
        break
    elif x == 'y':
        s = socket.socket()  # create socket object
        logger.debug('Socket created.')
        s.connect((IPADDRESS, PORT))  # connect to server
        line = s.recv(1024)  # receive msg
        print 'Received msg:', line  # print receive msg
        s.close()  # close socket connection
        logger.debug('Socket closed.')