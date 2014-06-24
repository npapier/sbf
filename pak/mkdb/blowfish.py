# SConsBuildFramework - Copyright (C) 2010, 2011, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

# ok for cl9.0 and 10.0

from os.path import join
import sys

# http://www.codeproject.com/KB/security/blowfish.aspx

descriptorName = 'blowfish'
descriptorVersion = '1-0'
projectFolderName = ''


if platform == 'win32':
	if CCVersionNumber >= 9:
		sln = join( buildDirectory, descriptorName + descriptorVersion, 'Blowfish.sln' )
		patchList = [ 'http://orange/files/Dev/localExt/src/Blowfish_{0}_PATCH.zip'.format(CCVersion) ]
		cmd = [
			# Release build command
			"\"{0}\" {1} /build Debug /out outDebug.txt".format(MSVSIDE, sln),
			# Debug build command
			 "\"{0}\" {1} /build Release /out outRelease.txt".format(MSVSIDE, sln) ]
		lib = [ ('Release/Blowfish.lib', 'Blowfish.lib'), ('Debug/Blowfish.lib', 'Blowfish_D.lib') ]
		binR = []
		binD = []
	else:
		print >>sys.stderr, "Unsupported MSVC version."
		exit(1)
elif platform == 'posix':
	patchList = [ 'http://orange/files/Dev/localExt/src/Blowfish_{0}_PATCH.zip'.format(CCVersion) ]
	cmd = [ 'g++ --shared -o libBlowfish.so BlowFish.cpp' ]
	lib = []
	binR = [ 'libBlowfish.so' ]
	binD = []
else:
	print >>sys.stderr, 'Unsupported platform {0}.'.format(platform)
	exit(1)
	
	
descriptor = {
	'urls'			: ['http://orange/files/Dev/localExt/src/Blowfish.zip'] + patchList,

	'name'			: descriptorName,
	'version'		: descriptorVersion,
	'license'		: ['COPYING'],

	'rootBuildDir'	: projectFolderName,
	'builds'		: cmd,

	'rootDir'		: projectFolderName,
	'license'		: ['COPYING'],
	'include'		: ['Blowfish.h'],
	'lib'			: lib,
	'binR'			: binR,
	'binD'			: binD,
}
