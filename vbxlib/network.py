

# RTG: don't use, rewrite!!!
# https://stackoverflow.com/questions/2953462/pinging-servers-in-python
import platform    # For getting the operating system name
import subprocess  # For executing a shell command

def ping(host):
    """
    Returns True if host (str) responds to a ping request.
    Remember that a host may not respond to a ping (ICMP) request even if the host name is valid.
    """

    # Option for the number of packets as a function of
    param = '-n' if platform.system().lower()=='windows' else '-c'

    # Building the command. Ex: "ping -c 1 google.com"
    command = ['ping', param, '1', host]

    return subprocess.call(command) == 0 # original
    return subprocess.run(command).returncode == 0 # new
    # RTG: both do not wor with 'node is unreacheable', returns 0 exitcode and 0% packet loss
    # RTG: both print out redundant info in wrong encoding


#https://stackoverflow.com/questions/7678456/local-network-pinging-in-python
from socket import *

def ping_port(host, port, print_out=True):

    if isinstance(port, str): port = int(port)

    s = socket(AF_INET, SOCK_STREAM)

    try:
        s.settimeout(3)
        s.connect((host, port))
        is_online = True
    except Exception as e:
        is_online = False
        msg = ('no connection: {}'.format(e))
    finally:
        s.close()

    if print_out:
        print('Host {}:{} is {}'.format(host, port, 'online' if is_online else 'offline ({})'.format(msg)))

    return is_online
