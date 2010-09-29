# SConsBuildFramework - Copyright (C) 2008, 2010, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

import os

from sbfFiles import *



def capitalize( str ):
	"""Return a copy of the string with only its first character capitalized. Other characters are left unchanged (unlike python capitalize)"""
	return str[0].upper() + str[1:]


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

	if not os.path.exists( path ) :
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
