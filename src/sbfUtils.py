# SConsBuildFramework - Copyright (C) 2008, 2010, 2011, 2012, 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

import os
import shutil
import sys
import tempfile
import urllib
import urlparse
from os.path import join, exists
from collections import OrderedDict
import subprocess


from sbfEnvironment import Environment
from sbfFiles import *


###### Download funtion ######
def download( url, filename, message = '* Retrieving {} from {}' ):
	def reporthook_urlretrieve( blockCount, blockSize, totalSize ):
		"""Prints report on download advancement"""
		size = blockCount * blockSize / 1024
		print ( '{} kB \r'.format(size) ),

	if message:	print ( message.format( filename, urlparse.urlparse(url).hostname ) )
	urllib.urlretrieve(url, filename, reporthook=reporthook_urlretrieve)
	if message:	print '{} downloaded.                '.format(os.path.basename(filename))

def extractFilenameFromUrl( url ):
	path = urlparse.urlparse(url).path
	return os.path.basename(path)

#def rsearchFilename( path ):
#	if len(path) <= 1:
#		return
#	else:
#		splitted = os.path.split(path)
#		if len(splitext(splitted[1])[1]) > 0:
#			return splitted[1]
#		else:
#			return rsearchFilename( splitted[0] )

###### Functions for print action ######
def printSeparator( text ):
	if len(text)==0:
		print ( '-' * 77 )
	else:
		text = ' ' + text + ' '
		numSep = (78 - len(text))/2
		print ( '-' * numSep + text + '-' * numSep )


def nopAction(target = None, source = None, env = None) :
	return 0

def stringFormatter( lenv, message ) :
	columnWidth	= lenv['outputLineLength']
	retVal = (' ' + message + ' ').center( columnWidth, '-' )
	return retVal


### execute command line ###
def subprocessCall2( command ): # @todo rename subprocessCall2 = subprocessCall
	# Executes commands
	try:
		retcode = subprocess.call( command )
		if retcode < 0:
			print >>sys.stderr, "  Child was terminated by signal", -retcode
			return -retcode
		elif retcode == 0:
			pass
		else:
			print >>sys.stderr, "  Child returned", retcode
			return retcode
	except OSError, e:
		print >>sys.stderr, "  Execution failed:", e
		exit(1)

def subprocessGetOuputCall( cmdLine, verbose = True ):
	"""Executes cmdLine in a subprocess.
	if verbose if True, then message about the command executed and its output is printed.
	@return the output of the executed command"""
	if verbose:
		print ( 'Executing {0}'.format(cmdLine) )
	try:
		output = subprocess.check_output( cmdLine )
		if verbose:
			print output
		return output
	except subprocess.CalledProcessError, e:
		print >>sys.stderr, "Execution failed:", e, '\n'
		exit(e.returncode)
	except OSError, e:
		print >>sys.stderr, "Execution failed:", e, '\n'
		exit(e.errno)


