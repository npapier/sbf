#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2010, 2011, 2013, 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

# ok for cl 9.0, 10.0 and 11.0 (32/64 bits)

from os.path import join

# http://www.libsdl.org

descriptorName = 'sdl'
descriptorVersion = '1-2-15'
descriptorVersionDot = descriptorVersion.replace('-', '.')

projectFolderName = 'SDL-{}'.format(descriptorVersionDot)

slnPath = 'VisualC'

if arch == 'x86-32':
	platform = 'Win32'
	lib =  [ 'VisualC/Release/SDL.lib', 'VisualC/SDLmain/Release/SDLmain.lib' ]
else:
	platform = 'x64'
	lib = [ 'VisualC/x64/Release/SDL.lib', 'VisualC/SDLmain/x64/Release/SDLmain.lib' ]

ConfigureVisualStudioVersion(CCVersionNumber)
cmdSDLRelease = GetMSBuildCommand( slnPath, 'SDL.sln', 'SDL', 'Release', maxcpucount = cpuCount, platform = platform )
cmdSDLMainRelease = GetMSBuildCommand( slnPath, 'SDL.sln', 'SDLmain', 'Release', maxcpucount = cpuCount, platform = platform )

descriptor = {
	'urls'			: [	'http://www.libsdl.org/release/SDL-1.2.15.tar.gz',
						'http://orange/files/Dev/localExt/PUBLIC/src/SDL-1.2.15_patch.zip'
		],

	'name'			: descriptorName,
	'version'		: descriptorVersion,

	'rootBuildDir'	: projectFolderName,
	'builds'		: [ cmdSDLRelease, cmdSDLMainRelease ],

	# packages developer and runtime
	'rootDir'		: projectFolderName,

	# developer package
	'license'		: ['README-SDL.txt', 'COPYING'],
	'include'		: ['include/'],
	'lib'			: lib,

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
