#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2009, 2010, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

# cl8-0Exp, cl9-0Exp, and cl10-0Exp
# gcc

if platform == 'win32':
	msg = 'WARNING: building this package must be done from a Visual Studio Command Prompt'
	print ( '{0}\n{1}\n{0}\n'.format( '-' * len(msg), msg ) )

	builds_cl = {	8  : 'bjam --toolset=msvc-8.0express --build-type=minimal threading=multi link=shared runtime-link=shared stage',
					9  : 'bjam --toolset=msvc-9.0express --build-type=minimal threading=multi link=shared runtime-link=shared stage',
					10 : 'bjam --toolset=msvc-10.0express --build-type=minimal threading=multi link=shared runtime-link=shared stage' }

	build = [ 'bootstrap', builds_cl[CCVersionNumber] ]
	lib = ['stage/lib/*.lib', 'stage/lib/*.dll']
else:
	build = ['./bootstrap.sh',  './bjam --toolset=gcc --build-type=minimal threading=multi link=shared runtime-link=shared stage' ]
	lib = ['stage/lib/*.so', 'stage/lib/*.so.*']

descriptor = {
 'urls'			: [	#"http://sourceforge.net/projects/boost/files/boost-jam/3.1.17/boost-jam-3.1.17-1-ntx86.zip/download",

 					"http://sourceforge.net/projects/boost/files/boost/1.45.0/boost_1_45_0.tar.bz2/download"
 					#"http://sourceforge.net/projects/boost/files/boost/1.43.0/boost_1_43_0.tar.bz2/download"
 					#"http://sourceforge.net/projects/boost/files/boost/1.42.0/boost_1_42_0.tar.bz2/download"
 					#"http://sourceforge.net/projects/boost/files/boost/1.41.0/boost_1_41_0.tar.bz2/download"
 					#"http://sourceforge.net/projects/boost/files/boost/1.40.0/boost_1_40_0.tar.bz2/download"
 					],

 'rootBuildDir'	: 'boost_1_45_0', #'boost_1_43_0', #'boost_1_42_0', #'boost_1_41_0', #'boost_1_40_0',
 'builds'		: build,

 'name'			: 'boost',
 'version'		: '1-45-0', #'1-43-0', #'1-42-0', # '1-41-0', #'1-40-0',

 'rootDir'		: 'boost_1_45_0', #'boost_1_43_0', #'boost_1_42_0', #'boost_1_41_0', #'boost_1_40_0',
 'license'		: ['LICENSE_1_0.txt'],
 'include'		: [('boost', 'boost1-45-0/boost/')],
 #'include'		: [('boost', 'boost1-43-0/boost/')],
 #'include'		: [('boost', 'boost1-42-0/boost/')],
 #'include'		: [('boost', 'boost1-41-0/boost/')],
 #'include'		: [('boost', 'boost1-40-0/boost/')],
 'lib'			: lib
}

# @todo pprint()
# info boost1-45-0_win32_cl9-0Exp.zip mt-gd-1_45
# info boost1-45-0_win32_cl9-0Exp.zip mt-1_45
