#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2010, 2011, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier
# Author Maxime Peresson

# cl8,9,10,11[Exp]

descriptorName = 'gtest'
descriptorVersion = '446'

from src.sbfCMake import getCMakeCmdConfigure, getCMakeCmdBuildDebug, getCMakeCmdBuildRelease

if CCVersionNumber in [8, 9, 10, 11]:
	options = '-D BUILD_SHARED_LIBS:BOOL=ON -D CMAKE_DEBUG_POSTFIX=-d'
else:
	print >>sys.stderr, "Wrong MSVC version. Version 8.0[Exp], 9.0[Exp], 10.0[Exp] or 11.0[Exp] required."
	exit(1)

descriptor = {
 'svnUrl'		: 'http://googletest.googlecode.com/svn/trunk@{0}'.format(descriptorVersion),

 'rootBuildDir'	: descriptorName,
 'builds'		: [ getCMakeCmdConfigure(CCVersionNumber, options), getCMakeCmdBuildDebug(), getCMakeCmdBuildRelease() ],

 'name'			: descriptorName,
 'version'		: descriptorVersion,

 'rootDir'		: descriptorName,

 'license'		: ['COPYING', 'CONTRIBUTORS'],

 'include'		: [	'include/' ],

'lib'			: [	'release/gtest.lib', 'release/gtest.pdb', 'release/gtest.dll',
					'debug/gtest-d.lib', 'debug/gtest-d.pdb', 'debug/gtest-d.dll' ]
}
