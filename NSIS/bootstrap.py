#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2009, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

from win32api import *
from win32con import *
import win32gui

import datetime
import logging
import os
import pysvn
import shutil

from Environment import Environment, Paths

# @todo uninstall graphviz setup (new temporary files)
# @todo takes care of PATH for machine (not only PATH for current user).
# @todo Moves functions in sbfUtils.py ?

myDate = str(datetime.datetime.today().strftime("%Y-%m-%d_%Hh%Mm%Ss"))

# @todo function getInstallPath( program, .... ).
# @todo posix version
def getInstallPath( key, subkey = '', text = '' ):
	try:
		regKey = RegOpenKey( HKEY_LOCAL_MACHINE, key )
		value, dataType = RegQueryValueEx( regKey, subkey )
		regKey.Close()
		if len(text) > 0:
			logging.info( '%s is installed in directory : %s' % (text, value) )
			#print ( '%s is installed in directory : %s' % (text, value) )
		return value
	except:
		if len(text) > 0:
			logging.warning( '%s is not installed' % text )
			#print ( '%s is not installed' % text )
		return ''

def getPythonInstallPath():
	return getInstallPath( 'SOFTWARE\\Python\\PythonCore\\2.6\\InstallPath', '', 'Python' )

def getCygwinInstallPath():
	return getInstallPath( 'SOFTWARE\\Cygnus Solutions\\Cygwin\\mounts v2\\/', 'native', 'Cygwin' )

def getSevenZipInstallPath():
	return getInstallPath( 'SOFTWARE\\7-Zip', 'Path', '7-Zip' )

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
			logging.info( 'Directory %s already exists' % directory_normalized )
			#print ( 'Directory %s already exists' % directory_normalized )
			return directory_normalized

#
raw_input('Start execution of SConsBuildFramework bootstrap script. Press return.\n')

logFilename = 'sbf-wininst_%s.log'% myDate
logging.basicConfig(filename=logFilename, level=logging.DEBUG,)
print ("Creates installation log file %s" % logFilename )
print

#
environment = Environment()

# Sets SCONS_BUILD_FRAMEWORK environment variable
logging.info('\n------ Sets SCONS_BUILD_FRAMEWORK environment variable')
print ('\n------ Sets SCONS_BUILD_FRAMEWORK environment variable')
#print
sbf_root = environment.get( 'SCONS_BUILD_FRAMEWORK' )
#print

if sbf_root == None or len(sbf_root) == 0 :
	sbf_root = r'D:\\Dev\\bin\\SConsBuildFramework'
else:
	sbf_root = os.path.normpath( os.path.expandvars( os.path.abspath(sbf_root) ) )
	sbf_root = sbf_root.replace( '\\', '\\\\' )

# sbf_root defined
print
sbf_root = directoryInput( 'SCONS_BUILD_FRAMEWORK root directory ? ', sbf_root )
sbf_root = os.path.normpath( os.path.expandvars( os.path.abspath(sbf_root) ) )

#print
environment.set( 'SCONS_BUILD_FRAMEWORK', sbf_root )
SCONS_BUILD_FRAMEWORK	= environment.get( 'SCONS_BUILD_FRAMEWORK', False ) # = sbf_root DEBUG
print

# Check out the current version of the sbf project
logging.info('\n------ svn checkout')
print ('\n------ svn checkout')
print

def svnCheckoutSBF( destination ):
	cwdSaved = os.getcwd()
	os.chdir( destination )

	client = pysvn.Client()
	client.set_interactive( True )
	client.exception_style = 1
	try:
		logging.info( 'Retrieves sbf from http://sbf.googlecode.com/svn/trunk/ in %s' % destination )
		print ( 'Retrieves sbf from http://sbf.googlecode.com/svn/trunk/ in %s' % destination )
		client.checkout( 'http://sbf.googlecode.com/svn/trunk/', '.' )
		return True
	except pysvn.ClientError, e :
		logging.error(e.args[0], '\n')
		print e.args[0], '\n'
		return False
	finally:
		os.chdir( cwdSaved )

# @todo improves this test => isUnderSvn()
if os.path.exists( os.path.join(SCONS_BUILD_FRAMEWORK, 'sbfMain.py' ) ):
	logging.info( 'SConsBuildFramework is already checkout in %s ' % SCONS_BUILD_FRAMEWORK )
	print ( 'SConsBuildFramework is already checkout in %s ' % SCONS_BUILD_FRAMEWORK )
else:
	svnCheckoutSBF( SCONS_BUILD_FRAMEWORK )
print

