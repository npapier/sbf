#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2009, 2010, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

# @todo posix version of Environment

from win32api import *
from win32con import *
import win32gui

import logging
import os



class IEnvironment:
	"""Abstract class for manipulating environment variable."""
	def get( self, varname, output = True ) :
		pass

	def set( seld, varname, value, output = True ) :
		pass

	# @todo isDefined()=> True, False



# @todo not always HKEY_CURRENT_USER => HKEY_LOCAL_MACHINE
class Environment( IEnvironment ):
	"""Windows version of IEnvironment"""

	# Returns the value of the environment variable varname if it exists.
	def get( self, varname, output = True ) :
		try:
			keyPath = r'Environment'
			regKey = RegOpenKey( HKEY_CURRENT_USER, keyPath )
			value, dataType = RegQueryValueEx( regKey, varname )
			regKey.Close()
			if output :
				logging.info( 'Current %s is : %s' % (varname, value) )
				#print 'Current %s is : %s' % (varname, value)
			return value
		except:
			if output :
				logging.info( 'No %s' % varname )
				print 'No %s' % varname
			return None

	# Sets the environment variable named varname to the string value
	def set( self, varname, value, output = True ) :
		keyPath = r'Environment'
		regKey = RegOpenKey( HKEY_CURRENT_USER, keyPath, 0, KEY_SET_VALUE )
		RegSetValueEx( regKey, varname, 0, REG_SZ, value )
		regKey.Close()
		if output :
			logging.info( 'Set %s in registry to : %s ' % (varname, value) )
			#print ( 'Set %s in registry to : %s ' % (varname, value) )

		logging.info( 'Broadcasting settings change message...' )
		#print 'Broadcasting settings change message...'
		win32gui.SendMessageTimeout( HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment", 0, 1000 )
