import socket
import mylogger
import platform
import sys

def getinfo():
    z = platform.processor() + '. ' + platform.platform()
    return z

#logging setup
logger = mylogger.init_logging(name='server1', loglevel=mylogger.DEBUG)

while True:
    try:
        s = socket.socket()  # create socket object
        logger.debug('Socket created.')
        PORT = 1234
        s.bind(('0.0.0.0', PORT))  # Binding to '0.0.0.0' or '' allows connections from any IP address that can route to it.
        logger.debug('Socket binded to port %s.', PORT)
        s.listen(5)
        logger.debug('Socket is listening.')
        c, address = s.accept()
        logger.debug('Connection accepted from %s.', address)
        #c.send('Connection has been established, thank you.')
        msg = getinfo()
        c.send(msg)
        logger.debug('Message sent to client. "Connection has been established, thank you."')
        c.close()  # Connection closed
        logger.debug('Connection closed.')

    except KeyboardInterrupt:
        sys.exit()
        pass # do cleanup heres

    finally:
        s.close()
        logger.debug('***Socket closed.***')