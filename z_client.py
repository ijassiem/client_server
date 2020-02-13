import socket
import mylogger
import pickle
import logging

#############################################
import sys, os, re, string, curses
from optparse import OptionParser
import ConfigParser
from multiprocessing.pool import ThreadPool
from collections import defaultdict

desc = """This programs connects to Mellanox switches via SSH and maps connections
              between switches and hosts using LLDP. Switch rates are read and displayed
              in a matrix.
           """
parser = OptionParser(description=desc)
parser.set_usage('%prog [options]')
parser.add_option('-l', dest='loglevel', type=str, default='INFO',
                  help='Log level: DEBUG,INFO,ERROR,WARINING,FATAL. Default = INFO')
parser.add_option('-a', '--maxleaves', type=int, default=36,
                  help='Number of leaf switches in the system.')
parser.add_option('-p', '--maxspines', type=int, default=18,
                  help='Number of spine switches in the system.')
parser.add_option('-n', '--numsw', type=int, default=36,
                  help='Number of switches to process.')
parser.add_option('-t', '--startswitch', type=int, default=1,
                  help='Start displaying from specified switch.')
parser.add_option('-d', '--display', type=str, default='spines',
                  help='Display spines or leaves.')
opts, args = parser.parse_args()

# Setup the logger
loglevel = opts.loglevel
logger = logging.getLogger('mellanox_switch_comms')
level = logging.getLevelName(loglevel)
logger.setLevel(level)
# fmt = '%(asctime)s %(funcName)s:%(lineno)d %(message)s'
fmt = '%(asctime)s %(levelname)s: %(message)s'
date_fmt = '%Y-%m-%d %H:%M:%S'
logging_format = logging.Formatter(fmt, date_fmt)
handler = logging.StreamHandler()
handler.setFormatter(logging_format)
handler.setLevel(level)
logger.addHandler(handler)

port = 22
username = 'monitor'
password = 'monitor'
sudo_password = password  # assume that it is the same password
hosts = []
strsw = opts.startswitch
numsw = opts.numsw
mspines = opts.maxspines
mleaves = opts.maxleaves
if opts.display == 'spines':
    if strsw + numsw > mspines + 1:
        rng = mspines + 1
    else:
        rng = strsw + numsw

    for i in range(strsw, rng):
        hosts.append('cbfsw-s{}.cbf.mkat.karoo.kat.ac.za'.format(i))
else:
    if strsw + numsw > mleaves + 1:
        rng = mleaves + 1
    else:
        rng = strsw + numsw
    for i in range(strsw, rng):
        hosts.append('cbfsw-l{}.cbf.mkat.karoo.kat.ac.za'.format(i))


def ssh_conn(hostname):
    ssh = MySSH(logger)
    ssh.connect(hostname=hostname,
                username=username,
                password=password,
                port=port)
    if ssh.connected() is False:
        logger.error('Connection failed.')
        return hostname
    return ssh


def rem_extra_chars(in_str):
    pat = re.compile('lines \d+-\d+ ')
    in_str = re.sub(pat, '', in_str)
    pat = re.compile('lines \d+-\d+\/\d+ \(END\) ')
    in_str = re.sub(pat, '', in_str)
    return in_str.replace('\r', '')


def run_cmd(ssh_obj, cmd, indata=None, enable=False):
    '''
    Run a command with optional input.

    @param cmd    The command to execute.
    @param indata The input data.
    @returns The command exit status and output.
             Stdout and stderr are combined.
    '''
    prn_cmd = cmd
    cmd = 'terminal type dumb\n' + cmd
    if enable:
        cmd = 'enable\n' + cmd

    output = ''
    output += ('\n' + '=' * 64 + '\n')
    output += ('host    : ' + ssh_obj.hostname + '\n')
    output += ('command : ' + prn_cmd + '\n')
    status, outp = ssh_obj.run(cmd, indata, timeout=10)
    output += ('status  : %d' % (status) + '\n')
    output += ('output  : %d bytes' % (len(output)) + '\n')
    output += ('=' * 64 + '\n')
    outp = rem_extra_chars(outp)
    output += outp
    return output


def run_threaded_cmd(ssh_list, cmd, enable=False):
    '''
    Run threaded command on all clients in ssh_list
    '''
    thread_obj = [0] * len(ssh_list)
    pool = ThreadPool(processes=len(ssh_list))
    output = []
    for i, ssh_obj in enumerate(ssh_list):
        thread_obj[i] = pool.apply_async(run_cmd, args=(ssh_obj, cmd), kwds={'enable': enable})
    for i, ssh_obj in enumerate(ssh_list):
        output.append(thread_obj[i].get())
    pool.close()
    pool.join()
    return [x.split('\n') for x in output]


