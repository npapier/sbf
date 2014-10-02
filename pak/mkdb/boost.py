#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2009, 2010, 2011, 2012, 2013, 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

# cl8-0Exp, cl9-0Exp, cl10-0Exp, cl11-0Exp and cl12-0Exp (32/64 bits)
# gcc

# look at http://stackoverflow.com/questions/2629421/how-to-use-boost-in-visual-studio-2010 for full (i.e. all modules) boost build

# http://www.zlib.net/ for zlib
# http://www.bzip.org/ for bzip2

# configuration
versionMajor = 1
versionMinor = 56
versionMaintenance = 0

descriptorName = 'boost'

descriptorVersion = '{major}-{minor}-{maintenance}'.format( major=versionMajor, minor=versionMinor, maintenance=versionMaintenance )
versionPostfix = '{}.{}.{}'.format(versionMajor, versionMinor, versionMaintenance)

absRootBuildDir = join(buildDirectory, descriptorName + descriptorVersion )
rootBuildDir = 'boost_{major}_{minor}_{maintenance}'.format( major=versionMajor, minor=versionMinor, maintenance=versionMaintenance )

def myVCCmd( cmd, execCmdInVCCmdPrompt = execCmdInVCCmdPrompt ):
	return lambda : execCmdInVCCmdPrompt(cmd)

cmd = 'bjam -j {}'.format( cpuCount )
cmd += ' --toolset={} threading=multi link=shared runtime-link=shared stage'
cmd += ' -s ZLIB_SOURCE={0}/zlib-1.2.8 -s BZIP2_SOURCE={0}/bzip2-1.0.6 '.format( absRootBuildDir )

if platform == 'win':
	if arch == 'x86-64':
		cmd += ' address-model=64 --without-python' # @todo enable python support (Python 64 needed)
	# else: pass

	builds_cl = {	8  : cmd.format('msvc-8.0express'),
			9  : cmd.format('msvc-9.0express'),
			10 : cmd.format('msvc-10.0express'),
			11 : cmd.format('msvc-11.0express'),
			12 : cmd.format('msvc-12.0express'),
			}
	if CCVersionNumber not in builds_cl:
		print ('Compiler cl version {} is not yet supported.'.format(CCVersionNumber))
		exit(1)
	build = [ myVCCmd('bootstrap'), myVCCmd(builds_cl[CCVersionNumber]) ]
	libD = ['stage/lib/*-mt-gd-1_*.lib']
	libR = ['stage/lib/*-mt-1_*.lib']
	sharedD = ['stage/lib/*-mt-gd-1_*.dll']
	sharedR = ['stage/lib/*-mt-1_*.dll']
else:
	# @todo debug version
	cmd = './' + cmd.format('gcc') + 'variant={}'
	build = ['./bootstrap.sh', cmd.format('release')] # cmd.format('debug')
	libD = []
	libR = ['stage/lib/*.a']
	sharedD = []
	sharedR = ['stage/lib/*.so.{}'.format(versionPostfix), 'stage/lib/*.so']

descriptor = {
 'urls'			: [	'http://sourceforge.net/projects/boost/files/boost/{major}.{minor}.{maintenance}/boost_{major}_{minor}_{maintenance}.tar.bz2/download'.format( major=versionMajor, minor=versionMinor, maintenance=versionMaintenance ),
				'http://zlib.net/zlib-1.2.8.tar.gz', 'http://www.bzip.org/1.0.6/bzip2-1.0.6.tar.gz' ],

 'name'			: descriptorName,
 'version'		: descriptorVersion,

 #
 'rootBuildDir'		: rootBuildDir,
 'builds'		: build,

 #
 'rootDir'		: 'boost_{major}_{minor}_{maintenance}'.format( major=versionMajor, minor=versionMinor, maintenance=versionMaintenance ),

 # developer package
 'license'		: ['LICENSE_1_0.txt'],
 'include'		: [('boost', 'boost/')],
 'lib'			: libD + libR,

 # runtime package (release version)
 'binR'			: sharedR,

 # runtime package (debug version)
 'binD'			: sharedD,
}

