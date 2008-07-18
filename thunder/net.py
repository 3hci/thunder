import os, urllib2, sys
import popen2

class Fetch:
	def __init__(self, uri):
		try:
			handle = urllib2.urlopen(uri)
			data_t = int(handle.info().items()[0][1])
			data = handle.read(512000)
			data_s = 0
			args = '-jxf'
			tar = popen2.Popen4('tar %s -' % args)
			while data != '':
				data_s += int(len(data))
				sys.stdout.write('\r[ ] Fetching %s: %d%%' % (os.path.basename(uri), int((float(data_s)/float(data_t))*100)))
				sys.stdout.flush()
				tar.tochild.write(data)
				data = handle.read(512000)
			sys.stdout.write('\r[+] Fetching %s: 100%%\n' % (os.path.basename(uri)))
			sys.stdout.flush()
		except urllib2.HTTPError:
			sys.stdout.write('\r[X] Fetching %s: ERROR\n' % (os.path.basename(uri)))
			sys.stdout.flush()
			sys.exit(-1)
		return None
