#!/usr/bin/env python
# stdlib imports
import os,  sys,  re
import time,  random
import types, popen2
# thunder imports
import slurp, net
import event

class Engine:
	def __init__(self, spec):
		self.DEBUG = False ; self.watcher = event.Watcher()
		self.partitions = {} ; self.th_vars = []
		self.host_cmds = [] ; self.chroot_cmds = []
		self.profile = [] ; self.handler_map = [
			('^debug.*', self._toggleDebug),
			('^set.*', self.setVar), ('^detect-disks.*', self.detectDisks),
			('^clear-partitions.*', self.clearPartitions),
			('^partition-disk.*', self.partitionDisk),	
			('^commit-partitions.*', self.commitPartitions),
			('^format-partition.*', self.formatPartition),
			('^mount-partition.*', self.mountPartition),
			('^swapon.*', self.swapOn), ('^exec-command.*', self.execCommand),
			('^fetch.*', self.fetchUri),
			('^fetch-and-extract.*', self.fetchAndExtract),
			('^chroot-command.*', self.chrootCommand),
			('^chroot-batch.*', self.chrootBatch)
		]
		self.watcher.logEvent('events', 'Profiling spec file %s' % spec)
		self._profile(spec, self.handler_map)
		self.slurp = slurp.Proc()
		for i in self.handler_map:
			if self.DEBUG == True: self.watcher.logEvent('debug', 'adding callback %s with pattern %s' % (repr(i[1]),i[0]))
			self.slurp.register_trigger(args={'t_pattern': i[0], 't_callback': i[1]})
		sp = open(spec, 'r')
		self.slurp.run(sp)

	def _profile(self, spec, map):
		slrp = slurp.Proc()
		for i in map:
			slrp.register_trigger(args={'t_pattern': i[0], 't_callback': self._profileFunc)
		slrp.run(open(spec, 'r'))
		slrp = None

	def _profileFunc(self, txt):
		cmd = txt.split()[0]
		num = len(self.profile) - 1
		self.profile.append((num, cmd))

	def setVar(self, txt):
		if type(txt) != types.StringType and txt != '':
			tmp = txt.split()
			self.th_vars.append((tmp[1], tmp[2]))
			if self.DEBUG == True: self.watcher.logEvent('debug', 'Setting key %s to value %s' % (tmp[1], tmp[2]))
			self.watcher.logEvent('events', txt.strip()+'\n')
			return True
		else:	return False
	
	def detectDisks(self, txt):
		if type(txt) == types.StringTYpe and txt != '':
			self.watcher.logEvent('events', txt.strip()+'\n')
			tmp_dsks = []
			for i in os.listdir('/dev/'):
				if i.find('hd') != -1 or i.find('sd') != -1:
					if len(i) == 3: tmp_dsks.append(i)
			self.th_disks = tmp_dsks
			self.th_disks.sort()
			line = txt.split()
			line.pop(0)
			for i in range(len(line)):
				if line[i] == 'prefer':
					prefer = line[(i+1)]
				if line[i] == 'accept':
					accept = line[(i+1)]
			pref_tmp = []
			acpt_tmp = []
			for i in self.th_disks:
				if i.find(prefer) != -1:
					pref_tmp.append(i)
				if i.find(accept) != -1:
					acpt_tmp.append(i)
			self.disks = []
			pref_tmp.sort()
			acpt_tmp.sort()
			for a in (pref_tmp, acpt_tmp):
				for b in a:
					self.disks.append(b)
			cnt=0
			for i in self.disks:
				self.th_vars.append(('drive%d' % cnt, '/dev/%s' % i))
				if self.DEBUG == True: self.watcher.logEvent('debug', 'Setting key drive%d to value /dev/%s' % (cnt,i))
				self.partitions[i] = []
				cnt += 1
			return True
		else: return False

	def clearPartitions(self, txt):
		if type(txt) == types.StringType and txt != '':
			tmp = self._chkSubs(txt)
			self.watcher.logEvent('events', tmp)
			line = tmp.split()
			disk = line[1]
			self._execCmd('dd if=/dev/zero of=%s bs=512K count=1' % disk)
			return True
		else: return False

	def partitionDisk(self, txt):
		if type(txt) == types.StringType and txt != '':
			tmp = self._chkSubs(txt)
			self.watcher.logEvent('events', tmp)
			opts = tmp.split()
			dev = opts[1]
			type = opts[2]
			if type == 'primary' or type == 'logical':
				pnum = opts[3]
				pnam = opts[4]
				if opts[5] != 'all': psze = opts[5]
				if opts[5] == 'all': psze = ''
				ptyp = opts[6]
				self.th_vars.append((pnam, '%s%s' % (dev,pnum)))
				if self.DEBUG == True: self.watcher.logEvent('debug', 'Setting key %s to value %s%s' % (pnam,dev,pnum))
				self.partitions[os.path.basename(dev)].append(',%s,%s' % (psze,ptyp))
			elif type == 'extended':
				if opts[3] != 'all': psze = opts[3]
				else: psze = ''
				self.partitions[os.path.basename(dev)].append(',%s,E' % psze)
			return True
		else: return False

	def commitPartitions(self, txt):
		if type(txt) == types.StringType and txt != '':
			kys = self.partitions.keys()
			kys.sort()
			for i in kys:
				if self.partitions[i] != []:
					self.watcher.logEvent('events', 'Partitioning %s' % i)
					fp = open('/tmp/partitions', 'w+')
					for b in self.partitions[i]:
						fp.write(b+'\n')
					fp.close()
					self._execCmd('cat /tmp/partitions | /sbin/sfdisk -uM /dev/%s' % i)
			return True
		else: return False

	def formatPartition(self, txt):
		if type(txt) == types.StringType and txt != '':
			line = self._chk_subs(txt).split()
			self.watcher.logEvent('events', line)
			line.pop(0)
			part = line[0]
			labl = line[1].upper()
			type = line[2]
			for i in [1,2,3]: line.pop(0)
			if len(line) > 0:
				args = ''
				for i in line:
					args = args+i+' '
				t = re.sub('\"', '', args)
				args = t
				if self._which('mkfs.%s' % type) != False:
					cmd = 'mkfs.%s -L %s %s %s' % (type, labl, re.sub("'", "", args), part)
			else:
				if self._which('mkswap') != False:
					cmd = 'mkswap -L %s %s' % (labl, part)
			self.watcher.logEvent('events','Formatting %s as %s\r' % (part,type))
			self._execCmd(cmd)
			return True
		else: return False

	def mountPartition(self, txt):
		if type(txt) == types.StringType and txt != '':
			line = self._chk_subs(txt).split()
			self.watcher.logEvent('events', line)
			line.pop(0)
			cmd = 'mount '
			if len(line) > 3:
				who = line[0]
				line.pop(0)
				what = line[0]
				line.pop(0)
				where = line[0]
				line.pop(0)
				opts = ''
				for i in line:
					opts = opts+i+' '
				t = re.sub('\"','',opts)
				opts = t
				t = re.sub("'", '', opts)
				opts = t
				gen = 1
			elif len(line) == 3:
				who = line[0]
				what = line[1]
				where = line[2]
				gen = 1
			elif len(line) == 2:
				gen = 0
				if line[0] == 'proc':
					cmd = cmd+'-t proc proc %s' % line[1]
					if os.path.isdir(line[1]) == False:
						self._execCmd('mkdir %s && sleep 1' % line[1])
						if self.DEBUG == True: self.watcher.logEvent('debug', 'mkdir %s && sleep 1' % line[1])
					who = 'proc'
					where = line[1]
			if gen == 1:
				if len(line) == 3:
					if what == 'auto':
						cmd = cmd+'%s %s' % (who, where)
					else:
						cmd = cmd+'-t %s %s %s' % (what, who, where)
				else:
					if what == 'auto':
						cmd = cmd+'-o %s %s %s' % (opts, who, where)
					else:
						if what != 'none':
							cmd = cmd+'-o %s -t %s %s %s' % (opts, what, who, where)
						else:
							cmd = cmd+'-o %s %s %s' % (opts, who, where)
				if os.path.isdir(where) == False:
					self._execCmd('mkdir %s && sleep 1' % where)
					if self.DEBUG == True: self.watcher.logEvent('debug', 'mkdir %s && sleep 1' % where)
			self.watcher.logEvent('events', 'Mounting %s on %s' % (who, where))
			self._execCmd(cmd)
			return True
		else: return False

	def swapOn(self, txt):
		if type(txt) == types.StringType and txt != '':
			tmp = self._chkSubs(txt).split()
			self.watcher.logEvent('events', tmp)
			tmp.pop(0)
			for i in tmp:
				if self._which('swapon') != False:
					cmd = 'swapon %s' % i
					self.watcher.logEvent('events', 'Activating swap on %s' % i)
					self._execCmd(cmd)
			return True
		else: return False

	def fetchUri(self, txt):
		if type(txt) == types.StringType and txt != '':
			tmp = self._chkSubs(txt)
			self.watcher.logEvent('events', tmp)
			uri = tmp.split()[1]
			tmp = net.Fetch(uri, self.watcher)
			return True
		else: return False

	def fetchAndExtract(self, txt):
		if type(txt) == types.StringType and txt != '':
			tmp = self._chkSubs(txt)
			uri = tmp.split()[1]
			archive = os.path.basename(uri)
			try: lcation = tmp.split()[2]
			except: lcation = './'
			tmp = net.FandA(uri, lcation, self.watcher)
			return True
		else: return False

	def execCommand(self, txt):
		if type(txt) == types.StringType and txt != '':
			ln_t = self._chkSubs(txt).split()
			self.watcher.logEvent('events', ln_t)
			ln_t.pop(0)
			li_t = ''
			for i in ln_t: li_t = li_t+i+' '
			if li_t[0].isalpha() == False and li_t[len(li_t)-1].isalpha() == False:
				line = li_t.strip()[1:][:-1]
			elif li_t[0].isalpha() == False and li_t[len(li_t)-1].isalpha() == True:
				line = li_t[1:]
			elif li_t[0].isalpha() == True and li_t[len(li_t)-1].isalpha() == False:
				line = li_t.strip()[:-1]
			else: line = li_t
			self._execCmd(line, flag=0)
			return True
		else: return False

	def chrootCommand(self, txt):
		if type(txt) == types.StringType and txt != '':
			tmp = self._chkSubs(txt)
			self.watcher.logEvent('events', tmp)
			line = tmp.split()
			line.pop(0)
			script = ''
			for i in line: script = script+i+' '
			self.chroot_cmds.append(script)
			return True
		else: return False

	def chrootBatch(self, txt):
		if type(txt) == types.StringType and txt != '':
			tmp = self._chkSubs(txt)
			self.watcher.logEvent('events', tmp)
			chroot = tmp.split()[1]
			self.watcher.logEvent('events', 'Executing commands in chroot.')
			fp = open('%s/chroot-commands.sh' % chroot, 'w+')
			fp.write('#!/bin/bash -x\n')
			for i in self.chroot_cmds:
				line = i[1:][:-2]
				fp.write(line+'\n')
			fp.close()
			self._execCmd('chmod +x %s/chroot-commands.sh' % chroot)
			time.sleep(1)
			self._execCmd('chroot %s ./chroot-commands.sh' % chroot)
			self.chroot_cmds = []
			return True
		else: return False

	def _execCmd(self, cmd, flag=1):
		if type(cmd) == types.StringType and cmd != '':
			line = self._chk_subs(cmd)
			self.watcher.logEvent('events', line)
			if self.DEBUG == True: self.watcher.logEvent('debug', 'Executing command: %s' % line)
			pipe = popen2.Popen4(line)
			buff = pipe.fromchild.readline()
			while buff != '':
				self.watcher.logEvent('output', buff)
				buff = pipe.fromchild.readline()
			if pipe.poll() > 0:
				self.watcher.logEvent('errors', 'Error while running command:\n%s...\n' % line)
			return True
		else: return False

	def _chkSubs(self, txt):
		if type(txt) == types.StringType and txt != '':
			key = ''
			retv = ''
			for i in txt.split():
				if i[0] == '%':
					key = i[1:]	
					for a in self.th_vars:
						if key == a[0]:
							if self.DEBUG == True:
								self.watcher.logEvent('debug', 'Replacing %s with %s' % (a[0], a[1]))
							retv = retv+a[1]+' '
				else:
					retv = retv+i+' '
			return retv
		else: return False
	
	def _which(self, prog):
		for path in os.getenv('PATH').split(':'):
			if os.path.isdir(path):
				for file in os.listdir(path):
					if file == prog:
						return os.path.join(path, file) 
		return False

	def _toggleDebug(self):
		if self.DEBUG == False: self.DEBUG = True
		if self.DEBUG == True: self.DEBUG = False
		return None

