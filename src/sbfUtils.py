# SConsBuildFramework - Copyright (C) 2008, 2010, 2011, 2012, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

import os
import sys
import tempfile
from os.path import join, exists
import subprocess


from sbfEnvironment import Environment
from sbfFiles import *



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
def subprocessCall2( command ):
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
	except CalledProcessError, e:
		print >>sys.stderr, "Execution failed:", e
		exit(e.returncode)
	except OSError, e:
		print >>sys.stderr, "Execution failed:", e
		exit(e.returncode)


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


def executeCommandInVCCommandPrompt( command, appendExit = True, vcvarsPath = None ):
	if not vcvarsPath:
		# Microsoft Visual Studio 2010 x86 tools.
		vcvarsPath = 'C:\\Program Files (x86)\\Microsoft Visual Studio 10.0\\VC\\bin\\vcvars32.bat'

	# Reads batch file to set environment for using Microsoft Visual Studio 20xx x86 tools.
	if not exists(vcvarsPath):
		print ("vcvars32.bat not found in '{0}'.".format(vcvarsPath))
		return 1

	with open(vcvarsPath) as file:
		setupVCLines = file.readlines()

	# Appends command
	setupVCLines.append( 'call {0}\n'.format(command) )
	if appendExit:
		setupVCLines.append( 'exit\n'.format(command) )

	# Writes patched vcvars.bat
	with tempfile.NamedTemporaryFile(suffix='.bat', delete=False) as file:
		file.writelines( setupVCLines )

	# Executing command
	retVal = subprocessCall2( '{comspec} /k ""{vcvarsbat}""'.format( comspec=os.environ['COMSPEC'], vcvarsbat=file.name ) )

	# Cleaning
	os.remove(file.name)

	return retVal


def getLambdaForExecuteCommandInVCCommandPrompt( vcvarsPath ):
	return lambda command, appendExit=True : executeCommandInVCCommandPrompt(command, appendExit, vcvarsPath)


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

