import socket
import mylogger

#logging setup
logger = mylogger.init_logging(name='server1', loglevel=mylogger.DEBUG)

s = socket.socket()  # create socket object
logger.debug('Socket created.')

#IPADDRESS = 'dbelab04'
IPADDRESS = 'localhost'
PORT = 1234

s.connect((IPADDRESS, PORT))


# close the connection
while True:
    # receive data from the server
    line = s.recv(1024)
    print 'Received msg:', line
    x = raw_input('Enter q to quit or r to refresh:\n')
    if x == 'q':
        logger.debug('Exiting loop.')
        break
    elif x == 'r':
        s.send('r')
        logger.debug('Sending refresh.')

s.close()
logger.debug('Socket closed.')