import types

class Watcher:
	def __init__(self):
		self.commands = []
		self.output = []
		self.events = []
		self.errors = []
		self.log = open('/tmp/thunder.log', 'a+')

	def logMsg(self, msg=''):
		try:
			if type(msg) != types.StringType and msg != '':
				raise InvalidEvent
			else:
				self.log.write(msg.strip()+'\n')
				self.log.flush()
		except InvalidEvent:
			err = 'ERROR: Invalid data passed to logMsg()\nDATA: %s' % repr(msg)
			self.log.write(msg.strip()+'\n')
			self.log.flush()

	def logEvent(self, event=''):
		try:
			if type(event) != types.StringType and event != '':
				raise InvalidEvent
			else:
				self.events.append(event)
				self.logMsg(event)
		except InvalidEvent:
			err = 'ERROR: Invalid data passed to logEvent()\nDATA: %s' % repr(event)
			self.errors.append(err)
			self.logMsg(err)

	def logError(self, error=''):
		try:
			if type(error) != types.StringType and error != '':
				raise InvalidEvent
			else:
				self.errors.append(error)
		except InvalidEvent:
			err = 'ERROR: Invalid data passed to logError()\nDATA: %s' % repr(error)
			self.errors.append(error.strip()+'\n')
			self.logMsg(err)

