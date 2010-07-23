#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2010, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier
# Author Maxime Peresson

# cl9-0Exp

import os.path


if CCVersionNumber == 9: 
	vcexpress = r"C:\Program Files (x86)\Microsoft Visual Studio 9.0\Common7\IDE\VCExpress.exe"
	sbfPath = os.getenv("SCONS_BUILD_FRAMEWORK")
	projetFolderName = 'gtest445'
	sln = os.path.join( sbfPath, 'pak', 'var', 'build', projetFolderName, projetFolderName, 'msvc', 'gtest-md.sln' )
	cmdDebug = "\"{0}\" {1} /build Debug /out outDebug.txt".format(vcexpress, sln)
	cmdRelease = "\"{0}\" {1} /build Release /out outRelease.txt".format(vcexpress, sln)	
	
else:
	print >>sys.stderr, "Wrong MSVC version. Version 9.0Exp Required."
	exit(1)

descriptor = {
 'urls'			: [	"http://orange/files/Dev/localExt/src/gtest445.zip" ],

 'rootBuildDir'	: 'gtest445',
 'builds'		: [	cmdDebug, cmdRelease ],

 'name'			: 'gtest',
 'version'		: '445',

 'rootDir'		: 'gtest445',
 
 'license'		: [('COPYING')],
 
 'include'		: [	'include/' ],

'lib'			: [	'msvc/gtest-md/Release/gtest-md.lib', 
					'msvc/gtest-md/Release/gtest-md.dll',
					'msvc/gtest-md/Debug/gtest-mdd.lib',
					'msvc/gtest-md/Debug/gtest-mdd.dll' ],
}
