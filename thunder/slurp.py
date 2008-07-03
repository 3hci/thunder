import re

class Proc:
	def __init__(self):
		self.triggers = []

	def register_trigger(self, args={}):
		try: self.triggers.append(args)
		except: return False
		return True

	def run(self, fp=None):
		if fp != None:
			bf = fp.readline()
			while bf != '':
				for i in self.triggers:
					if re.match(i['t_pattern'],bf.strip()): 
						i['t_callback'](bf.strip())
				bf = fp.readline()

