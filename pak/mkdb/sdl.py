#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2010, 2011, 2013, 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

# ok for cl x.y (32/64 bits) and gcc

# http://www.libsdl.org

from os.path import join
#from src.sbfCMake import getCMakeCmdConfigure, getCMakeCmdBuildDebug, getCMakeCmdBuildRelease

descriptorName = 'sdl'
#descriptorVersion = '1-2-15'
descriptorVersion = '2-0-3'
descriptorVersionDot = descriptorVersion.replace('-', '.')

if descriptorVersion == '1-2-15':
	urls = [	'http://www.libsdl.org/release/SDL-{}.tar.gz'.format(descriptorVersionDot), '$SRCPAKPATH/SDL-1.2.15_patch.zip']
	projectFolderName = 'SDL-{}'.format(descriptorVersionDot)
	license = ['README-SDL.txt', 'COPYING']
else:
	projectFolderName = 'SDL2-{}'.format(descriptorVersionDot)
	urls = ['https://www.libsdl.org/release/SDL2-devel-2.0.3-VC.zip']#['http://www.libsdl.org/release/SDL2-{}.tar.gz'.format(descriptorVersionDot)]
	#('$SRCPAKPATH/headers_angle-es2only-legacy.zip', projectFolderName)]
	license = ['README.txt', 'README-SDL.txt', 'COPYING.txt']

if platform == 'win':
	if descriptorVersion == '1-2-15':
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
		include = ['include/']
	else:
		rootDir = projectFolderName
		builds = []
		include = [('include/', 'SDL2/')]
		if arch == 'x86-32':
			lib = ['lib/x86/SDL2.lib', 'lib/x86/SDL2main.lib']
			bin = ['lib/x86/SDL2.dll']
		elif arch == 'x86-64':
			lib = ['lib/x64/SDL2.lib', 'lib/x64/SDL2main.lib']
			bin = ['lib/x64/SDL2.dll']
		else:
			print ('Architecture {} not yet supported.'.format(arch))
			exit(1)

		# # building with CMake (@todo I was unable to activate VIDEO_OPENGLES         (Wanted: ON): OFF !!!)
		# rootDir = projectFolderName
		# builds = [	#Patcher('CMakeLists.txt', [('^(.*CheckOpenGLESX11().*)$', '#\\1')]),
					# # Patcher('CMakeLists.txt', [('^(if\(\$\{CMAKE_SOURCE_DIR\} STREQUAL \$\{CMAKE_BINARY_DIR\}\))$', 'set(CMAKE_REQUIRED_INCLUDES "${SBF_LOCALEXT}/include")\ninclude_directories(${SBF_LOCALEXT}/include)\n\\1')]),
					# MakeDirectory('../build'), ChangeDirectory('../build'),
					# # 'cmake ../SDL2-2.0.3',
					# getCMakeCmdConfigure(CC, CCVersionNumber, arch, options, CMakeListsPath = '../{}'.format(rootDir) ),
					# # getCMakeCmdBuildDebug(),
					# getCMakeCmdBuildRelease() ]
		# lib = ['release/SDL2.lib']
		# bin = ['release/SDL2.dll']
else:
	builds = GetAutoconfBuildingCommands("`pwd`/install")

	rootDir = join(projectFolderName, 'install')
	license = [ '../{}'.format(file) for file in license]
	lib = []
	bin = ['lib/*.so.*']
	include = ['include/']


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
	'include'		: include,
	'lib'			: lib,

	# runtime package
	'bin'			: bin,
}
