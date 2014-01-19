import numpy
import matplotlib.pyplot as plt



speeds = ['slow', 'fast', 'moderate']
transfersizes = ['short', 'medium', 'long']
drops = ['1', '2', '4', '8']
tlps = ['on', 'off']

def extract_vectors(file):
	return numpy.loadtxt(file, unpack=True)

def plot(data, filename):

	plt.boxplot(data, notch=False, sym='+', vert=True, whis=1.5,
		positions=None, widths=None, patch_artist=False,
		bootstrap=None, usermedians=None, conf_intervals=None)

	plt.savefig('plots/%s' % filename)
	plt.clf()


for speed in speeds:
	for transfersize in transfersizes:

		vector_1_off = []
		vector_2_off = []
		vector_4_off = []
		vector_8_off = []

		vector_1_on = []
		vector_2_on = []
		vector_4_on = []
		vector_8_on = []

		for drop in drops:

			for tlp in tlps:

				filename = 'measurements/%s_%s_%s_tlp%s' % (speed, transfersize, drop, tlp)



				if tlp == 'off':
					if drop == '1':
						vector_1_off = extract_vectors(filename)
					elif drop == '2':
						vector_2_off = extract_vectors(filename)
					elif drop == '4':
						vector_4_off = extract_vectors(filename)
					else:
						vector_8_off = extract_vectors(filename)

				elif tlp=='on':
					if drop == '1':
						vector_1_on = extract_vectors(filename)
					elif drop == '2':
						vector_2_on = extract_vectors(filename)
					elif drop == '4':
						vector_4_on = extract_vectors(filename)
					else:
						vector_8_on = extract_vectors(filename)




		completion_time = [vector_1_off[0], vector_1_on[0], vector_2_off[0], vector_2_on[0],
			vector_4_off[0], vector_4_on[0], vector_8_off[0], vector_8_on[0]]



		transmission_time = [vector_1_off[1], vector_1_on[1], vector_2_off[1], vector_2_on[1],
			vector_4_off[1], vector_4_on[1], vector_8_off[1], vector_8_on[1]]


		print completion_time
		
		plot(completion_time, 'completion_time_%s_%s' % (speed, transfersize))
		plot(transmission_time, 'transmission_time_%s_%s' % (speed, transfersize))



		
				
