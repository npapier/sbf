#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2009, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

from __future__ import with_statement

from win32api import *
from win32con import *
import win32gui

import os
import pysvn
import shutil

from Environment import Environment, Paths

# @todo Improves output
# @todo takes care of PATH for machine (not only PATH for current user).
# @todo Moves functions in sbfUtils.py ?

# @todo function getInstallPath( program, .... ).
# @todo no win32 version
def getInstallPath( key, subkey = '', text = '' ):
	try:
		regKey = RegOpenKey( HKEY_LOCAL_MACHINE, key )
		value, dataType = RegQueryValueEx( regKey, subkey )
		regKey.Close()
		if len(text) > 0:
			print ( '%s is installed in directory : %s' % (text, value) )
		return value
	except:
		if len(text) > 0:
			print ( '%s is not installed' % text )
		return ''

def getPythonInstallPath():
	return getInstallPath( 'SOFTWARE\\Python\\PythonCore\\2.5\\InstallPath', '', 'Python' )

def getCygwinInstallPath():
	return getInstallPath( 'SOFTWARE\\Cygnus Solutions\\Cygwin\\mounts v2\\/', 'native', 'Cygwin' )

def getGraphvizInstallPath():
	return getInstallPath( 'SOFTWARE\\ATT\\Graphviz', 'InstallPath', 'Graphviz' )

def getDoxygenInstallPath():
	return getInstallPath( 'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\doxygen_is1', 'InstallLocation', 'doxygen' )

# @todo Uses HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\CollabNet Subversion Client UninstallString, because of version independence
def getCollabNetSubversionClientInstallPath():
	return getInstallPath( 'SOFTWARE\\CollabNet\\Subversion\\1.6.1\\Client', 'Install Location', 'CollabNet svn (client)' )

def getCollabNetSubversionServerInstallPath():
	return getInstallPath( 'SOFTWARE\\CollabNet\\Subversion\\1.6.1\\Server', 'Install Location', 'CollabNet svn (client and server)' )

def directoryInput( text, defaultValue ):
	while( True ):
		directory = raw_input( text + defaultValue + ' ' )
		if len(directory) == 0:
			directory = defaultValue
		directory_normalized = os.path.normpath( os.path.expandvars( directory ) )
		if not os.path.exists(directory_normalized):
			answer = raw_input('Creates directory %s\n no or the default choice (y)es ?'% directory_normalized )
			if answer in ['y', '']:
				os.makedirs( directory_normalized )
				return directory_normalized
			else:
				continue
		else:
			print ( 'Directory %s already exists' % directory_normalized )		# ????????? improves message
			return directory_normalized

#
raw_input('Start execution of SConsBuildFramework bootstrap. Press return.\n')

# @todo FIXME
# startFrom (NSIS $INSTDIR)
#startFrom = os.getcwd()
#print "DEBUG:startFrom", startFrom
#print

#
environment = Environment()

# Sets SCONS_BUILD_FRAMEWORK environment variable
print ('------ Sets SCONS_BUILD_FRAMEWORK environment variable')
sbf_root = environment.get( 'SCONS_BUILD_FRAMEWORK' )

if sbf_root == None or len(sbf_root) == 0 :
	sbf_root = 'D:\\Dev\\bin\\SConsBuildFramework'
sbf_root = os.path.normpath( os.path.expandvars( os.path.abspath(sbf_root) ) )

# sbf_root defined
sbf_root = directoryInput( 'SCONS_BUILD_FRAMEWORK root directory ? ', sbf_root )
sbf_root = os.path.normpath( os.path.expandvars( os.path.abspath(sbf_root) ) )

environment.set( 'SCONS_BUILD_FRAMEWORK', sbf_root )
SCONS_BUILD_FRAMEWORK	= environment.get( 'SCONS_BUILD_FRAMEWORK', False ) # = sbf_root DEBUG
print

# Check out the current version of the sbf project
print ('------ svn checkout')
def svnCheckoutSBF( destination ):
	cwdSaved = os.getcwd()
	os.chdir( destination )

	client = pysvn.Client()
	client.set_interactive( True )
	client.exception_style = 1
	try:
		print ( 'Checkout with svn http://sbf.googlecode.com/svn/trunk/ in %s' % destination )
		client.checkout( 'http://sbf.googlecode.com/svn/trunk/', '.' )
		return True
	except pysvn.ClientError, e :
		print e.args[0], '\n'
		return False
	finally:
		os.chdir( cwdSaved )

# @todo improves this test => isUnderSvn()
if os.path.exists( os.path.join(SCONS_BUILD_FRAMEWORK, 'sbfMain.py' ) ):
	print ( 'SConsBuildFramework is already checkout in %s ' % SCONS_BUILD_FRAMEWORK )
else:
	svnCheckoutSBF( SCONS_BUILD_FRAMEWORK )
print

