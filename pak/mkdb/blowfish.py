# SConsBuildFramework - Copyright (C) 2010, 2011, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

# ok for cl9.0 and 10.0

from os.path import join

# http://www.codeproject.com/KB/security/blowfish.aspx

descriptorName = 'blowfish'
descriptorVersion = '1-0'
projectFolderName = ''

if CCVersionNumber >= 9:
	sln = join( buildDirectory, descriptorName + descriptorVersion, 'Blowfish.sln' )
	cmdDebug = "\"{0}\" {1} /build Debug /out outDebug.txt".format(MSVSIDE, sln)
	cmdRelease = "\"{0}\" {1} /build Release /out outRelease.txt".format(MSVSIDE, sln)
else:
	print >>sys.stderr, "Unsupported MSVC version."
	exit(1)

descriptor = {
	'urls'			: ['http://orange/files/Dev/localExt/src/Blowfish.zip', 'http://orange/files/Dev/localExt/src/Blowfish_{0}_PATCH.zip'.format(CCVersion) ],

	'name'			: descriptorName,
	'version'		: descriptorVersion,

	'rootBuildDir'	: projectFolderName,
	'builds'		: [ cmdDebug, cmdRelease ],

	'rootDir'		: projectFolderName,
	'license'		: ['COPYING'],
	'include'		: ['Blowfish.h'],
	'lib'			: [ ('Release/Blowfish.lib', 'Blowfish.lib'), ('Debug/Blowfish.lib', 'Blowfish_D.lib') ]
}
