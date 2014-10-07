# SConsBuildFramework - Copyright (C) 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

class Use_openil( IUse ):
	def getName( self ):
		return "openil"

	def getVersions( self ):
		return ['1-7-8']


	def getLIBS( self, version ):
		if self.platform == 'win' :
			if self.config == 'release' :
				libs = ['DevIL', 'ILU']
				return libs, libs
			else:
				libs = ['DevIL', 'ILU']
				return libs, libs #['DevILd'] @todo openil should be compiled in debug on win32 platform
		else:
			libs = ['IL', 'ILU']
			return libs, []

	def hasRuntimePackage( self, version ):
		if self.platform == 'win':
			return self.ccVersionNumber >= 9.0000 and version == '1-7-8'
		else:
			return True