def close_ssh(ssh_list):
    thread_obj = [0] * len(ssh_list)
    pool = ThreadPool(processes=len(ssh_list))
    logger.info('Closing SSH connections')
    for i, ssh_obj in enumerate(ssh_list):
        thread_obj[i] = pool.apply_async(ssh_obj.ssh.close)
    for i, ssh_obj in enumerate(ssh_list):
        thread_obj[i].get()
    pool.close()
    pool.join()


# Natural sort
def atoi(text):
    return int(text) if text.isdigit() else text


def natural_keys(text):
    '''
    alist.sort(key=natural_keys) sorts in human order
    last element in return value is empty string if last value in string is a digit
    '''
    value = [atoi(c) for c in re.split('(\d+)', text)]
    return value


def get_rates(switch_dict, ssh_list):
    # Get switch rates:
    speed_exp = ['B/s', 'KB/s', 'MB/s', 'GB/s']
    cmd = 'show interface ethernet rates'
    good_output = False
    # timeout = 5
    # while not good_output and timeout > 0:
    try:
        all_output = run_threaded_cmd(ssh_list, cmd)
        for output in all_output:
            sw_name_idx = [i for i, s in enumerate(output) if 'CBFSW' in s][0]
            sw_name = output[sw_name_idx].split(' ')[0].split('-')[-1]
            rates = [filter(None, output[y].split(' ')) for y in [i for i, s in enumerate(output) if 'Eth' in s]]
            for line in rates:
                eth = line[0]
                egress = float(line[1]) * (1000 ** (speed_exp.index(line[2])))
                ingress = float(line[4]) * (1000 ** (speed_exp.index(line[5])))
                switch_dict[sw_name][eth]['egress'] = egress
                switch_dict[sw_name][eth]['ingress'] = ingress
        good_output = True
    except (ValueError, IndexError):
        pass
        #        timeout -= 1
    # if timeout == 0:
    #    logger.error('Malformed switch output... trying again')

    # Create rates matrix
    cols = len(switch_dict.keys()) + 1
    if opts.display == 'spines':
        lines = mleaves * 2 + 1
    else:
        # Find how many ethernet ports there are on the leavs
        port_list = []
        lines = 0
        for k, v in switch_dict.iteritems():
            for port in v.keys():
                try:
                    port_list.index(port)
                except ValueError:
                    port_list.append(port)
        port_list = sorted(port_list, key=natural_keys)
        lines = len(port_list) * 2 + 1
    matrix = [[0 for x in range(cols)] for y in range(lines)]
    try:
        sorted_swlist = sorted(switch_dict.keys(), key=natural_keys)
        first_sw = int(natural_keys(sorted_swlist[0])[-2])
    except (ValueError, IndexError):
        logger.error('Switch name not end in a number: {}'.format(first_sw))
        close_ssh(ssh_list)
        raise ValueError
    for switch in switch_dict.keys():
        idx = sorted_swlist.index(switch) + 1
        for port, data in switch_dict[switch].iteritems():
            if opts.display == 'spines':
                if data.has_key('remote_switch'):
                    rem_sw = re.split('(\d+)', data['remote_switch'])
                    try:
                        rem_sw_nr = int(rem_sw[-2])
                    except (ValueError, IndexError):
                        logger.error(
                            'Remote switch name from LLDP does not end in a number: {}'.format(data['remote_switch']))
                        close_ssh(ssh_list)
                        raise ValueError
                    try:
                        matrix[0][idx] = switch
                        matrix[rem_sw_nr * 2 - 1][idx] = data['egress']
                        matrix[rem_sw_nr * 2][idx] = data['ingress']
                        matrix[rem_sw_nr * 2 - 1][0] = 'L' + str(rem_sw_nr) + ' out'
                        matrix[rem_sw_nr * 2][0] = 'L' + str(rem_sw_nr) + '  in'
                    except IndexError:
                        pass
            else:
                try:
                    port_idx = port_list.index(port) + 1
                    matrix[0][idx] = switch
                    matrix[port_idx * 2 - 1][idx] = data['ingress']
                    matrix[port_idx * 2][idx] = data['egress']
                    matrix[port_idx * 2 - 1][0] = port[3:] + ' out'
                    matrix[port_idx * 2][0] = port[3:] + '  in'
                except IndexError:
                    pass
    return matrix


