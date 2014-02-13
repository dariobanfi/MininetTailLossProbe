'''

This program is used to create measurements of 
the mininet configuration
It generates a total of 72 files, with all the single
configurations

'''


import dpkt
import datetime
import os

__author__ = "Dario Banfi, Thomas Kuehner"
__license__ = "GPL"
__version__ = "2.0"
__email__ = "dario.banfi@tum.de"
__status__ = "Developement"

def main():

	speeds = ['slow', 'fast', 'moderate']
	transfersizes = ['short', 'medium', 'long']
	drops = ['1', '2', '4', '8']
	tlps = ['on', 'off']


	for speed in speeds:
		for transfersize in transfersizes:
			for drop in drops:
				for tlp in tlps:

					if tlp=='on':
						tcp_early_retrans = '3'
					else:
						tcp_early_retrans = '2'

					# Configurating different params and saving to 
					# measurements folder
					os.system('sysctl -w net.ipv4.tcp_early_retrans=%s' % tcp_early_retrans)
					os.system('python mininet_tlp_measurement.py -s %s -ts %s -d %s' % (speed, transfersize, drop))
					measure_pcap('measurements/%s_%s_%s_tlp%s.txt' % (speed, transfersize, drop, tlp))




def measure_pcap(savefile):

	'''
	Opens a pcap files and saves on a text
	file the completion_time and the retransmission_time
	separated by a tabulation
	'''

	f = open('out.pcap')
	pcap = dpkt.pcap.Reader(f)

	tcp_packets = []

	# Putting only TCP packets in to tcp_packets list
	for ts, buf in pcap:
		eth = dpkt.ethernet.Ethernet(buf)


		# Considering only IPv4 packets
		if eth.type == 2048:
			ip = eth.data
			if type(ip.data) == dpkt.tcp.TCP:
				tcp_packets.append((datetime.datetime.fromtimestamp(ts),ip.data))

	f.close()

	# Completion time is calculated as the last tcp packet time
	# minus the first

	completion_time = tcp_packets[-1][0] - tcp_packets[0][0]
	completion_time_seconds = str(completion_time.total_seconds())

	# Getting Syn and Ack tcp sequence numbers
	syn = tcp_packets[0][1].seq
	ack = syn + 1

	sequence_numbers = {}
	retransmitted_packets = {}

	for timestamp, packet in tcp_packets:

		# We ignore ack and syn since their sequence number doesn't change
		if packet.seq != ack and packet.seq != syn:

			# If the seq number is in the dict, it means that packet
			# is a duplicate, so a retransmission. We save it to the dict
			# of retransmitted packets
			if str(packet.seq) in sequence_numbers:
				retransmitted_packets[str(packet.seq)] = (timestamp, packet)
				continue

			sequence_numbers[str(packet.seq)] = (timestamp,packet)

	if not retransmitted_packets:
		retransmission_time_seconds = '0'
	else:
		# We get the retransmitted packet with the lowest seq number
		# which will be the retransmission of the  first dropped packet

		first_retransmission = retransmitted_packets[min(retransmitted_packets)]

		retransmission_time =  first_retransmission[0] - sequence_numbers[str(first_retransmission[1].seq)][0]
		retransmission_time_seconds = str(retransmission_time.total_seconds())

	
	with open(savefile, 'a') as output:
		
		output.write(completion_time_seconds + '\t' + retransmission_time_seconds + '\n')
		
measure_pcap('test.txt')
