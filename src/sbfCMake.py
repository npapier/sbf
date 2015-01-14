# SConsBuildFramework - Copyright (C) 2011, 2013, 2014, 2015, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

# @todo see mkdb/gtest.py for def createCMakeInitialCacheFile( directory ):

def getCMakeCmdConfigure( CC, CCVersionNumber, arch, options, CMakeListsPath = 'CMakeLists.txt' ):
	"""Helper for mkpak."""

	gccCommandLine = 'cmake -G "{generator}" {options} {CMakeList}'

	if CC == 'cl':
		cmakeGenerator = {
		8	: 'Visual Studio 8 2005',
		9	: 'Visual Studio 9 2008',
		10	: 'Visual Studio 10',
		11	: 'Visual Studio 11',
		12	: 'Visual Studio 12'
		}
		if CCVersionNumber in cmakeGenerator:
			desiredGenerator = cmakeGenerator[CCVersionNumber]
			if arch == 'x86-64':	desiredGenerator += ' Win64'
			return 'cmake -G "{generator}" {options} {CMakeList}'.format( generator=desiredGenerator, options=options, CMakeList = CMakeListsPath )
		else:
			print ('Given unsupported MSVC version {}. \nVersion 8.0[Exp], 9.0[Exp], 10.0[Exp], 11.0[Exp] or 12.0[Exp] required.'.format(ccVersionNumber))
			exit(1)
	elif CC == 'gcc':
		return gccCommandLine.format( generator='Unix Makefiles', options=options, CMakeList = CMakeListsPath )
	elif CC == 'emcc':
		# emscripten support only static library
		options = ' -DBUILD_SHARED_LIBS=OFF ' + options
		# Custom toolchain description file for CMake
		# It teaches CMake about the Emscripten compiler, so that CMake can generate makefiles
		# from CMakeLists.txt that invoke emcc.
		options = ' -DCMAKE_TOOLCHAIN_FILE="%EMSCRIPTEN%/cmake/Modules/Platform/Emscripten.cmake" ' + options
		# @todo -G "Unix Makefiles" (Linux and OSX)
		# -G "MinGW Makefiles" (Windows)
		return 'emcmake ' + gccCommandLine.format( generator='MinGW Makefiles', options=options, CMakeList = CMakeListsPath )
	else:
		print ("Given compiler '{}' not yet supported.".format(CC))
		exit(1)


def getCMakeCmdBuildDebug( buildir = '.' ):
	"""Helper for mkpak."""
	cmdDebug = 'cmake --build {} --config debug'.format(buildir)
	return cmdDebug

def getCMakeCmdBuildRelease( buildir = '.' ):
	"""Helper for mkpak."""
	cmdRelease = 'cmake --build {} --config release'.format(buildir)
	return cmdRelease
