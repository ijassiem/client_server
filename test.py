msg = 'hello'
msgb = 'hello'
K = 10
print msg
msg = '{0: <10}'.format(len(msg)) + msg
msgb = str(len(msgb)).ljust(K) + msgb
print msg
print msgb
header = msg[0:10]
print header
print type(header)
#header_value = int(header)
#print header_value
#print type(header_value)