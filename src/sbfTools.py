# SConsBuildFramework - Copyright (C) 2010, 2011, 2012, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

from sbfUtils import getPathFromEnv

# To be able to use sbfTools.py without SCons
try:
	from SCons.Script import *
except ImportError as e:
	#print ('sbfWarning: unable to import SCons.Script')
	pass

import logging
from os.path import join
import sys
#from sbfFiles import getNormalizedPathname

isPyWin32Available = False

if sys.platform == 'win32':
	try:
		import win32api
		import win32con
		import win32gui
		isPyWin32Available = True

		def _getInstallPath( key = win32con.HKEY_LOCAL_MACHINE, subkey = '', samDesired = win32con.KEY_READ, printedMessage = '', enableLogging = True ):
			"""	SOFTWARE\Python\PythonCore\2.6\InstallPath\\ => default value of SOFTWARE\Python\PythonCore\2.6\InstallPath
				SOFTWARE\7-Zip\Path => Path value of SOFTWARE\7-Zip"""

			p = subkey.rfind('\\')
			mySubkey = subkey[:p]
			myValueName = subkey[p+1:]
			try:
				regKey = win32api.RegOpenKeyEx( key, mySubkey, 0, samDesired )
				value, dataType = win32api.RegQueryValueEx( regKey, myValueName )
				regKey.Close()
				if len(printedMessage) > 0 and enableLogging:
					logging.info( '%s is installed in directory : %s' % (printedMessage, value) )
				return value
			except:
				if len(printedMessage) > 0 and enableLogging:
					logging.warning( '%s is not installed' % printedMessage )
				return ''

		def getInstallPath( key = win32con.HKEY_LOCAL_MACHINE, subkey = '', printedMessage = '', enableLogging = True ):
			"""Calls _getInstallPath() using KEY_WOW64_64KEY to access a 64-bit key from either a 32-bit or 64-bit application, then if needed KEY_WOW64_32KEY
			to access a 32-bit key from either a 32-bit or 64-bit application. See _getInstallPath()."""

			# Access a 64-bit key from either a 32-bit or 64-bit application
			installPath = _getInstallPath( key, subkey, win32con.KEY_READ | win32con.KEY_WOW64_64KEY )
			if len(installPath):	return installPath

			# Access a 32-bit key from either a 32-bit or 64-bit application.
			installPath = _getInstallPath( key, subkey, win32con.KEY_READ | win32con.KEY_WOW64_32KEY )
			return installPath

	except ImportError:
		print ('sbfWarning: pywin32 is not installed (from sbfTools.py).')
		print ('sbfWarning: locating programs using Windows registry is disabled.')

if isPyWin32Available:
	winGetInstallPath = getInstallPath




def appendBin( path ):
	return join( path, 'bin' )
#	return join( getNormalizedPathname(path), 'bin' )

def nop( path ):
	return path
#	return getNormalizedPathname(path)

def locateProgramUsingRegistry( programName ):
	currentSvnVersion = winGetInstallPath(win32con.HKEY_LOCAL_MACHINE, r'SOFTWARE\CollabNet\Subversion\Client Version')
	cygwin = [r'SOFTWARE\Cygwin\setup\rootDir', r'SOFTWARE\Cygnus Solutions\Cygwin\mounts v2\/\native']
	myMap = {
		'cygwin'		: cygwin,
		'cygpath'		: cygwin,
		'doxygen'		: [r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\doxygen_is1\InstallLocation' ],
		'graphviz'		: [r'SOFTWARE\AT&T Research Labs\Graphviz\InstallPath', r'SOFTWARE\ATT\Graphviz\InstallPath'],
		'gtkmm'			: [r'SOFTWARE\gtkmm\2.4\Path'],
		'nsis'			: [r'SOFTWARE\NSIS\\'],
		'python'		: [r'SOFTWARE\Python\PythonCore\2.7\InstallPath\\', r'SOFTWARE\Python\PythonCore\2.6\InstallPath\\'],
		'rsync'			: cygwin,
		'ssh'			: cygwin,
		'svn'			: [	r'SOFTWARE\CollabNet\Subversion\{0}\Client\Install Location'.format(currentSvnVersion),
							r'SOFTWARE\CollabNet\Subversion\{0}\Server\Install Location'.format(currentSvnVersion) ],
		'7z'			: [r'SOFTWARE\7-Zip\Path'],
		'tortoisemerge'	: [r'SOFTWARE\TortoiseSVN\TMergePath']
	}

	actionMap = {
		'cygpath'		: appendBin,
		'doxygen'		: appendBin,
		'graphviz'		: appendBin,
		'rsync'			: appendBin,
		'ssh'			: appendBin
	}

	currentAction = actionMap.get( programName, nop )

	for param in myMap.get(programName, []):
		location = getInstallPath(win32con.HKEY_CURRENT_USER, subkey = param, printedMessage = programName, enableLogging = False)
		if len(location)>0:
			return currentAction(location)
		location = getInstallPath(win32con.HKEY_LOCAL_MACHINE, subkey = param, printedMessage = programName, enableLogging = False)
		if len(location)>0:
			return currentAction(location)
	return ''


def locateProgramUsingPATH( programName ):
	"""Searches programName in PATH environment variable"""
	#location = WhereIs( programName, os.getenv('PATH') )
	location = WhereIs( programName )
	if location:
		return os.path.dirname(location)
	return ''


def locateProgram( programName ):
	# Using registry
	if isPyWin32Available:
		location = locateProgramUsingRegistry( programName.lower() )
		if len(location)>0:
			return location

	# Using PATH
	location = locateProgramUsingPATH( programName )
	if len(location)>0:
		return location

	return ''


def getPathsForTools():
	"""	Returns a list containing path for cygwin binaries (rsync and ssh) @todo posix,
		7z (for zip* targets),
		nsis (for nsis target),
		graphviz and doxygen (for doxygen target)
	"""

	paths = []

	#
	cygwinLocation = locateProgram('cygwin')
	if cygwinLocation:
		paths.append( os.path.join(cygwinLocation, 'bin') )

	# TortoiseMerge is append to the PATH by installation program

	paths.append( locateProgram('7z') )
	paths.append( locateProgram('nsis') )

	paths.append( locateProgram('graphviz') )
	paths.append( locateProgram('doxygen') )

	# paths.append( locateProgram('svn') ) not needed

	return paths


def getPathsForRuntime( sbf ):
	return [	join( sbf.myInstallPaths[0], 'bin' ),
				join( sbf.myInstallPaths[0], 'lib' ),
				join( sbf.myInstallExtPaths[0], 'bin' ),
				join( sbf.myInstallExtPaths[0], 'lib' ) ]


def prependToPATH( env, newPaths, enableLogging = True ):
	"""env['ENV']['PATH'] = newPaths + env['ENV']['PATH']"""
	for path in newPaths:
		if enableLogging: print ('Prepends {0} to sbf private PATH'.format(path))
		env.PrependENVPath( 'PATH', path )

def appendToPATH( env, newPaths, enableLogging = True ):
	"""env['ENV']['PATH'] = env['ENV']['PATH'] + newPaths"""
	for path in newPaths:
		if enableLogging: print ('Appends {0} to sbf private PATH'.format(path))
		env.AppendENVPath( 'PATH', path )
