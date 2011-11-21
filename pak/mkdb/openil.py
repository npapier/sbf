#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2009, 2010, 2011, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

# ok for cl8.0Exp, cl9.0Exp, cl10.0Exp

# http://openil.sourceforge.net/

import os.path

descriptorName = 'openil'
descriptorVersion = '1-7-8'
projetFolderName = 'devil-1.7.8'
libPath = 'lib/vc9/x86'

absRootBuildDir = os.path.join( buildDirectory, descriptorName + descriptorVersion, 'devil-1.7.8', 'projects' )

if CCVersionNumber == 8:
	descriptor = {
	 'urls'			: ['http://downloads.sourceforge.net/openil/DevIL-SDK-x86-1.7.8.zip'],

	 'name'			: 'openil',
	 'version'		: '1-7-8',

	 'license'		: ['COPYING'],
	 'include'		: ['include/'],
	 'lib'			: ['lib/*.dll', 'lib/*.lib']
	}
elif CCVersionNumber in [9,10]: 
	sln = os.path.join( absRootBuildDir, 'msvc{0}'.format(int(CCVersionNumber)), 'ImageLib.sln' )
	cmdRelease = "\"{0}\" {1} /build Release /out outRelease.txt".format(MSVSIDE, sln)
	descriptor = {
	 'urls'			: ['http://downloads.sourceforge.net/openil/DevIL-1.7.8.zip', 'http://orange/files/Dev/localExt/src/openil1-7-8_LibCompiled-vc9.zip', 'http://orange/files/Dev/localExt/src/openil1-7-8_PATCH.zip'],

	 'rootBuildDir'	: projetFolderName,
	 'builds'		: [ cmdRelease ],

	 'name'			: descriptorName,
	 'version'		: descriptorVersion,

	 'rootDir'		: projetFolderName,
	 'license'		: ['COPYING'],
	 'include'		: [('include/IL/','IL/')],
	 'lib'			: [ os.path.join(libPath, '*.dll'), os.path.join(libPath, '*.lib') ]
	}
else:
	print >>sys.stderr, "Wrong MSVC version. Version 8.0[Exp], 9.0[Exp] or 10.0[Exp] required."
	exit(1)

