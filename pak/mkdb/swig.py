#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2013, 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

version = '3-0-2'
versionDot = version.replace('-', '.')


if platform == 'win':
	urls		= [ 'http://sourceforge.net/projects/swig/files/swigwin/swigwin-{version}/swigwin-{version}.zip'.format(version=versionDot) ]
	rootBuildDir	= 'swigwin-{version}'.format(version=versionDot)
	builds		= []
	prgName		= 'swig.exe'
elif platform == 'posix':
	urls		= [ 'http://sourceforge.net/projects/swig/files/swig/swig-{version}/swig-{version}.tar.gz'.format(version=versionDot) ]
	rootBuildDir	= 'swig-{version}'.format(version=versionDot)
	builds		= [ './configure', 'make' ]
	prgName		= 'swig'
else:
	print >>sys.stderr, "Platform {} not supported".format(platform)
	exit(1)

descriptor = {
 'urls'			: urls,
 
 'name'			: 'swig',
 'version'		: version,

 # building
 'rootBuildDir'		: rootBuildDir,
 'builds'		: builds,

 # packages developer and runtime
 'rootDir'		: rootBuildDir,

 # developer package 
 'license'		: ['LICENSE', 'LICENSE-GPL', 'LICENSE-UNIVERSITIES'],

 'custom'		: [	(prgName, 'bin/'),
					(GlobRegEx('Lib/.*', pruneFiles='(?!^.*[.](swg|i)$)', recursive=True), 'bin/Lib/') ]
}
