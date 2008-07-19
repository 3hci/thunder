import os, urllib2, sys
import popen2

def Fetch(uri):
	try:	
		handle = urllib2.urlopen(uri)
		data_t = int(handle.info().items()[0][1])
		data = handle.read(512000) 
		data_s = 0
		fp = open(os.path.basename(uri), 'w+')
		while data != '':
			data_s += int(len(data))
			sys.stdout.write('\r[ ] Fetching %s: %d%%' % (os.path.basename(uri),int((float(data_s)/float(data_t))*100)))
			sys.stdout.flush()
			fp.write(data)
			data = handle.read(512000)
		sys.stdout.write('\r[+]\n')
	except:
		sys.stdout.write('\r[X]\n')
		sys.stdout.flush()
		sys.exit(255)
	sys.stdout.flush()
	return True

	
def FandA(uri, dst='./'):
	try:
		handle = urllib2.urlopen(uri)
		data_t = int(handle.info().items()[0][1])
		data = handle.read(512000)
		data_s = 0
		args = '-jxf'
		tar = popen2.Popen4('tar %s - -C %s' % (args, dst))
		while data != '':
			data_s += int(len(data))
			sys.stdout.write('\r[ ] Fetching and extracting %s: %d%%' % (os.path.basename(uri), int((float(data_s)/float(data_t))*100)))
			sys.stdout.flush()
			tar.tochild.write(data)
			data = handle.read(512000)
		sys.stdout.write('\r[+] Fetching and extracting %s: 100%%\n' % (os.path.basename(uri)))
		sys.stdout.flush()
	except:
		sys.stdout.write('\r[X] Fetching and extracting %s: ERROR\n' % (os.path.basename(uri)))
		sys.stdout.flush()
		sys.exit(-1)
	return True
