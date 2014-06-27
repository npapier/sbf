#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2009, 2010, 2011, 2012, 2013, 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

# cl8-0Exp, cl9-0Exp, cl10-0Exp and cl11-0Exp (32/64 bits)
# gcc

# configuration
versionMajor = 1
versionMinor = 54
versionMaintenance = 0

def myVCCmd( cmd, execCmdInVCCmdPrompt = execCmdInVCCmdPrompt ):
	return lambda : execCmdInVCCmdPrompt(cmd)

cmd = 'bjam -j {}'.format( cpuCount )
cmd += ' --toolset={} --build-type=minimal threading=multi link=shared runtime-link=shared stage'

if platform == 'win':
	if arch == 'x86-64':
		cmd += ' address-model=64 --without-python' # @todo enable python support (Python 64 needed)
	# else: pass

	builds_cl = {	8  : cmd.format('msvc-8.0express'),
					9  : cmd.format('msvc-9.0express'),
					10 : cmd.format('msvc-10.0express'),
					11 : cmd.format('msvc-11.0express') }
	build = [ myVCCmd('bootstrap'), myVCCmd(builds_cl[CCVersionNumber]) ]
	libD = ['stage/lib/*-mt-gd-1_*.lib']
	libR = ['stage/lib/*-mt-1_*.lib']
	sharedD = ['stage/lib/*-mt-gd-1_*.dll']
	sharedR = ['stage/lib/*-mt-1_*.dll']
else:
	cmd = './' + cmd
	build = ['./bootstrap.sh',  cmd.format('gcc') ]
	lib = ['stage/lib/*.so', 'stage/lib/*.so.*']

descriptor = {
 'urls'			: [	'http://sourceforge.net/projects/boost/files/boost/{major}.{minor}.{maintenance}/boost_{major}_{minor}_{maintenance}.tar.bz2/download'.format( major=versionMajor, minor=versionMinor, maintenance=versionMaintenance ) ],

 'name'			: 'boost',
 'version'		: '{major}-{minor}-{maintenance}'.format( major=versionMajor, minor=versionMinor, maintenance=versionMaintenance ),

 #
 'rootBuildDir'	: 'boost_{major}_{minor}_{maintenance}'.format( major=versionMajor, minor=versionMinor, maintenance=versionMaintenance ),
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
