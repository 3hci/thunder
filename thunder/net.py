import os, urllib2, sys

class Fetch:
	def __init__(self, uri):
		try:
			handle = urllib2.urlopen(uri)
			data_t = int(handle.info().items()[0][1])
			fp = open(os.path.basename(uri), 'w+')
			data = handle.read(40960)
			data_s = 0
			while data != '':
				data_s += int(len(data))
				sys.stdout.write('\r[ ] Fetching %s: %d%%' % (os.path.basename(uri), int((float(data_s)/float(data_t))*100)))
				sys.stdout.flush()
				data = handle.read(40960)
			print ''
		except urllib2.HTTPError:
			sys.stdout.write('[ERROR]: %s' % 'error')
			sys.stdout.flush()
			sys.exit(-1)
		return None


