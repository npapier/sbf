# SConsBuildFramework - Copyright (C) 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

class Use_glew( IUse ):
	def getName( self ):
		return 'glew'

	def getVersions( self ):
		return ['1-9-0', '1-5-1']

	def getLIBS( self, version ):
		libs = ['glew32']
		return libs, libs

	def hasRuntimePackage( self, version ):
		if self.platform == 'win' and self.ccVersionNumber >= 10.0000 and version == '1-9-0':
			return True
		else:
			return False