def execute( commandAndParams, commandPath = None ):
	"""Executes commandAndParams = [command, parameter0, ..., parameterX] in commandPath directory if given.
		Returns the output of the command."""

	# Computes args argument of Popen()
	if commandPath:
		argsForPopen = [join(commandPath, commandAndParams[0])]
		for elt in commandAndParams[1:]:
			argsForPopen.append(elt)
	else:
		argsForPopen = commandAndParams

	# Executes command
	pipe = subprocess.Popen( args=argsForPopen, shell=False, bufsize=0, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
	pipe.wait()

	# Retrieves stdout or stderr
	lines = pipe.stdout.readlines()
	if len(lines) == 0 :
		lines = pipe.stderr.readlines()
		if len(lines) == 0:
			return "No output"

	for line in lines:
		line = line.strip()
		if len(line) > 0:
			return line

def call( commandAndParams, commandPath = None, env={} ):
	"""	Executes commandAndParams = [command, parameter0, ..., parameterX] in commandPath directory if given.
		@env the environment variables for the new process
		Returns the return code of the command."""

	# Computes args argument of Popen()
	if commandPath:
		argsForPopen = [join(commandPath, commandAndParams[0])]
		for elt in commandAndParams[1:]:
			argsForPopen.append(elt)
	else:
		argsForPopen = commandAndParams

	# Executes command
	retVal = subprocess.call( args=argsForPopen, cwd=commandPath, env=env )

	return retVal


def executeCommandInVCCommandPrompt( command, appendExit = True, vcvarsPath = None, arch = 'x86-32' ):
	"""	@param vcvarsPath
		@param arch	see SConsBuildFramework.myArch"""

	if not vcvarsPath:
		# Microsoft Visual Studio 2012 x86 tools.
		vcvarsPath = 'C:\\Program Files (x86)\\Microsoft Visual Studio 11.0\\VC\\vcvarsall.bat'

	# Reads batch file to set environment for using Microsoft Visual Studio 20xx x86 tools.
	if not exists(vcvarsPath):
		print ("vcvarsall.bat not found in '{0}'.".format(vcvarsPath))
		return 1

	# Creates a copy of .bat and patches it
	with open(vcvarsPath) as file:
		setupVCLines = file.readlines()

	for (i, line) in enumerate(setupVCLines):
		line = line.replace('%~dp0bin', join(dirname(vcvarsPath), 'bin'))
		line = line.replace('goto :eof', 'goto :myeof')
		setupVCLines[i] = line

	# Appends command
	setupVCLines.append( ':myeof\n' )
	setupVCLines.append( '@set TMP=\n' )
	setupVCLines.append( '@set TEMP=\n' )
	setupVCLines.append( '@set tmp=\n' )
	setupVCLines.append( '@set temp=\n' )
	setupVCLines.append( '@call {0}\n'.format(command) )
	if appendExit:
		setupVCLines.append( '@exit\n'.format(command) )

	# Writes patched vcvars.bat
	with tempfile.NamedTemporaryFile(suffix='.bat', delete=False) as file:
		file.writelines( setupVCLines )

	# Architecture parameter given to vcvarsall.bat
	if arch == 'x86-32':
		vcvarsArchParam = 'x86'
	elif arch == 'x86-64':
		vcvarsArchParam = 'x86_amd64'
	print '{comspec} /k ""{vcvarsbat}"" {archParam}'.format( comspec=os.environ['COMSPEC'], vcvarsbat=file.name, archParam=vcvarsArchParam)
	# Executing command
	retVal = subprocessCall2( '{comspec} /k ""{vcvarsbat}"" {archParam}'.format( comspec=os.environ['COMSPEC'], vcvarsbat=file.name, archParam=vcvarsArchParam) )

	# Cleaning
	os.remove(file.name)

	return retVal


def getLambdaForExecuteCommandInVCCommandPrompt( vcvarsPath, arch ):
	return lambda command, appendExit=True : executeCommandInVCCommandPrompt(command, appendExit, vcvarsPath, arch)


# Helpers to construct a SConsBuildFramework project on filesystem
def getSConsBuildFrameworkDefaultOptions( productName, type, version ):
	"""@brief Returns a string containing an SConsBuildFramework project file (default.options)"""
	SConsBuildFrameworkDefaultOptions = """productName	= '{name}'
type			= '{type}'
version		= '{version}'"""

	return SConsBuildFrameworkDefaultOptions.format( name=productName, type=type, version=version )


def createSConsBuildFrameworkProject( projectName, type, version, includeFiles, sourceFiles ):
	# Create a new directory tree for the compilation.
	os.makedirs( projectName )
	includeDir = join(projectName, 'include')
	os.makedirs( includeDir )
	srcDir = join(projectName, 'src')
	os.makedirs( srcDir )

	# Create the SConsBuildFramework project options file
	defaultOptionsString = getSConsBuildFrameworkDefaultOptions(projectName, type, version)
	with open( join(projectName, 'default.options'), 'w') as file:
		file.write( defaultOptionsString )

	# Copy the sconstruct file into the project
	sbfRoot = os.getenv('SCONS_BUILD_FRAMEWORK')
	print sbfRoot
	shutil.copy( join(sbfRoot, 'template/projectTemplate/sconstruct'), projectName )

	# Copy include and source files to the right place.
	copyTree( includeFiles, includeDir, '.' )
	copyTree( sourceFiles, srcDir, '.' )


def buildDebugAndReleaseUsingSConsBuildFramework( path, CCVersion, arch ):
	owd = os.getcwd()
	os.chdir(path)

	# 'buildPath={}/build'.format(os.getcwd())
	cmdLine = ['installPath={}/local'.format(os.getcwd()), 'clVersion={}'.format(CCVersion), 'targetArchitecture={}'.format(arch), 'printCmdLine=full']
	if sys.platform == 'win32':
		sconsExecutable = 'scons.bat'
	else:
		sconsExecutable = 'scons'
	subprocessGetOuputCall([sconsExecutable, 'debug']	+cmdLine)
	subprocessGetOuputCall([sconsExecutable, 'release']	+cmdLine)

	os.chdir(owd)


### Severals helpers ###
def capitalize( str ):
	"""Return a copy of the string with only its first character capitalized. Other characters are left unchanged (unlike python capitalize)"""
	return str[0].upper() + str[1:]


def getPathFromEnv( varname, normalizedPathname = True ):
	"""Return the value of the environment variable varname if it exists, or None.
	The returned path, if any, could be normalized (see getNormalizedPathname())
	A warning is printed if the environment variable does'nt exist or if the environment variable refers to an non existing path."""

	# Retrieves environment variable
	#path = os.getenv( varname )
	path = Environment().get(varname, False)

	# Error cases
	if not path :
		print "sbfWarning: %s is not defined." % varname
		return None

	if not exists( path ) :
		print "sbfWarning: %s is defined, but its value '%s' is not a valid path." % (varname, path)
		return None

	# Normalized path name
	if normalizedPathname :
		path = getNormalizedPathname( path )

	return path


def getFromEnv( varname, returnEmptyStringIfNotExist = False ):
	"""	@return If returnEmptyStringIfNotExist is false, the value of the environment variable varname if it exists or None.
		If returnEmptyStringIfNotExist is true, the value of the environment variable varname if it exists or an empty string."""

	value = Environment().get(varname, False)

	if returnEmptyStringIfNotExist:
		if value:
			return value
		else:
			return ''
	else:
		return value


def removePathHead( param ):
	"""
	'me' => ''
	'home/me' => 'me'
	['home/me', 'home/you'] => ['me', 'you']"""

	def _removePathHead( path ):
		splitted = path.split(os.sep,1)
		if len(splitted)>1:
			return splitted[1]
		else:
			return ''

	if isinstance( param, str ):
		return _removePathHead( param )
	else:
		retVal = []
		for path in param:
			newPath = _removePathHead(path)
			if newPath:
				retVal.append( newPath )
			#else: do nothing
		return retVal


### Splits the given string to obtain a list of values ###
def convertToList( givenStr ) :
	if isinstance(givenStr, str):
		if givenStr.find(',') == -1 :
			# no ','
			# The words are separated by arbitrary strings of whitespace characters
			return givenStr.split()
		else:
			# ','
			# The words are comma-separated
			return givenStr.replace(' ', '').split(',')
	else:
		return givenStr

### Constructs a string from a list or a set ###
def convertToString( list ) :
	result = ' '
	for element in list :
		result += element + ' '

	return result

### Constructs a string from a dictionary ###
def convertDictToString( dict ) :
	result = ''

	sortedKey = sorted(dict.keys())
	for key in sortedKey :
		result += "%s=%s " % (key, dict[key])
# Random order version
#	for key, value in dict.iteritems() :
#		result += "%s=%s " % (key, value)
	return result


def getSwapDict( iDict ):
	"""Returns a new dictionnary with each element (key, value) swapped (value, key)"""
	oDict = OrderedDict()
	for (key, value) in iDict.iteritems():
		oDict[value] = key
	return oDict


def getDictPythonCode( dict, dictName, orderedDict = False, eol = False, addImport = True ):
	"""@return list of string containing python code building the given dictionary"""
	# Computing the maximum length of the keys
	maxLength = 0;
	for key in dict.iterkeys():
		maxLength = max(maxLength, len(key))
	if orderedDict:
		if addImport:
			retVal = ['from collections import OrderedDict', '{0} = OrderedDict()'.format(dictName)]
		else:
			retVal = ['{0} = OrderedDict()'.format(dictName)]
	else:
		retVal = ['{0} = {{}}'.format(dictName)]
	for (key, value) in dict.iteritems():
		tmp = "{0}['{1}']".format(dictName, key).ljust(maxLength+len(dictName)+5)
		if isinstance(value, list):
			tmp += "= {0}".format(value)
			retVal.append( tmp )
		else:
			tmp += "= '{0}'".format(value)
			retVal.append( tmp )
	if eol:
		retVal = [ elt + '\n' for elt in retVal ]
	return retVal

