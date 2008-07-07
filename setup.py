#!/usr/bin/env python
from distutils.core import setup
setup(name='thunder',
      version='0.1.0',
      py_modules=['thunder/__init__', 'thunder/mslurp', 'thunder,parser'],
	  data_files=[('/sbin/', ['bin/installer.py']), ('/etc', ['etc/install.th'])]
      )

