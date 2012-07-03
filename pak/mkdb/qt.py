#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2011, 2012, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

# cl8, 9, 10 [Exp]

# required perl in PATH for syncqt
# required DXSDK and MSSDK

descriptorName = 'qt'
descriptorVersion = '4-8-1'
descriptorVersionDot = descriptorVersion.replace('-', '.')
qtRootDir = 'qt-everywhere-opensource-src-{0}'.format(descriptorVersionDot)

#
import os
from os.path import join

def myVCCmd( cmd, execCmdInVCCmdPrompt = execCmdInVCCmdPrompt ):
	return lambda : execCmdInVCCmdPrompt(cmd)

absRootBuildDir = join( buildDirectory, descriptorName + descriptorVersion )

if CCVersionNumber not in [8, 9, 10]:
	print >>sys.stderr, "Wrong MSVC version. Version 8.0[Exp], 9.0[Exp] or 10.0[Exp] required."
	exit(1)

def getQMakePlatform( ccVersionNumber ):
	"""Helper for mkpak."""

	qmakeGenerator = {
		8	: 'win32-msvc2005',
		9	: 'win32-msvc2008',
		10	: 'win32-msvc2010' }
	return qmakeGenerator[ccVersionNumber]

currentPlatform = getQMakePlatform( CCVersionNumber )

#
if 'DXSDK_DIR' not in os.environ:
	print >>sys.stderr, "DXSDK_DIR environment variable not available. Install DirectX SDK."
	exit(1)
DXSDKDir = os.environ['DXSDK_DIR']

#
MSSDKDir = r'C:\Program Files (x86)\Microsoft SDKs\Windows\v7.0A'

#
if 'INCLUDE' not in os.environ:	os.environ['INCLUDE'] = ''
os.environ['INCLUDE'] += ';"{0}"'.format(	join( DXSDKDir, 'Include' ) )
if 'PATH' not in os.environ:	os.environ['PATH'] = ''
os.environ['PATH'] += ';' + join(MSSDKDir, 'Bin') # mt.exe

#os.environ['INCLUDE'] += ';"{0}";"{1}";"{2}"'.format(	join( DXSDKDir, 'Include' ),	# d3d9.h
#														join( MSSDKDir, 'Include' ), 	# vmr9.h, dshow.h
#														join( MSVC, 'Include' ) )

#os.environ['LIB'] += ';' + join( MSSDKDir, 'Lib' ) # strmiids.lib, dmoguids.lib, msdmo.lib

descriptor = {

	'urls':		[ 'http://releases.qt-project.org/qt4/source/{0}.zip'.format(qtRootDir) ],

	'name'			: descriptorName,
	'version'		: descriptorVersion,

	'rootBuildDir'	: qtRootDir,

	'builds'		: [
		myVCCmd('configure -shared -qt-zlib -qt-libpng -qt-libmng -qt-libtiff -qt-libjpeg -nomake examples -nomake demos -nomake docs -debug-and-release -opensource -confirm-license -platform {platform} -mp -prefix {installPath}'.format(platform=currentPlatform, installPath=join(absRootBuildDir, 'install'))),
		myVCCmd('nmake'),
		myVCCmd('nmake install')
		],

	'rootDir'		: 'install',
	'include'		: ['include/*'],
	'lib'			: ['lib/*.lib', 'lib/*.dll', 'lib/*.pdb'],
	'bin'			: ['bin/*.exe'], #'bin/*.dll', 
	'license'		: [	'../{0}/LICENSE.LGPL'.format(qtRootDir),
						'../{0}/LICENSE.FDL'.format(qtRootDir),
						'../{0}/LGPL_EXCEPTION.txt'.format(qtRootDir)]
}

