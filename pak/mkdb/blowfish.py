#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2010, 2011, 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

# ok for cl9.0, 10.0 and 11.0 (32/64 bits) and posix

# http://www.codeproject.com/KB/security/blowfish.aspx

import os
import sys
from os.path import join

# Version components definition
versionMajor = 1
versionMinor = 0
versionMaint = 0

# Package name
descriptorName = 'blowfish'
descriptorVersion = '{}-{}'.format( versionMajor, versionMinor )
projectFolderName = ''

myLocalExtDirectory = 'local_{}'.format(platform_arch_ccVersion)

if platform == 'win':
	lib = [ join(myLocalExtDirectory, 'bin', '*.lib') ]
elif platform == 'posix':
	lib = [ join(myLocalExtDirectory, 'bin', '*.a') ]
else:
	print >>sys.stderr, 'Unsupported platform {}.'.format(platform)


descriptor = {
	'urls'			: ['http://orange/files/Dev/localExt/PUBLIC/src/' + file for file in ['Blowfish.zip', 'Blowfish_PATCH.zip']],

	'name'			: descriptorName,
	'version'		: descriptorVersion,

	'builds'		: [
		CreateSConsBuildFrameworkProject( descriptorName, 'static', descriptorVersion, ['Blowfish.h'], ['BlowFish.cpp'] ),
		BuildDebugAndReleaseUsingSConsBuildFramework( descriptorName, clVersion, arch ) ],

	# packages developer and runtime
	'rootDir'		: descriptorName,

	# developer package
	'license'		: [join('..', 'COPYING')],
	'include'		: ['include/Blowfish.h'],
	'lib'			: lib,
}
