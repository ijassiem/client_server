import socket
import mylogger

logger = mylogger.init_logging(name='server1', loglevel=mylogger.DEBUG)

s = socket.socket()  # create socket object
logger.debug('Socket created.')

try:
    port = 1234
    s.bind(('0.0.0.0', port))  # Binding to '0.0.0.0' or '' allows connections from any IP address that can route to it.
    logger.debug('Socket binded to %s.', port)
    s.listen(5)
    logger.debug('Socket is listening.')
    c, address = s.accept()
    logger.debug('Connection from %s.', address)
    c.send('Thank you for connecting.')
    logger.debug('Message sent to client.')
    c.close()
    logger.debug('Connection closed.')
finally:
    s.close()
    logger.debug('Socket closed.')
