#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2010, 2011, 2013, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

# ok for cl 9.0, 10.0 and 11.0

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

if CCVersionNumber >= 10:
	patchFile = 'http://orange/files/Dev/localExt/src/SDL-1.2.14_{0}_PATCH.zip'.format('cl10-0Exp')
else:
	patchFile = 'http://orange/files/Dev/localExt/src/SDL-1.2.14_{0}_PATCH.zip'.format(CCVersion)

descriptor = {
	'urls'			: ['http://www.libsdl.org/release/SDL-1.2.14.zip', patchFile ],

	'name'			: descriptorName,
	'version'		: descriptorVersion,

	'rootBuildDir'	: projectFolderName,
	'builds'		: [	cmdDebug, cmdRelease ],

	# packages developer and runtime
	'rootDir'		: projectFolderName,

	# developer package
	'license'		: ['README-SDL.txt', 'COPYING'],
	'include'		: ['include/'],
	'lib'			: [	'VisualC/SDL/Release/SDL.lib', 'VisualC/SDLmain/Release/SDLmain.lib' ],

	# runtime package
	'bin'				: ['VisualC/SDL/Release/SDL.dll'],
	#'runtimeCustom'	: [],

	# runtime package (release version)
	#'binR'			: [],
	#'runtimeCustomR'	: [],

	# runtime package (debug version)
	#'binD'			: [],
	#'runtimeCustomD'	: [],
}
