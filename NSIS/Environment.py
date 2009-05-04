#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2009, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

# @todo posix version of Environment 
from win32api import *
from win32con import *
import win32gui

import os

# IEnvironment and co
class IEnvironment:
	def get( self, varname, output = True ) :
		pass

	def set( seld, varname, value, output = True ) :
		pass

	# @todo isDefined()=> True, False

# @todo not always HKEY_CURRENT_USER => HKEY_LOCAL_MACHINE
class Environment( IEnvironment ):
	# Returns the value of the environment variable varname if it exists.
	def get( self, varname, output = True ) :
		try:
			keyPath = r'Environment'
			regKey = RegOpenKey( HKEY_CURRENT_USER, keyPath )
			value, dataType = RegQueryValueEx( regKey, varname )
			regKey.Close()
			if output :
				print 'Current %s is : %s' % (varname, value)
			return value
		except:
			if output :
				print 'No %s' % varname
			return None

	# Sets the environment variable named varname to the string value
	def set( self, varname, value, output = True ) :
		keyPath = r'Environment'
		regKey = RegOpenKey( HKEY_CURRENT_USER, keyPath, 0, KEY_SET_VALUE )
		RegSetValueEx( regKey, varname, 0, REG_SZ, value )
		regKey.Close()
		if output :
			print 'Set %s in registry to : %s ' % (varname, value)

		print 'Broadcasting settings change message...'
		win32gui.SendMessageTimeout( HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment", 0, 1000 )


# Class to manipulate a sequence of paths
class Paths:

	def __getNormalizedPathname( self, pathname ) :
		return os.path.normpath( os.path.expandvars(os.path.expanduser(pathname)) )

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
			path_normalized = self.__getNormalizedPathname(path)
			num = 0
			for element in self.__paths:
				element_normalized = self.__getNormalizedPathname(element)
				if element_normalized == path_normalized:
					num += 1
			return num

	# Appends the specified path to the beginning in the path list
	def prepend( self, path ):
		self.__paths.insert(0, path)

	# Appends the specified path to the end in the path list
	def append( self, path ):
		self.__paths.append( path )

	# Removes the specified path in the path list
	def remove( self, path ):
		path_normalized = self.__getNormalizedPathname(path)
		for i, element in enumerate(self.__paths):
			element_normalized = self.__getNormalizedPathname(element)
			if element_normalized == path_normalized:
				del self.__paths[i]
				return True
		return False

	# Removes all occurences of the specified path in the path list
	# @todo
	# def removeAll( self, path ):

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
