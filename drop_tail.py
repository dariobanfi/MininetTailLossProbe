'''

Mininet TLP measurement project

This program is launched by a host which
is trasmitting data, redirected to the nfqueue
number 0.
It simply drops the number of packets 
passed by the argument --drop

'''

import argparse
import nfqueue
import socket

__author__ = "Dario Banfi, Thomas Kuehner"
__license__ = "GPL"
__version__ = "2.0"
__email__ = "dario.banfi@tum.de"
__status__ = "Developement"


parser = argparse.ArgumentParser(
    description='Create a tail loss in TCP Segements')

parser.add_argument('-d',
    '--drop',
    required=True,
    help='Number of tail packets to drop')

parser.add_argument('-ts',
    '--transfersize',
    required=True,
    help='Set the transfer size of the TCP packets', 
    choices=['short', 'medium', 'long'])

args = vars(parser.parse_args())

transfersize = args['transfersize']
if transfersize == 'short':
    size = 64
elif transfersize == 'medium':
    size = 128
elif transfersize == 'long':
    size = 256
else:
    raise ValueError('Illegal argument ' + transfersize)

# Upper and lower limit for the packets to drop
# The upper limit is calculated as the transmission
# size + 2 because we have also to count the
# SYN and FIN acknowledgements packets which
# get caught by the nfqueue

upper_limit = size + 2
lower_limit = upper_limit - int(args['drop'])
counter = 1

def callback(handle, handle_new=None):

    '''

    nfqueue-bindings callback function which 
    checks if the counter is within the drop window,
    and if yes, it drops it

    It would be better to drop with sequence numbers,
    but since the drops aren't too big there shouldn't
    be problems with the counter approach.

    '''

    global counter

    if handle_new is not None:
        handle = handle_new

    if lower_limit <= counter < upper_limit:
        handle.set_verdict(nfqueue.NF_DROP)
    else:
        handle.set_verdict(nfqueue.NF_ACCEPT)

    counter = counter + 1


# Creating the queue number 0 and setting the
# right callback function

queue = nfqueue.queue()
queue.open()
queue.bind(socket.AF_INET)
queue.set_callback(callback)
queue.create_queue(0)

try:
    queue.try_run()
except (KeyboardInterrupt, SystemExit):
    queue.unbind(socket.AF_INET)
    queue.close()



