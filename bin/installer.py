#!/usr/bin/env python
import os, sys, re
from thunder import slurp

class Thunder:
	def __init__(self, file):
		self.slurp = slurp.Proc()
		self.th_vars = []
		self.partitions = {} 
		self.host_commands = []
		self.chroot_commands = []
		self.slurp.register_trigger(args={'t_pattern': '^set.*', 't_callback': self.set})
		self.slurp.register_trigger(args={'t_pattern': '^detect-disks.*', 't_callback': self.detect_disks})
		self.slurp.register_trigger(args={'t_pattern': '^clear-partitions.*', 't_callback': self.clear_partitions})
		self.slurp.register_trigger(args={'t_pattern': '^partition-disk.*', 't_callback': self.partition_disk})
		self.slurp.register_trigger(args={'t_pattern': '^commit-partitions.*', 't_callback': self.commit_partitions})
		self.slurp.register_trigger(args={'t_pattern': '^format-partition.*', 't_callback': self.format_partition})
		self.slurp.register_trigger(args={'t_pattern': '^mount-partition.*', 't_callback': self.mount_partition})
		self.slurp.register_trigger(args={'t_pattern': '^swapon.*', 't_callback': self.swapon})
		self.slurp.register_trigger(args={'t_pattern': '^fetch-and-extract.*', 't_callback': self.fetch_and_extract})
		self.slurp.register_trigger(args={'t_pattern': '^exec-command.*', 't_callback': self.exec_command})
		self.slurp.register_trigger(args={'t_pattern': '^exec-batch.*', 't_callback': self.exec_batch})
		self.slurp.register_trigger(args={'t_pattern': '^chroot-command.*', 't_callback': self.chroot_command})
		self.slurp.register_trigger(args={'t_pattern': '^chroot-batch.*', 't_callback': self.chroot_batch})
		fp = open(file, 'r')
		self.slurp.run(fp)

	def set(self, txt):
		tmp = txt.split()
		self.th_vars.append((tmp[1], tmp[2]))
		return
	
	def detect_disks(self, txt):
		sys.stdout.write('Detecting disks: ')
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
				sys.stdout.write(b+' ')
				self.disks.append(b)
		cnt=0
		for i in self.disks:
			self.th_vars.append(('drive%d' % cnt, '/dev/%s' % i))
			self.partitions[i] = []
			cnt += 1
		print ''
		return self.disks

	def clear_partitions(self, txt):
		sys.stdout.write('[ ] Clearing partitions\r')
		sys.stdout.flush()
		tmp = self._chk_subs(txt)
		line = tmp.split()
		disk = line[1]
		self._exec_cmd('dd if=/dev/zero of=%s bs=512K count=1' % disk)
		sys.stdout.write('[X] Clearing partitions\n')
		sys.stdout.write('[ ] Adding partitions: ')
		return

	def partition_disk(self, txt):
		tmp = self._chk_subs(txt)
		opts = tmp.split()
		dev = opts[1]
		type = opts[2]
		if type == 'primary' or type == 'logical':
			pnum = opts[3]
			pnam = opts[4]
			if opts[5] != 'all': psze = opts[5]
			if opts[5] == 'all': psze = ''
			ptyp = opts[6]
			sys.stdout.write('%s%s ' % (dev,pnum))
			self.th_vars.append((pnam, '%s%s' % (dev,pnum)))
			self.partitions[os.path.basename(dev)].append(',%s,%s' % (psze,ptyp))
		elif type == 'extended':
			if opts[3] != 'all': psze = opts[3]
			else: psze = ''
			sys.stdout.write('swap ')
			self.partitions[os.path.basename(dev)].append(',%s,E' % psze)
		return

	def commit_partitions(self, txt):
		fp = open('/tmp/partitions', 'w+')
		for i in self.partitions.keys():
			for b in self.partitions[i]:
				fp.write(b+'\n')
		fp.close()
		self._exec_cmd('cat /tmp/partitions | /sbin/sfdisk -uM /dev/hda')
		sys.stdout.write('\r[X]')
		print ''
		return

	def format_partition(self, txt):
		line = self._chk_subs(txt).split()
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
				cmd = 'mkfs.%s -L %s %s %s' % (type, labl, args, part)
		else:
			if self._which('mkswap') != False:
				cmd = 'mkswap -L %s %s' % (labl, part)
		sys.stdout.write('[ ] Formatting %s as %s\r' % (part,type))
		sys.stdout.flush()
		self._exec_cmd(cmd)
		sys.stdout.write('\r[X]\n')
		return

	def mount_partition(self, txt):
		line = self._chk_subs(txt).split()
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
					cmd = 'mkdir %s && sleep 1' % line[1]
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
				cmd = 'mkdir %s && sleep 1' % where
		sys.stdout.write('[ ] Mounting %s on %s' % (who, where))
		self._exec_cmd(cmd)
		sys.stdout.write('\r[X]')
		print ''
		return

	def swapon(self, txt):
		tmp = self._chk_subs(txt).split()
		tmp.pop(0)
		for i in tmp:
			if self._which('swapon') != False:
				cmd = 'swapon %s' % i
				sys.stdout.write('[ ] Activating swap on %s' % i)
				self._exec_cmd(cmd)
				sys.stdout.write('\r[X]\n')
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
		sys.stdout.write('[ ] Fetching %s' % os.path.basename(uri))
		self._exec_cmd('wget -c %s' % uri)
		sys.stdout.write('\r[X]\n')
		sys.stdout.write('[ ] Extracting into %s' % lcation)
		self._exec_cmd('tar %s %s -C %s' % (args, archive, lcation))
		sys.stdout.write('\r[X]\n')
		return

	def exec_command(self, txt):
		line = self._chk_subs(txt)
		self.host_commands.append('/bin/bash -c %s' % line[13:])
		return

	def exec_batch(self, txt):
		sys.stdout.write('[ ] Running commands')
		fp = open('/tmp/commands.sh', 'w+')
		for i in self.host_commands:
			fp.write(re.sub('"', '\\\"', i)+'\n')
		self._exec_cmd('cat /tmp/commands.sh | /bin/bash')
		sys.stdout.write('\r[X] Executed script, it was hopefully successful, I didn\'t check.\n')
		self.host_commands = []
		return

	def chroot_command(self, txt):
		tmp = self._chk_subs(txt)
		line = tmp.split()
		line.pop(0)
		script = ''
		for i in line: script = script+i+' '
		self.chroot_commands.append(script)
		return

	def chroot_batch(self, txt):
		tmp = self._chk_subs(txt)
		chroot = tmp.split()[1]
		sys.stdout.write('[ ] Executing commands in chroot.')
		fp = open('%s/chroot-commands.sh' % chroot, 'w+')
		fp.write('#!/bin/bash\n')
		for i in self.chroot_commands:
			fp.write(i+'\n')
		self._exec_cmd('chmod +x %s/chroot-commands.sh' % chroot)
		self._exec_cmd('chroot %s ./chroot-commands.sh' % chroot)
		sys.stdout.write('\r[X]\n')
		self.chroot_commands = []
		return

	def _exec_cmd(self, cmd):
		os.system('%s &>/tmp/%s.log' % (cmd, cmd.split()[0]))
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
			if os.path.isdir(path):
				for file in os.listdir(path):
					if file == prog:
						return os.path.join(path, file) 
		return False


if __name__ == '__main__':
	o = Thunder('/etc/install.th')
