#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2010, 2011, 2013, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier
# Author Maxime Peresson

# cl8,9,10,11,12[Exp]

descriptorName = 'gtest'
descriptorVersion = '446'

from src.sbfCMake import getCMakeCmdConfigure, getCMakeCmdBuildDebug, getCMakeCmdBuildRelease

options = ' -D BUILD_SHARED_LIBS:BOOL=ON -D CMAKE_DEBUG_POSTFIX=-d '
cmakeInitialCacheOption = ' -C "../CMakeInitialCache.txt" '

# CMakeInitialCache.txt
def createCMakeInitialCacheFile( directory ):
	def _createCMakeInitialCacheFile( directory ):
		str = """message("Input: CMAKE_CXX_FLAGS=${CMAKE_CXX_FLAGS}")

if (CMAKE_CXX_FLAGS)
	message("Customizing CMAKE_CXX_FLAGS")

	# add new flags
	set (FLAGS "${CMAKE_CXX_FLAGS} /D _VARIADIC_MAX=10 ")

	set(CMAKE_CXX_FLAGS "${FLAGS}" CACHE STRING "" FORCE)
	message("Output:CMAKE_CXX_FLAGS=${CMAKE_CXX_FLAGS}")
else()
	message("Don't customize CMAKE_CXX_FLAGS")
endif()
"""
		with open( join(directory, 'CMakeInitialCache.txt'), 'w' ) as f:
			f.write(str)
	return lambda : _createCMakeInitialCacheFile(directory)

descriptor = {
 'svnUrl'		: 'http://googletest.googlecode.com/svn/trunk@{0}'.format(descriptorVersion),

 'name'			: descriptorName,
 'version'		: descriptorVersion,

 'rootBuildDir'	: descriptorName,
 'builds'		: [ createCMakeInitialCacheFile(join( buildDirectory, descriptorName + descriptorVersion )),
					getCMakeCmdConfigure(CCVersionNumber, options ),
					getCMakeCmdConfigure(CCVersionNumber, options + cmakeInitialCacheOption ),
					getCMakeCmdBuildDebug(), getCMakeCmdBuildRelease() ],

 'rootDir'		: descriptorName,

 # developer package
 'license'		: ['COPYING', 'CONTRIBUTORS'],
 'include'		: [	'include/' ],
 'lib'			: [	'release/gtest.lib', 'release/gtest.pdb',
					'debug/gtest-d.lib', 'debug/gtest-d.pdb' ],

 # runtime package (release version)
 'binR'			: [	'release/gtest.dll' ],

 # runtime package (debug version)
 'binD'			: [	'debug/gtest-d.dll' ]
 }
 