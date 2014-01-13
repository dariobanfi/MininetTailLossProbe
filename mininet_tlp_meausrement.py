'''

Mininet TLP measurement project

This program creates emulated network through
the mininet library and generates some TCP
traffic between the hosts, which is saved as
a .pcap file in the working directory

PROUDLY RATED 10/10 BY PYLINT

'''

import argparse
import traceback
import time
from mininet.topo import Topo
from mininet.link import TCLink
from mininet.net import Mininet
from mininet import log

__author__ = "Dario Banfi, Thomas Kuehner"
__license__ = "GPL"
__version__ = "2.0"
__email__ = "dario.banfi@tum.de"
__status__ = "Developement"


def main():

    '''

    Main function of the program
    Its process the arguments given by command
    line and it creates the network
    After that, it starts a nc6 server on A and
    make C request data, which is saved via 
    tcpdump on the interface linking A and B

    '''

    port = 5000

    log.setLogLevel('info')

    parser = argparse.ArgumentParser(
        description='Create a new virtual network simulation')

    parser.add_argument('-s',
        '--speed',
        help='Sets the link speed and latency.' \
        'Possible values: slow, fast and moderate', 
        choices=['slow', 'fast', 'moderate'],
        default='moderate')

    parser.add_argument('-ts',
        '--transfersize',
        help='Set the transfer size of the TCP packets', 
        choices=['short', 'medium', 'long'], default='medium')

    parser.add_argument('-f',
        '--file',
        help='Defines the filename of the generated pcap file',
        default='out.pcap')

    parser.add_argument('-d',
        '--drop',
        help='Number of tail packets to drop',
        default='0')

    args = vars(parser.parse_args())
    topo = MininetTopo(args['speed'])
    net = Mininet(topo, link=TCLink)
    host_a, host_b, host_c = net.get('h1', 'h2', 'h3')

    print 'Configuring hosts'
    _configure_network_hosts(host_a, host_b, host_c)

    # Calling drop_tail to drop the segments

    print 'Prepairing to drop %s packets' % args['drop']
    _drop_tail(host_b, args['drop'] , args['transfersize'])


    net.start()

    time.sleep(1)


    try:
        
        print 'Starting nc6 server'
        _start_server(host_a, port, args['transfersize'])

        print 'Launching tcpdump'
        _record_traffic(host_b, 'h2-eth0', args['file'] )

        print 'Starting transmission, please wait. (2 min max)'
        _request_packets(host_c, host_a.IP(), port)

    # Catching KeyboardInterrupt and SystemExit in case
    # the programs hangs or it's killed, so that the
    # finally statements gets executed
    except KeyboardInterrupt:
        print traceback.format_exc() 

    # Closing the network and killing the background processes
    finally:
        print 'Cleaning processes'
        time.sleep(1)
        print 'Shutting down'
        host_a.cmd('pkill nc6')
        host_a.cmd('pkill tcpdump')
        host_b.cmd('pkill -f "python drop_tail.py"')
        net.stop()

class MininetTopo(Topo):

    '''

    Creates a custom mininet topology consisting of 3 Hosts and
    2 links.
    The host in the middle acts as a router and has two interfaces.
    The host A belongs to the same subnet of B host's interface 0,
    and the host C belongs to the same subnet of B host's 
    interface 1

    '''

    def __init__(self, speed, **opts):
        Topo.__init__(self, **opts)

        if speed == 'fast':
            bandwidth = 1
            delay = '5ms'
        elif speed == 'moderate':
            bandwidth = 0.5
            delay = '10ms'
        elif speed == 'slow':
            bandwidth = 0.1
            delay = '20ms'
        else:
            raise ValueError('Illegal argument ' + speed)

        self.node_a = self.addHost('h1', ip='10.0.1.1/24')
        self.node_b = self.addHost('h2', ip='10.0.1.2/24')
        self.node_c = self.addHost('h3', ip='10.0.2.2/24')

        self.addLink(self.node_a, self.node_b, bw = bandwidth, delay = delay,
            use_tbf=True)
        self.addLink(self.node_b, self.node_c, bw = bandwidth, delay = delay,
            use_tbf=True)


def _drop_tail(host, drop, transfer_size):

    ''' 

    Forwards packet in the host to a NFQUEUE
    and launches drop_tail.py on it 

    '''

    host.cmd('modprobe nfnetlink_queue')
    host.cmd('iptables -A FORWARD -i h2-eth0 -o h2-eth1 \
        -p tcp -j NFQUEUE --queue-num 0')

    host.cmd('python drop_tail.py -d %s -ts %s &' % (drop, transfer_size))


def _configure_network_hosts(host_a, host_b, host_c):

    ''' Configuration of the network hosts '''

    # Setting a IP address to the 2nd interface of B
    # and enabling ip_forward
    host_b.intf('h2-eth1').setIP('10.0.2.1/24')
    host_b.cmd('sysctl net.ipv4.ip_forward=1')

    # Configuring the routing tables to let the two
    # subnets communicate
    host_a.cmd('route add default gw 10.0.1.2')
    host_b.cmd('route add -net 10.0.2.0 netmask 255.255.255.0 gw 10.0.2.1')
    host_c.cmd('route add default gw 10.0.2.1')
    host_b.cmd('route add -net 10.0.1.0 netmask 255.255.255.0 gw 10.0.1.2')

def _request_packets(host, ip_address, port):

    ''' 
    Launches a nc6 client on on the given ip_address
    and port and dumps the received bytes into /dev/null
    '''

    request = 'nc6 %s %d > /dev/null' % (ip_address, port)
    print host.cmd(request)

def _start_server(host, port, transfersize):

    '''
    Starts a nc6 server on the given host, listening
    on the port and serving data from /dev/zero from
    clients connecting to him
    '''

    # Numbers of TCP packets sent
    if transfersize == 'short':
        size = 64
    elif transfersize == 'medium':
        size = 128
    elif transfersize == 'long':
        size = 256
    else:
        raise ValueError('Illegal argument ' + transfersize)

    command = 'dd if=/dev/zero bs=1448 count=%d |' \
    ' nc6 -4 -v -l --rev-transfer -p %d &' % (size, port)
    print  host.cmd(command)

def _record_traffic(host, interface, save_file):

    ''' Opens a tcpdump instance on the host's interface '''

    host.cmd('tcpdump -p -i %s -s 68 -w %s &' % (interface, save_file))

if __name__ == '__main__':

    main()
