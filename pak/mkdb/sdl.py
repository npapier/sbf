#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2010, 2011, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

# ok for cl9.0 and 10.0

from os.path import join

# http://www.libsdl.org

descriptorName = 'sdl'
descriptorVersion = '1-2-14'
projectFolderName = 'SDL-1.2.14'

if CCVersionNumber >= 9:
	sln = join( buildDirectory, descriptorName + descriptorVersion, projectFolderName, 'VisualC', 'SDL.sln' )
	cmdDebug = "\"{0}\" {1} /build Debug /out outDebug.txt".format(MSVSIDE, sln)
	cmdRelease = "\"{0}\" {1} /build Release /out outRelease.txt".format(MSVSIDE, sln)
else:
	print >>sys.stderr, "Unsupported MSVC version."
	exit(1)

descriptor = {
	'urls'			: ['http://www.libsdl.org/release/SDL-1.2.14.zip', 'http://orange/files/Dev/localExt/src/SDL-1.2.14_{0}_PATCH.zip'.format(CCVersion) ],

	'name'			: descriptorName,
	'version'		: descriptorVersion,

	'rootBuildDir'	: projectFolderName,
	'builds'		: [	cmdDebug, cmdRelease ],

	'rootDir'		: projectFolderName,
	'license'		: ['README-SDL.txt', 'COPYING'],
	'include'		: ['include/'],
	'lib'			: [	'VisualC/SDL/Release/SDL.lib', 'VisualC/SDL/Release/SDL.dll', 'VisualC/SDLmain/Release/SDLmain.lib' ]
}

#descriptor = {
#	'urls'			: ['http://www.libsdl.org/release/SDL-devel-1.2.14-VC8.zip'],

#	'name'			: 'sdl',
#	'version'		: '1-2-14',

#	'rootDir'		: 'SDL-1.2.14',
#	'license'		: ['README-SDL.txt', 'COPYING'],
#	'include'		: ['include/'],
#	'lib'			: ['lib/*.dll', 'lib/*.lib']
#}
