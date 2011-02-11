# SConsBuildFramework - Copyright (C) 2008, 2010, 2011, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

import os
from os.path import join, exists
import subprocess


from sbfFiles import *



def capitalize( str ):
	"""Return a copy of the string with only its first character capitalized. Other characters are left unchanged (unlike python capitalize)"""
	return str[0].upper() + str[1:]



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


###### Return the value of the environment variable varname if it exists, or None ######
# The returned path, if any, could be normalized (see getNormalizedPathname())
# A warning is printed if the environment variable does'nt exist or if the environment variable refers to an non existing path.
def getPathFromEnv( varname, normalizedPathname = True ) :
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
