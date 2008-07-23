import types

class InvalidEvent: pass

class Watcher:
	def __init__(self):
		self.commands = []
		self.output = []
		self.events = []
		self.errors = []
		self.log = open('/tmp/thunder.log', 'a+')

	def _log(self, msg=''):
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

	def logEvent(self, ev_type='', ev_data=''):
		try:
			if type(ev_type) != types.StringType and type(ev_data) != types.StringType:
				raise InvalidEvent
			if ev_type == '' or ev_data == '':
				raise InvalidEvent
			else:
				if ev_type == 'command': self.commands.append(ev_data)
				if ev_type == 'output': self.output.append(ev_data)
				if ev_type == 'events': self.events.append(ev_data)
				if ev_type == 'errors': self.errors.append(ev_data)
				self._log(event)
				return True
		except InvalidEvent:
			err = 'ERROR: Invalid data passed to logEvent()\nDATA: (%s, %s)' % (repr(ev_type),repr(ev_data))
			self.errors.append(err)
			self.logMsg(err)
			return False

	def getNextEvent(self, ev_type=''):
		try:
			if ev_type == 'command':
				retv = self.commands[0]
				self.commands.pop(0)
			elif ev_type == 'output':
				retv = self.output[0]
				self.output.pop(0)
			elif ev_type == 'events':
				retv = self.events[0]
				self.events.pop(0)
			elif ev_type == 'errors':
				retv = self.errors[0]
				self.errors.pop(0)
			else: raise InvalidEvent
		except InvalidEvent:
			err = 'ERROR: Invalid data passed to getNextEvent()\nDATA: (%s)' % (repr(ev_type))
			self.errors.append(err)
			self.logMsg(err)
			return False
