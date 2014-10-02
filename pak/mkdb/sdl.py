#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2010, 2011, 2013, 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

# ok for cl 9.0, 10.0 and 11.0 (32/64 bits) and gcc

# http://www.libsdl.org

from os.path import join


descriptorName = 'sdl'
descriptorVersion = '1-2-15'
#descriptorVersion = '2-0-3'
descriptorVersionDot = descriptorVersion.replace('-', '.')

if descriptorVersion == '1-2-15':
	urls = [	'http://www.libsdl.org/release/SDL-{}.tar.gz'.format(descriptorVersionDot), '$SRCPAKPATH/SDL-1.2.15_patch.zip']
	projectFolderName = 'SDL-{}'.format(descriptorVersionDot)
else:
	urls = [	'http://www.libsdl.org/release/SDL2-{}.tar.gz'.format(descriptorVersionDot)]
	projectFolderName = 'SDL2-{}'.format(descriptorVersionDot)

license = ['README-SDL.txt', 'COPYING']

if platform == 'win':
	ConfigureVisualStudioVersion(CCVersionNumber)

	slnPath = 'VisualC'
	vcxprojFiles = []
	if arch == 'x86-32':
		targetPlatform = 'Win32'
		lib =  [ 'VisualC/Release/SDL.lib', 'VisualC/SDLmain/Release/SDLmain.lib' ]
		dxguidPath = '$(DXSDK_DIR)/Lib/x86'
	else:
		targetPlatform = 'x64'
		lib = [ 'VisualC/x64/Release/SDL.lib', 'VisualC/SDLmain/x64/Release/SDLmain.lib' ]
		dxguidPath = '$(DXSDK_DIR)/Lib/x64'

	cmdSDLRelease = GetMSBuildCommand( slnPath, 'SDL.sln', 'SDL', 'Release', maxcpucount = cpuCount, platform = targetPlatform )
	cmdSDLMainRelease = GetMSBuildCommand( slnPath, 'SDL.sln', 'SDLmain', 'Release', maxcpucount = cpuCount, platform = targetPlatform )

	builds =	[	# Fixes vcproj files
				SearchVcxproj(vcxprojFiles, slnPath),
				# Adds <AdditionalLibraryDirectories>dxguidPath</AdditionalLibraryDirectories>
# @todo helper in sbfPackagingSystem.py
				Patcher(vcxprojFiles, [('^(.*\<Link\>.*)$', '\\1\n      <AdditionalLibraryDirectories>{}</AdditionalLibraryDirectories>'.format(dxguidPath))]),
				#	Configures which version of cl have to be invoke.
				MSVC['SetPlatformToolset']( vcxprojFiles, CCVersionNumber ),
				# build
				cmdSDLRelease, cmdSDLMainRelease ]
	rootDir = projectFolderName
	bin = ['VisualC/SDL/Release/SDL.dll']
else:
	builds = GetAutoconfBuildingCommands("`pwd`/install")

	rootDir = join(projectFolderName, 'install')
	license = [ '../{}'.format(file) for file in license]
	lib = []
	bin = ['lib/*.so.*']


descriptor = {
	'urls'			: urls,

	'name'			: descriptorName,
	'version'		: descriptorVersion,

	'rootBuildDir'	: projectFolderName,
	'builds'		: builds,

	# packages developer and runtime
	'rootDir'		: rootDir,

	# developer package
	'license'		: license,
	'include'		: ['include/'],		# @todo when update to 2.0 use on linux AND windows include/SDL/*
	'lib'			: lib,

	# runtime package
	'bin'			: bin,
}
