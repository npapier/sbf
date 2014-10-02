# SConsBuildFramework - Copyright (C) 2009, 2010, 2011, 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

import logging
import os
import sys


class IEnvironment:
	"""Abstract class for manipulating environment variable.
		@todo isDefined()=> True, False"""

	def get( self, varname, output = True ) :
		pass

	def set( self, varname, value, output = True ) :
		pass


class DefaultEnvironment( IEnvironment ):
	"""Default implementation of IEnvironment class"""
	def get( self, varname, output = True ) :
		value = os.getenv(varname)
		if output:
			if value:
				logging.info('Current %s is : %s' % (varname, value))
				print ('Current %s is : %s' % (varname, value))
			else:
				logging.info('Current %s : -' % varname)
				print ('Current %s : -' % varname)	
		return value


	def set( self, varname, value, output = True ) :
		print( 'DefaultEnvironment::set() not implemented' )


class NoOpEnvironment( IEnvironment ):
	"""Abstract class for manipulating environment variable."""
	def get( self, varname, output = True ) :
		print( 'Environment::get() not implemented' )

	def set( self, varname, value, output = True ) :
		print( 'Environment::set() not implemented' )


### Environment class for windows platform
isPyWin32Available = False
if sys.platform == 'win32':
	try:
		from win32api import *
		from win32con import *
		import win32gui
		isPyWin32Available = True

		class WinEnvironment( IEnvironment ):
			"""	Windows version of IEnvironment
				@todo not always HKEY_CURRENT_USER => HKEY_LOCAL_MACHINE"""

			def get( self, varname, output = True ) :
				"""Returns the value of the environment variable varname if it exists."""
				try:
					keyPath = r'Environment'
					regKey = RegOpenKey( HKEY_CURRENT_USER, keyPath )
					value, dataType = RegQueryValueEx( regKey, varname )
					regKey.Close()
					if output :
						logging.info('Current %s is : %s' % (varname, value))
						print ('Current %s is : %s' % (varname, value))
					return value
				except:
					if output :
						logging.info('Current %s : -' % varname)
						print ('Current %s : -' % varname)
					return None

			def set( self, varname, value, output = True ) :
				"""Sets the environment variable named varname to the string value."""
				keyPath = r'Environment'
				regKey = RegOpenKey( HKEY_CURRENT_USER, keyPath, 0, KEY_SET_VALUE )
				RegSetValueEx( regKey, varname, 0, REG_SZ, value )
				regKey.Close()
				if output :
					logging.info( 'Set %s in registry to : %s ' % (varname, value) )
					print ( 'Set %s in registry to : %s ' % (varname, value) )

				logging.info( 'Broadcasting settings change message...' )
				#print 'Broadcasting settings change message...'
				win32gui.SendMessageTimeout( HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment", 0, 1000 )

	except ImportError as e:
		print ('sbfWarning: pywin32 is not installed (from sbfEnvironment.py).')

	if isPyWin32Available:
		Environment = WinEnvironment
	else:
		Environment = DefaultEnvironment
else:
	Environment = DefaultEnvironment

