#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2011, 2012, 2013, 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

# cl8, 9, 10 and 11 [Exp] (32/64 bits)

descriptorName = 'qt'
descriptorMajorMinorVersion = '4-8'
descriptorVersion = descriptorMajorMinorVersion + '-5'
descriptorVersionDot = descriptorVersion.replace('-', '.')
qtRootDir = 'qt-everywhere-opensource-src-{0}'.format(descriptorVersionDot)

#
import os
from os.path import join

# Requirements
print ('Requirements :')
print (' * perl in PATH for syncqt')
print (' * required DXSDK and MSSDK')

# qt.conf
def createQtConfFile( directory ):
	def _createQtConfFile( directory ):
		qtConfStr = """[Paths]
Prefix=
Documentation=../doc
Headers=../include
Libraries=../lib
Binaries=
Plugins=plugins
Data=..
Translations=translations
Settings=../etc
Examples=../examples
Demos=../demos
"""
		with open( join(directory, 'qt.conf'), 'w' ) as f:
			f.write(qtConfStr)
	return lambda : _createQtConfFile(directory)

qtConfDirectory = join( buildDirectory, descriptorName + descriptorVersion )

def myVCCmd( cmd, execCmdInVCCmdPrompt = execCmdInVCCmdPrompt ):
	return lambda : execCmdInVCCmdPrompt(cmd)

absRootBuildDir = join( buildDirectory, descriptorName + descriptorVersion )

from src.sbfQt import getQMakePlatform
currentPlatform = getQMakePlatform( CC, CCVersionNumber, arch )

if 'DXSDK_DIR' not in os.environ:
	print >>sys.stderr, "DXSDK_DIR environment variable not available. Install DirectX SDK."
	exit(1)
DXSDKDir = os.environ['DXSDK_DIR']

#if CCVersionNumber == 11.0000:
#	MSSDKDir = r'C:\Program Files (x86)\Microsoft SDKs\Windows\v7.1A'
#elif CCVersionNumber == 10.0000:
#	MSSDKDir = r'C:\Program Files (x86)\Microsoft SDKs\Windows\v7.0A'
#else:
#	assert( False )

#
if 'INCLUDE' in os.environ:
	os.environ['INCLUDE'] = join( DXSDKDir, 'Include' ) + os.pathsep + os.environ['INCLUDE']
else:
	os.environ['INCLUDE'] = join( DXSDKDir, 'Include' )

# mt.exe
#if 'PATH' in os.environ:
#	os.environ['PATH'] = join(MSSDKDir, 'Bin') + os.pathsep + os.environ['PATH']
#else:
#	os.environ['PATH'] = join(MSSDKDir, 'Bin')

#os.environ['INCLUDE'] += ';"{0}";"{1}";"{2}"'.format(	join( DXSDKDir, 'Include' ),	# d3d9.h
#														join( MSSDKDir, 'Include' ), 	# vmr9.h, dshow.h
#														join( MSVC, 'Include' ) )

#os.environ['LIB'] += ';' + join( MSSDKDir, 'Lib' ) # strmiids.lib, dmoguids.lib, msdmo.lib

descriptor = {

	'urls':		[ 'http://download.qt-project.org/official_releases/qt/{0}/{1}/{2}.tar.gz'.format(
		descriptorMajorMinorVersion.replace('-', '.'),
		descriptorVersionDot, 
		qtRootDir ),
		'http://orange/files/Dev/localExt/PUBLIC/src/qt-everywhere-opensource-src-4.8.5_patch.zip'
		],

	'name'			: descriptorName,
	'version'		: descriptorVersion,
#	'buildVersion'	: '-0',

	'rootBuildDir'	: qtRootDir,

	'builds'		: [
		myVCCmd('configure -shared -qt-zlib -qt-libpng -qt-libmng -qt-libtiff -qt-libjpeg -nomake examples -nomake demos -nomake docs -debug-and-release -opensource -confirm-license -platform {platform} -mp -prefix "{installPath}"'.format(platform=currentPlatform, installPath=join(absRootBuildDir, 'install'))),
		myVCCmd('nmake'),
		myVCCmd('nmake install'),
		createQtConfFile(qtConfDirectory)
		],

	# packages developer and runtime
	'rootDir'		: 'install',

	# developer package
	'license'		: [	'../{}/LICENSE.LGPL'.format(qtRootDir),
						'../{}/LICENSE.FDL'.format(qtRootDir),
						'../{}/LGPL_EXCEPTION.txt'.format(qtRootDir)], # @todo other license files ? .LICENSE-DESKTOP and so on
	'include'		: ['include/*'],
	'lib'			: ['lib/*.lib', 'lib/*.pdb'],
	'custom'		: [	('bin/*.exe', 'bin/'),
						(GlobRegEx('lib/[^\.]+(?<!d4)[.]dll$'),	'bin/'), # to match *4.dll without *d4.dll (see 'binR')
						('{}/qt.conf'.format(qtConfDirectory), 'bin/'),
						('mkspecs/*', 'mkspecs/'),
						'q3porting.xml'
						],

	# runtime package
	'bin'				: [	'{}/qt.conf'.format(qtConfDirectory),
							('translations/*', 'translations/') ],

	# runtime package (release version)
	'binR'			: [	GlobRegEx('lib/[^\.]+(?<!d4)[.]dll$'),	# to match *4.dll without *d4.dll
						(GlobRegEx('plugins/.*', pruneFiles='(?![^.]+(?<!d4)[.]dll$)', recursive=True), 'plugins/')
						],

	# runtime package (debug version)
	'binD'			: [	GlobRegEx('lib/[^\.]+(?<=d4)[.]dll$'),	# to match *d4.dll
						(GlobRegEx('plugins/.*', pruneFiles='(?![^.]+(?<=d4)[.](dll|pdb)$)', recursive=True), 'plugins/')
						]
# @todo install/phrasebooks ?
}
