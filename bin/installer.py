#!/usr/bin/env python2.5
import os, sys, re
from thunder import mslurp

class Thunder:
	def __init__(self, file):
		self.slurp = mslurp.Proc()
		self.th_vars = []
		self.slurp.register_trigger(args={'t_pattern': '^set.*', 't_callback': self.set})
		self.slurp.register_trigger(args={'t_pattern': '^detect-disks.*', 't_callback': self.detect_disks})
		self.slurp.register_trigger(args={'t_pattern': '^partition-disk.*', 't_callback': self.partition_disk})
		self.slurp.register_trigger(args={'t_pattern': '^format-partition.*', 't_callback': self.format_partition})
		self.slurp.register_trigger(args={'t_pattern': '^mount-partition.*', 't_callback': self.mount_partition})
		self.slurp.register_trigger(args={'t_pattern': '^fetch-and-extract.*', 't_callback': self.fetch_and_extract})
		self.slurp.register_trigger(args={'t_pattern': '^exec-command.*', 't_callback': self.exec_command})
		self.slurp.register_trigger(args={'t_pattern': '^chroot-command.*', 't_callback': self.chroot_command})
		fp = open(file, 'r')
		self.slurp.run(fp)

	def set(self, txt):
		tmp = txt.split()
		self.th_vars.append((tmp[1], tmp[2]))
		return
	
	def detect_disks(self, txt):
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
			cnt += 1
		return self.disks

	def partition_disk(self, txt):
		tmp = self._chk_subs(txt)
		opts = tmp.split()
		dev = opts[1]
		type = opts[2]
		if type == 'primary':
			pnum = opts[3]
			pnam = opts[4]
			psze = opts[5]
			ptyp = opts[6]
			self.th_vars.append((pnam, '%s%s' % (dev,pnum)))
		return

	def format_partition(self, txt):
		line = self._chk_subs(txt).split()
		line.pop(0)
		part = line[0]
		line.pop(0)
		type = line[0]
		line.pop(0)
		if len(line) > 0:
			args = ''
			for i in line:
				args = args+i+' '
			t = re.sub('\"', '', args)
			args = t
			if self._which('mkfs.%s' % type) != False:
				print 'mkfs.%s %s %s' % (type, args, part)
		else:
			if self._which('mkswap') != False:
				print 'mkswap %s' % part
		return

	def mount_partition(self, txt):
		print self._chk_subs(txt)
		return

	def fetch_and_extract(self, txt):
		tmp = self._chk_subs(txt)
		uri = tmp.split()[1]
		archive = uri.split('/')[len(uri.split('/'))-1]
		try: lcation = tmp.split()[2]
		except: lcation = './'
		if archive[0] == '%':
			archive_t = self._chk_subs(archive)
			archive = archive_t
		if lcation[0] == '%':
			lcation_t = self._chk_subs(lcation)
			lcation = lcation_t
		if archive[-2:] == 'z2': args = '-jxf'
		if archive[-2:] == 'gz': args = '-zxf'
		print 'wget -c %s' % uri
		print 'tar %s %s -C %s' % (args, archive, lcation)
		return

	def exec_command(self, txt):
		line = self._chk_subs(txt)
		print '/bin/sh -c %s' % line[13:]
		return

	def chroot_command(self, txt):
		tmp = self._chk_subs(txt)
		chroot = tmp.split()[1]
		line = tmp.split()
		line.pop(0)
		line.pop(0)
		script = ''
		for i in line: script = script+i+' '
		print 'echo %s > %s/chroot.sh' % (script, chroot)
		print 'chmod +x %s/chroot.sh' % chroot
		print 'chroot %s ./chroot.sh' % chroot
		return

	def _chk_subs(self, txt):
		key = ''
		retv = ''
		for i in txt.split():
			if i[0] == '%':
				key = i[1:]	
				for a in self.th_vars:
					if key == a[0]:
						 retv = retv+a[1]+' '
			else:
				retv = retv+i+' '
		return retv
	
	def _which(self, prog):
		for path in os.getenv('PATH').split(':'):
			for file in os.listdir(path):
				if file == prog:
					return os.path.join(path, file) 
		return False


if __name__ == '__main__':
	o = Thunder('/etc/install.th')
