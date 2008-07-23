#!/usr/bin/env python
from distutils.core import setup
setup(name='thunder',
      version='0.2.1',
      py_modules=['thunder/__init__', 'thunder/slurp', 'thunder/net', 'thunder/engine'],
	  data_files=[('/sbin/', ['bin/installer.py']), ('/etc', ['etc/install.th'])]
      )

