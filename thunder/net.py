import os, urllib2, sys
import popen2, types

def Fetch(uri='', watcher=None):
	if type(uri) != types.StringType or uri == '' or watcher == None:
		return False
	try:	
		handle = urllib2.urlopen(uri)
		data_t = int(handle.info().items()[0][1])
		data = handle.read(512000) 
		data_s = 0
		fp = open(os.path.basename(uri), 'w+')
		while data != '':
			data_s += int(len(data))
			watcher.logEvent('events', 'Fetching %s: %d%%' % (os.path.basename(uri),int((float(data_s)/float(data_t))*100)))
			fp.write(data)
			data = handle.read(512000)
		fp.flush()
		fp.close()
	except:
		watcher.logEvent('errors', 'Error fetching %s' % uri)
	return True

	
def FandA(uri='', dst='./', watcher=None):
	if type(uri) != types.StringType or type(dst) != types.StringType or uri == '' or dst == './' or watcher == None:
		return False
	try:
		handle = urllib2.urlopen(uri)
		data_t = int(handle.info().items()[0][1])
		data = handle.read(512000)
		data_s = 0
		args = '-jxf'
		tar = popen2.Popen4('tar %s - -C %s' % (args, dst))
		while data != '':
			data_s += int(len(data))
			watcher.logEvent('events', 'Fetching and extracting %s: %d%%' % (os.path.basename(uri), int((float(data_s)/float(data_t))*100)))
			tar.tochild.write(data)
			data = handle.read(512000)
		watcher.logEvent('events', 'Fetching and extracting %s: 100%%\n' % (os.path.basename(uri)))
	except:
		watcher.logEvent('errors', 'Fetching and extracting %s: ERROR\n' % (os.path.basename(uri)))
	return True
