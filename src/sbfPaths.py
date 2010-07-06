#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2009, 2010, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

import os


def getNormalizedPathname( pathname ) :
	return os.path.normpath( os.path.expandvars(os.path.expanduser(pathname)) )

class Paths:
	"""Class to manipulate a sequence of paths"""

# Public interface
	def __init__( self, stringPaths ):
		if	stringPaths == None or\
			len(stringPaths) == 0:
			self.__pathsORI	= ''
			self.__paths	= []
		else:
			self.__pathsORI	= stringPaths
			self.__paths	= stringPaths.split( os.pathsep )

	def dump( self ):
		for element in self.__paths:
			print element

	def count( self, path = '' ):
		if len(path) == 0:
			return len(self.__paths)
		else:
			path_normalized = getNormalizedPathname(path)
			num = 0
			for element in self.__paths:
				element_normalized = getNormalizedPathname(element)
				if element_normalized == path_normalized:
					num += 1
			return num

	# Appends the specified path to the beginning in the path list
	def prepend( self, path ):
		self.__paths.insert(0, path)

	# Appends the specified path to the end in the path list
	def append( self, path ):
		self.__paths.append( path )

	# Removes all occurences of the specified path in the path list
	def remove( self, path ):
		path_normalized = getNormalizedPathname(path)
		indexToDelete = []
		for i, element in enumerate(self.__paths):
			element_normalized = getNormalizedPathname(element)
			if element_normalized == path_normalized:
				indexToDelete.append( i )
		#
		indexToDelete.reverse()
		for index in indexToDelete:
			del self.__paths[index]

	# Searches the first non existing paths
	def findFirstNonExisting( self ):
		for path in self.__paths:
			path_normalized = getNormalizedPathname(path)
			if not os.path.exists( path_normalized ):
				return path

	# Accessors
	def getOriginalString( self ):
		return self.__pathsORI

	def getString( self ):
		if len(self.__paths) == 0:
			return ''
		elif len(self.__paths) == 1:
			return self.__paths[0]
		else: # > 1
			retVal = self.__paths[0]
			for path in self.__paths[1:]:
				retVal += os.pathsep + path
			return retVal

	def getList( self ):
		return self.__paths[:]

	# @todo checks checkDuplicate(self), checkInvalid()

