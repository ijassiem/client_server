import socket
import mylogger
import pickle

HEADERSIZE = 10
IPV4 = socket.AF_INET
TCP = socket.SOCK_STREAM
PORT = 1234
#IPADDRESS = 'dbelab04'
IPADDRESS = 'localhost' # localhost or 127.0.0.1
#logging setup
logger = mylogger.init_logging(name='basic_client', loglevel=mylogger.DEBUG)

s = socket.socket(IPV4, TCP)  # create socket object

s.connect((IPADDRESS, PORT))  # attempt connection to server

while True:
    full_msg = b''
    new_msg = True  # set new_msg flag
    while True:
        msg = s.recv(16)  # buffer size 16 bytes for incoming message
        if new_msg:
            msg_len = int(msg[:HEADERSIZE])  # convert value in HEADER(expected message length) to int
            logger.debug('Expected message length: %s', msg_len)  # print expected message length
            new_msg = False  # clear new_msg flag

        #full_msg += msg.decode("utf-8")
        full_msg += msg  # append messages

        #print(len(full_msg))
        #logger.debug('Full message length: %s', full_msg)  # print full message length

        if len(full_msg)-HEADERSIZE == msg_len:  # execute when complete message is received based on size indicated in HEADER
            logger.debug('Full message received: %s', pickle.loads(full_msg[HEADERSIZE:]))
            new_msg = True # set new_msg flag
            full_msg = b"" # clear/empty message