def draw(stdscr, switch_dict, ssh_list):
    from decimal import Decimal

    def fexp(number):
        (sign, digits, exponent) = Decimal(number).as_tuple()
        return len(digits) + exponent - 1

    def fman(number):
        return Decimal(number).scaleb(-fexp(number)).normalize()

    # Clear screen
    stdscr.clear()
    lines = curses.LINES
    cols = curses.COLS
    matrix = get_rates(switch_dict, ssh_list)
    # prev_matrix = matrix
    m_rows = len(matrix)
    m_rows = m_rows + (m_rows / 2)
    m_cols = len(matrix[0])
    # find max number size in matrix
    max_num = max([x for x in [j for i in matrix for j in i] if isinstance(x, int)])
    colw = fexp(max_num) + 1
    if colw < 9: colw = 9
    blank_str = ' ' * colw
    # Initialise windows and colours
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_WHITE, -1)
    curses.init_pair(2, curses.COLOR_BLACK, -1)
    curses.init_pair(3, curses.COLOR_YELLOW, -1)
    curses.init_pair(4, curses.COLOR_YELLOW, -1)
    curses.init_pair(5, curses.COLOR_GREEN, -1)
    curses.init_pair(6, curses.COLOR_GREEN, -1)
    curses.init_pair(7, curses.COLOR_RED, -1)
    curses.init_pair(8, curses.COLOR_RED, -1)
    col_title = curses.newpad(1, m_cols * colw)
    row_title = curses.newpad(m_rows, colw)
    disp_wind = curses.newpad(m_rows, m_cols * colw)
    top_cornr = curses.newpad(1, colw)
    top_cornr.addstr(0, 0, 'Rates', curses.A_BOLD | curses.A_UNDERLINE)
    # Data display block upper left-hand corner
    dminrow = 0
    dmincol = 0
    # Column title upper left-hand corner
    cminrow = 0
    cmincol = 0
    # Row title upper left-hand conrner
    rminrow = 1
    rmincol = 0
    # Data display window
    dwminrow = 1
    dwmincol = colw + 1
    dwmaxrow = lines - 1
    dwmaxcol = cols - 1
    dwrows = dwmaxrow - dwminrow
    dwcols = dwmaxcol - dwmincol
    # Column title display window
    ctminrow = 0
    ctmincol = colw + 1
    ctmaxrow = 0
    ctmaxcol = cols - 1
    # Row title display window
    rtminrow = 1
    rtmincol = 0
    rtmaxrow = lines - 1
    rtmaxcol = colw
    stdscr.nodelay(1)
    try:
        data_rdy = True
        blink = True
        pool = ThreadPool(processes=1)
        while True:
            if data_rdy:
                data_rdy = False
                thread_obj = pool.apply_async(get_rates, args=(switch_dict, ssh_list))
                blankc = 0
                reverse = False
                for i, row in enumerate(matrix):
                    if i == 0:
                        for j, val in enumerate(row):
                            if j == 0:
                                pass
                                # col_title.addstr(i,j, 'Switch', curses.A_BOLD | curses.A_UNDERLINE)
                            else:
                                col_title.addstr(i, (j - 1) * colw, '{0:>{1}}'.format(val, colw),
                                                 curses.A_BOLD | curses.A_UNDERLINE)
                    else:
                        for j, val in enumerate(row):
                            if j == 0:
                                if val == 0:
                                    val = 'N/C'
                                col_pair = 1
                                if reverse: col_pair += 1
                                row_title.addstr(i + blankc - 1, 0, val, curses.color_pair(col_pair) | curses.A_BOLD)
                                if (i - 1) % 2 == 1:
                                    row_title.addstr(i + blankc - 1 + 1, 0, ' ')
                            else:
                                width = colw - 2
                                if not val:
                                    val = 0
                                man = fman(val)
                                exp = fexp(val)
                                if exp < 3:
                                    col_pair = 1
                                    if reverse: col_pair += 1
                                    rate = 'Bs'
                                    val = '{0:>{1}} {2}'.format(int(val), width - 1, rate)
                                elif exp < 6:
                                    col_pair = 1
                                    if reverse: col_pair += 1
                                    rate = 'KB'
                                    man *= 10 ** (exp - 3)
                                    man = man.normalize()
                                    if width - 8 < 0:
                                        val = '{0:>{1}} {2}'.format(int(man), width - 1, rate)
                                    else:
                                        val = '{0:{1}.1f} {2}'.format(man, width - 1, rate)
                                elif exp < 9:
                                    col_pair = 3
                                    if reverse: col_pair += 1
                                    rate = 'MB'
                                    man *= 10 ** (exp - 6)
                                    man = man.normalize()
                                    if width - 8 < 0:
                                        val = '{0:>{1}} {2}'.format(int(man), width - 1, rate)
                                    else:
                                        val = '{0:{1}.1f} {2}'.format(man, width - 1, rate)
                                elif exp < 12:
                                    if man > 4.8:
                                        col_pair = 7
                                        if reverse: col_pair += 1
                                        col_title.addstr(0, (j - 1) * colw, '{0:>{1}}'.format(matrix[0][j], colw),
                                                         curses.color_pair(
                                                             col_pair) | curses.A_BOLD | curses.A_UNDERLINE)
                                        row_title.addstr(i + blankc - 1, 0, matrix[i][0],
                                                         curses.color_pair(col_pair) | curses.A_BOLD)
                                    else:
                                        col_pair = 5
                                        if reverse: col_pair += 1
                                    rate = 'GB'
                                    man *= 10 ** (exp - 9)
                                    man = man.normalize()
                                    val = '{0:{1}.1f} {2}'.format(man, width - 1, rate)
                                else:
                                    col_pair = 1
                                    rate = 'Bs'
                                    val = '{0:>{1}} {2}'.format(int(val), width - 1, rate)
                                disp_wind.addstr(i + blankc - 1, (j - 1) * colw, val, curses.color_pair(col_pair))
                                if (i - 1) % 2 == 1:
                                    disp_wind.addstr(i + blankc - 1 + 1, (j - 1) * colw, ' ')
                        if (i - 1) % 2 == 1:
                            blankc += 1
                            reverse = False  # not(reverse)
                # prev_matrix = matrix
            else:
                char = stdscr.getch()
                if char == curses.ERR:
                    try:
                        if thread_obj.ready():
                            matrix = thread_obj.get()
                            data_rdy = True
                            if blink:
                                top_cornr.addstr(0, 0, 'Rates', curses.A_BOLD | curses.A_UNDERLINE | curses.A_REVERSE)
                            else:
                                top_cornr.addstr(0, 0, 'Rates', curses.A_BOLD | curses.A_UNDERLINE)
                            blink = not (blink)
                        else:
                            time.sleep(0.1)
                    except:
                        return False
                else:
                    redraw = True
                    if char == curses.KEY_LEFT:
                        if dmincol > colw:
                            dmincol -= colw
                        else:
                            dmincol = 0
                    elif char == curses.KEY_RIGHT:
                        if dmincol < (m_cols - 2) * colw - dwcols:
                            dmincol += colw
                        else:
                            dmincol = (m_cols - 1) * colw - dwcols
                    elif char == curses.KEY_UP:
                        if dminrow > 0:
                            dminrow -= 1
                        else:
                            dminrow = 0
                    elif char == curses.KEY_DOWN:
                        if dminrow < m_rows - dwrows - 2:
                            dminrow += 1
                        else:
                            dminrow = m_rows - dwrows - 2
            # Shift titles with text
            cmincol = dmincol
            rminrow = dminrow
            disp_wind.refresh(dminrow, dmincol, dwminrow, dwmincol, dwmaxrow, dwmaxcol)
            col_title.refresh(cminrow, cmincol, ctminrow, ctmincol, ctmaxrow, ctmaxcol)
            row_title.refresh(rminrow, rmincol, rtminrow, rtmincol, rtmaxrow, rtmaxcol)
            top_cornr.refresh(0, 0, 0, 0, 1, colw - 1)
    except KeyboardInterrupt:
        return True



