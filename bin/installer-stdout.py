#!/usr/bin/env python
import os, sys, time
import optparse
from thunder import engine

def showVersion(option, opt_str, value, parser):
	print 'T.H.U.N.D.E.R. v0.2.2'
	print 'Mike "Fuzzy" Partin <fuzzy@thwap.org>'
	print 'http://www.github.com/fuzzyoni/thunder.git/wiki'
	sys.exit()

def main():
	parser.add_option('-s', '--spec', dest="spec", help="Specify the install file to use", metavar="INFILE")
	parser.add_option('-d', '--debug', action="store_true", dest="debug", default=False, help="Turn on DEBUG information")
	parser.add_option('-V', '--version', action='callback', callback=showVersion, help='Show version information')

