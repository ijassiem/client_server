import socket
import mylogger

#logging setup
logger = mylogger.init_logging(name='server1', loglevel=mylogger.DEBUG)

s = socket.socket()  # create socket object
logger.debug('Socket created.')

try:
    PORT = 1234
    s.bind(('0.0.0.0', PORT))  # Binding to '0.0.0.0' or '' allows connections from any IP address that can route to it.
    logger.debug('Socket binded to port %s.', PORT)
    s.listen(5)
    logger.debug('Socket is listening.')
    c, address = s.accept()
    logger.debug('Connection from %s.', address)
    c.send('Thank you for connecting.')
    logger.debug('Message sent to client.')
    while True:
        line = s.recv(8195)
    #     print(line)
    #     c.send(line)
        if line == 'q':
            break
    c.close()
    logger.debug('Connection closed.')
finally:
    s.close()
    logger.debug('Socket closed.')