# $SCONS_BUILD_FRAMEWORK\SConsBuildFramework.options
logging.info('\n------ Writes the main configuration file (SConsBuildFramework.options)')
print ('\n------ Writes the main configuration file (SConsBuildFramework.options)')
print
SConsBuildFramework_optionsString = """numJobs = %s
pakPaths = [ 'V:\\Dev\\localExt_win32_cl9-0' ]

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
	backup = 'SConsBuildFramework.options_' + myDate + '.backup.txt'
	logging.info( 'Backups SConsBuildFramework.options into %s' % backup )
	print( 'Backups SConsBuildFramework.options into %s' % backup )
	shutil.copyfile( sbf_options, os.path.join( SCONS_BUILD_FRAMEWORK, backup ) )


# @todo Asks numJobs
numJobs			= os.getenv('NUMBER_OF_PROCESSORS')	#@todo non win32 and non existence for NUM_OF_PROC
print
sbfLocalPath	= directoryInput( 'sbf local directory ? ', r'd:\\local' )
print
sbfTmpPath		= directoryInput( 'sbf tmp directory ? ', r'd:\\tmp\\sbf\\build' )

print
with open( sbf_options, 'w' ) as file :
	logging.info( 'Writes %s' % sbf_options )
	print ( 'Writes %s' % sbf_options )
	tmp = SConsBuildFramework_optionsString % (numJobs, sbfLocalPath, sbfTmpPath)
	file.write( tmp.replace( '\\', '\\\\' ) )				# @todo non win32
print

# Gets PATH, saves path.txt and updates PATH
logging.info('\n------ Updates PATH')
print ('\n------ Updates PATH')
print

# gets
PATH = environment.get( 'PATH' )
#print

# backups PATH environment variable
backup = os.path.join( SCONS_BUILD_FRAMEWORK, 'PATH_%s.backup.txt' % myDate )
with open( backup, 'w' ) as file :
	logging.info( 'Backups PATH in %s' % backup )
	print ( 'Backups PATH in %s' % backup )
	file.write( 'PATH=%s' % PATH )
print

# updates
def addToPath( path, paths, addEvenNonExisting = False ):
	if	addEvenNonExisting == False and \
		not os.path.exists(path):
		return False

	if paths.count( path ) == 0 :
		# Adds path to paths
		logging.info( 'Adds %s to PATH' % path )
		print( 'Adds %s to PATH\n' % path )
		paths.append( path )
		return True
	else:
		logging.info( '%s already in PATH' % path )
		#print( '%s already in PATH' % path )
		return False

def removeAllNonExisting( paths ):
	while( True ):
		nonExistingPath = paths.findFirstNonExisting()
		if nonExistingPath == None:
			break
		else:
			logging.info( 'Removes non existing path %s to PATH' % nonExistingPath )
			print( 'Removes non existing path %s to PATH' % nonExistingPath )
			paths.remove( nonExistingPath )

paths = Paths( PATH )

# Cleans PATH
removeAllNonExisting( paths )
print

# Prepends $SCONS_BUILD_FRAMEWORK in PATH for 'scons' file containing scons.bat $*
if paths.count( SCONS_BUILD_FRAMEWORK ) == 0:
	logging.info( 'Adds %s to PATH' % SCONS_BUILD_FRAMEWORK )
	print( 'Adds %s to PATH' % SCONS_BUILD_FRAMEWORK )
	print
	paths.prepend( SCONS_BUILD_FRAMEWORK )
else:
	paths.remove( SCONS_BUILD_FRAMEWORK )
	paths.prepend( SCONS_BUILD_FRAMEWORK )

# Add c:\pythonXY (where c:\pythonXY is the path to your python's installation directory) to your PATH environment variable (See Tips for Vista Users).
# This is important to be able to run the Python executable from any directory in the command line.
pythonInstallPath = getPythonInstallPath()
addToPath( pythonInstallPath, paths )
# Adds C:\PythonXY\Scripts
addToPath( os.path.join(pythonInstallPath, 'Scripts'), paths )
#print

# Adds c:\cygwin\bin to PATH
addToPath( os.path.join(getCygwinInstallPath(), 'bin'), paths )
#print

# @todo Adds TortoiseMerge to PATH

# Adds SevenZip to PATH
addToPath( getSevenZipInstallPath(), paths )
#print

# PATH environment variable installPaths[0]\bin and intallPaths[0]\lib and Ext version
addToPath( os.path.join(sbfLocalPath, 'bin' ), paths, True )
addToPath( os.path.join(sbfLocalPath, 'lib' ), paths, True )
# @todo not very robust to different compiler versions
sbfLocalExtPath = sbfLocalPath + 'Ext_win32_cl9-0Exp'
addToPath( os.path.join(sbfLocalExtPath, 'bin' ), paths, True )
addToPath( os.path.join(sbfLocalExtPath, 'lib' ), paths, True )
#print

# Adds graphviz to PATH
addToPath( os.path.join(getGraphvizInstallPath(), 'bin'), paths )
#print

# Adds doxygen to PATH
addToPath( os.path.join(getDoxygenInstallPath(), 'bin'), paths )
#print

# Adds svn to PATH
addToPath( getCollabNetSubversionClientInstallPath(), paths )
addToPath( getCollabNetSubversionServerInstallPath(), paths )
#print

environment.set( 'PATH', paths.getString() )
print

#
raw_input('Finish execution of SConsBuildFramework bootstrap script. Press return.')