##############################################

HEADERSIZE = 10
IDSIZE = 5
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
    flag1 = False
    flag2 = False
    while True:
        msg = s.recv(256)  # buffer size 16 bytes for incoming message
        if new_msg:
            msg_len = int(msg[:HEADERSIZE])  # convert value in HEADER(expected message length) to int
            logger.debug('Expected message length: %s', msg_len)  # print expected message length
            new_msg = False  # clear new_msg flag

        #full_msg += msg.decode("utf-8")
        full_msg += msg  # append messages

        #print(len(full_msg))
        #logger.debug('Full message length: %s', full_msg)  # print full message length

        if len(full_msg)-HEADERSIZE == msg_len:  # execute when complete message is received based on size indicated in HEADER
            #logger.debug('Full message received: %s', pickle.loads(full_msg[HEADERSIZE+IDSIZE:]))
            print 'ID:', full_msg[HEADERSIZE:HEADERSIZE+IDSIZE]
            if full_msg[HEADERSIZE:HEADERSIZE+IDSIZE].strip() == 'ID01':
                flag1 = True
                ssh_list_values = pickle.loads(full_msg[HEADERSIZE+IDSIZE:])
                print ssh_list_values
            elif full_msg[HEADERSIZE:HEADERSIZE+IDSIZE].strip() == 'ID02':
                flag2 = True
                switch_dict_undefault = pickle.loads(full_msg[HEADERSIZE+IDSIZE:])
                print switch_dict_undefault
            new_msg = True # set new_msg flag
            full_msg = b"" # clear/empty message

        if flag1 & flag2:
            curses.wrapper(draw, switch_dict_undefault, ssh_list_values)
            flag1 = False
            flag2 = False
