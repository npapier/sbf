# SConsBuildFramework - Copyright (C) 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

class Use_glut( IUse ):
	def getName(self ):
		return 'glut'

	def getVersions( self ):
		return ['3-7']

	def getLIBS( self, version ):
		if self.platform == 'win' :
			libs = ['glut32']
			return libs, libs
		else:
			libs = ['glut']
			return libs, libs

	def hasRuntimePackage( self, version ):
		if self.platform == 'win' and self.ccVersionNumber >= 10.0000 and version == '3-7':
			return True
		else:
			return False