# $SCONS_BUILD_FRAMEWORK\SConsBuildFramework.options
print ('------ Writes the main configuration file (SConsBuildFramework.options)')
SConsBuildFramework_optionsString = """numJobs = %s
pakPaths = [ 'V:\\Dev\\localExt_win32_cl8-0', 'V:\\Dev\\localExt_win32_cl8-0\\pending' ]

#svnUrls = { '' : ['http://svn.gna.org/svn/gle', 'http://svn.gna.org/svn'] } for ULIS (vgsdk 0-4 from gna)

#svnUrls = { 'glContext'	: 'http://oglpp.googlecode.com/svn/glContext/trunk',
#            'gle'			: 'http://oglpp.googlecode.com/svn/gle/trunk',
#            'glo'			: 'http://oglpp.googlecode.com/svn/glo/trunk',
#            'vgsdk'		: 'http://vgsdk.googlecode.com/svn/branches/0-4' } for ULIS (vgsdk branches/0-4 from googlecode)

#svnUrls = { 'glContext'	: 'http://oglpp.googlecode.com/svn/glContext/trunk',
#            'gle'			: 'http://oglpp.googlecode.com/svn/gle/trunk',
#            'glo'			: 'http://oglpp.googlecode.com/svn/glo/trunk',
#            'vgsdk'		: 'http://vgsdk.googlecode.com/svn/trunk' }

# to authenticate check out the source code using your login: [ 'svn+ssh://login@orange/srv/svn/lib', 'svn+ssh://login@orange/srv/svn/bin' ]
# to anonymously check out the source code : [ 'svn://orange/srv/svn/lib', 'svn://orange/srv/svn/bin' ]
svnUrls = { 'glContext'	: 'http://oglpp.googlecode.com/svn/glContext/trunk',
            'gle'		: 'http://oglpp.googlecode.com/svn/gle/trunk',
            'glo'	    : 'http://oglpp.googlecode.com/svn/glo/trunk',
            'vgsdk'		: 'http://vgsdk.googlecode.com/svn/trunk',
            '' : [ 'svn://orange/srv/svn/lib', 'svn://orange/srv/svn/bin', 'svn://orange/srv/svn/share' ] }
weakLocalExtExclude = ['sofa'] # to avoid cleaning projects at each sofa update.
installPaths = ['%s']
buildPath    = '%s'"""

sbf_options = os.path.join( SCONS_BUILD_FRAMEWORK, 'SConsBuildFramework.options' )

if os.path.exists( sbf_options ):
	print( 'Backups SConsBuildFramework.options into SConsBuildFramework.optionsORI' )
	shutil.copyfile( sbf_options, os.path.join( SCONS_BUILD_FRAMEWORK, 'SConsBuildFramework.optionsORI' ) )

# @todo Asks numJobs
numJobs			= os.getenv('NUMBER_OF_PROCESSORS')	#@todo no win32 and non existence for NUM_OF_PROC
sbfLocalPath	= directoryInput( 'sbf local directory ? ', 'd:\\local' )
sbfTmpPath		= directoryInput( 'sbf tmp directory ? ', 'd:\\tmp\\sbf\\build' )

with open( sbf_options, 'w' ) as file :
	print ( 'Writes %s' % sbf_options )
	tmp = SConsBuildFramework_optionsString % (numJobs, sbfLocalPath, sbfTmpPath)
	file.write( tmp.replace( '\\', '\\\\' ) )				# @todo non win32
print

# Gets PATH, saves path.txt and updates PATH
print ('------ Updates PATH')
# gets
PATH = environment.get( 'PATH' )

# saves
with open( 'path.txt', 'w' ) as file :
	print ( 'Backup PATH in path.txt' )
	file.write( 'PATH=\n%s' % PATH )

# updates
def addToPath( path, paths ):
	if not os.path.exists(path):
		return False

	if paths.count( path ) == 0 :
		# Adds path to paths
		print( 'Adds %s to PATH' % path )
		paths.append( path )
		return True
	else:
		print( '%s already in PATH' % path )
		return False

paths = Paths( PATH )

# try $SCONS_BUILD_FRAMEWORK in PATH => scons and sbfPak (@todo FIXME scons fox linux)
if paths.count( SCONS_BUILD_FRAMEWORK ) == 0:
	print( 'Adds %s to PATH' % SCONS_BUILD_FRAMEWORK )
	paths.prepend( SCONS_BUILD_FRAMEWORK )
else:
	paths.remove( SCONS_BUILD_FRAMEWORK )
	paths.prepend( SCONS_BUILD_FRAMEWORK )
print

# Add c:\python25 (where c:\python25 is the path to your python's installation directory) to your PATH environment variable (See Tips for Vista Users).
# This is important to be able to run the Python executable from any directory in the command line.
pythonInstallPath = getPythonInstallPath()
addToPath( pythonInstallPath, paths )

# Adds C:\Python25\Scripts
addToPath( os.path.join(pythonInstallPath, 'Scripts'), paths )
print

# Adds c:\cygwin\bin to PATH
addToPath( getCygwinInstallPath(), paths )
print

# PATH environment variable installPaths[0]\bin and intallPaths[0]\lib and Ext version
addToPath( os.path.join(sbfLocalPath, 'bin' ), paths )
addToPath( os.path.join(sbfLocalPath, 'lib' ), paths )

sbfLocalExtPathlocal = sbfLocalPath + 'Ext_win32_cl8-0Exp'					# @todo not very robust
addToPath( os.path.join(sbfLocalExtPathlocal, 'bin' ), paths )
addToPath( os.path.join(sbfLocalExtPathlocal, 'lib' ), paths )
print

# Adds graphviz to PATH
addToPath( os.path.join(getGraphvizInstallPath(), 'bin'), paths )
print

# Adds doxygen to PATH
addToPath( os.path.join(getDoxygenInstallPath(), 'bin'), paths )
print

# Adds svn to PATH
addToPath( getCollabNetSubversionClientInstallPath(), paths )
addToPath( getCollabNetSubversionServerInstallPath(), paths )
print

environment.set( 'PATH', paths.getString() )

#
raw_input('Finish execution of SConsBuildFramework bootstrap. Press return.')
