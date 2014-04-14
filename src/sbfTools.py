# SConsBuildFramework - Copyright (C) 2010, 2011, 2012, 2013, Nicolas Papier.
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
import os, sys
from os.path import join, exists
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
		'cmake'			: [r'SOFTWARE\Kitware\CMake {}\\'.format(version) for version in ['2.8.11.2']],
		'cygwin'		: cygwin,
		'cygpath'		: cygwin,
		'doxygen'		: [r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\doxygen_is1\InstallLocation' ],
		'git'			: [r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Git_is1\InstallLocation' ],
		'graphviz'		: [r'SOFTWARE\AT&T Research Labs\Graphviz\InstallPath', r'SOFTWARE\ATT\Graphviz\InstallPath'],
		'gtkmm'			: [r'SOFTWARE\gtkmm\2.4\Path'],
		'nsis'			: [r'SOFTWARE\NSIS\\'],
		'python'		: [r'SOFTWARE\Python\PythonCore\2.7\InstallPath\\', r'SOFTWARE\Python\PythonCore\2.6\InstallPath\\'],
		'rsync'			: cygwin,
		'ssh'			: cygwin,
		'svn'			: [	r'SOFTWARE\CollabNet\Subversion\{0}\Client\Install Location'.format(currentSvnVersion),
							r'SOFTWARE\CollabNet\Subversion\{0}\Server\Install Location'.format(currentSvnVersion) ],
		'swig'			: [],
		'7z'			: [r'SOFTWARE\7-Zip\Path'],
		'tortoisegitmerge'	: [r'SOFTWARE\TortoiseGit\TMergePath'],
		'tortoisesvnmerge'	: [r'SOFTWARE\TortoiseSVN\TMergePath']
	}

	actionMap = {
		'cmake'			: appendBin,
		'cygpath'		: appendBin,
		'doxygen'		: appendBin,
		'git'			: appendBin,
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
	# The following code is similar to location = WhereIs( programName, os.getenv('PATH') )
	for path in os.getenv('PATH').split(os.pathsep):
		if exists( join(path, programName) ):
			return path
	return ''


def locateProgram( programName ):
	# Using registry
	if isPyWin32Available:
		location = locateProgramUsingRegistry( programName.lower() )
		if len(location)>0:
			return location

	# Using PATH
	if sys.platform == "win32" and\
		not programName.endswith(".exe") and\
		not programName.endswith(".bat") :
		location = locateProgramUsingPATH( programName + ".exe" )
		if len(location)>0:
			return location
	else:
		location = locateProgramUsingPATH( programName )
		if len(location)>0:
			return location

	# For program not in registry and not in PATH
	#	graphviz
	if programName == 'graphviz':
		graphvizLocation = r"C:\Program Files (x86)\Graphviz2.36\bin"
		graphvizLocation32 = r"C:\Program Files\Graphviz2.36\bin"

		if exists( graphvizLocation ):		return graphvizLocation
		if exists( graphvizLocation32 ):	return graphvizLocation32

	return ''


def getPathsForTools( verbose = False ):
	"""	Returns a list containing path for cygwin binaries (rsync and ssh) @todo posix,
		7z (for pakupdate, zip* targets),
		nsis (for nsis target),
		graphviz and doxygen (for doxygen target)
	"""

	def _append( paths, program, verbose ):
		location = locateProgram(program)
		if location:
			paths.append( location )
		else:
			if verbose:
				print ('sbfWarning: unable to locate {0}'.format(program))

	paths = []

	#
	cygwinLocation = locateProgram('cygwin')
	if cygwinLocation:
		paths.append( join(cygwinLocation, 'bin') )

	# TortoiseMerge is append to the PATH by installation program

	_append(paths, '7z', verbose )
	_append(paths, 'nsis', verbose )

	_append(paths, 'graphviz', verbose )
	_append(paths, 'doxygen', verbose )

	# paths.append( locateProgram('svn') ) not needed

	return paths


def getPathsForRuntime( sbf ):
	return [	join( sbf.myInstallDirectory, 'bin' ),
				join( sbf.myInstallExtPaths[0], 'bin' ),
				join( sbf.myInstallExtPaths[0], 'lib' ) ]


def prependToPATH( env, newPaths, enableLogging = True ):
	"""env['ENV']['PATH'] = newPaths + env['ENV']['PATH']"""
	for path in reversed(newPaths):
		if enableLogging: print ('Prepends {0} to sbf private PATH'.format(path))
		env.PrependENVPath( 'PATH', path )

def appendToPATH( env, newPaths, enableLogging = True ):
	"""env['ENV']['PATH'] = env['ENV']['PATH'] + newPaths"""
	for path in reversed(newPaths):
		if enableLogging: print ('Appends {0} to sbf private PATH'.format(path))
		env.AppendENVPath( 'PATH', path )
