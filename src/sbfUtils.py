# SConsBuildFramework - Copyright (C) 2008, 2010, 2011, 2012, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

import os
from os.path import join, exists
import subprocess


from sbfFiles import *



### execute command line ###
def subprocessCall( cmdLine, verbose = True ):
	"""Executes cmdLine in a subprocess.
	if verbose if True, then message about the command executed and its output is printed.
	@return the output of the executed command"""
	if verbose:
		print ( 'Executing {0}'.format(cmdLine) )
	try:
		output = subprocess.check_output( cmdLine, shell=True )
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



### Severals helpers ###
def capitalize( str ):
	"""Return a copy of the string with only its first character capitalized. Other characters are left unchanged (unlike python capitalize)"""
	return str[0].upper() + str[1:]


def getPathFromEnv( varname, normalizedPathname = True ) :
	"""Return the value of the environment variable varname if it exists, or None.
	The returned path, if any, could be normalized (see getNormalizedPathname())
	A warning is printed if the environment variable does'nt exist or if the environment variable refers to an non existing path."""
	# Retrieves environment variable
	path = os.getenv( varname )

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
