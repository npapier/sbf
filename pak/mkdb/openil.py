#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2009, 2010, 2011, 2013, 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

# cl8.0, cl9.0, cl10.0 and cl11.0[Exp]
# gcc

# http://openil.sourceforge.net/

from os.path import join

descriptorName = 'openil'
descriptorVersion = '1-7-8'
descriptorVersionDot = descriptorVersion.replace('-', '.')
projetFolderName = 'devil-{}'.format(descriptorVersionDot)

if platform == 'win':
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
	elif CCVersionNumber in [9,10,11]: 
		sln = os.path.join( absRootBuildDir, 'msvc{0}'.format(int(CCVersionNumber)), 'ImageLib.sln' )
		cmdRelease = "\"{0}\" {1} /build Release /out outRelease.txt".format(MSVSIDE, sln)
		descriptor = {
		 'urls'			: ['http://downloads.sourceforge.net/openil/DevIL-1.7.8.zip', 'http://orange/files/Dev/localExt/src/openil1-7-8_LibCompiled-vc9.zip', 'http://orange/files/Dev/localExt/src/openil1-7-8_PATCH.zip'],

		 'rootBuildDir'	: projetFolderName,
		 'builds'		: [ cmdRelease ],

		 'name'			: descriptorName,
		 'version'		: descriptorVersion,

		 # packages developer and runtime
		 'rootDir'		: projetFolderName,

		 # developer package
		 'license'		: ['COPYING'],
		 'include'		: [('include/IL/','IL/')],
		 'lib'			: [ join(libPath, '*.lib') ],

		# runtime package
		'bin'				: [ join(libPath, '*.dll') ]
		}
	else:
		print >>sys.stderr, "Wrong MSVC version. Version 8.0[Exp], 9.0[Exp], 10.0[Exp] or 11.0[Exp] required."
		exit(1)
else:
	# @todo requirements
	print ('Requirements: automake, autoconf, libtool, shtool and texinfo')

	descriptor = {
		'urls'			: ['https://github.com/DentonW/DevIL/archive/master.zip'],

		 'rootBuildDir'	: 'DevIL-master/DevIL',
		 'builds'		: ['autoreconf -i'] + GetAutoconfBuildingCommands('"LIBS=-lm -lz -lIL" --enable-ILU --prefix=`pwd`/../../install'),
		 # LIBS=-lm -lz -lIL: Here to pass -lIL when linking ilur

		 'name'			: descriptorName,
		 'version'		: descriptorVersion,

		 # packages developer and runtime
		 'rootDir'	: 'DevIL-master/DevIL',

		 # developer package
		 'license'		: ['COPYING'],
		 'include'		: [('../../install/include/IL/','IL/')],

		# runtime package
		'bin'				: [ join('../../install/lib/*.so*') ]
	}
