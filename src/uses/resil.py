# SConsBuildFramework - Copyright (C) 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

class Use_resil( IUse ):
	def getName( self ):
		return 'resil'

	def getVersions( self ):
		return ['1-8-2']


	def getLIBS( self, version ):
		if self.platform == 'win' :
			if self.config == 'release' :
				libs = ['ResIL', 'ILU']
				return libs, libs
			else:
				libs = ['ResIL', 'ILU']
				return libs, libs # @todo resil should be compiled in debug on win32 platform
		# else @todo

	def hasRuntimePackage( self, version ):
		if self.platform == 'win' and version == '1-8-2':
			return True
		else:
			return False
