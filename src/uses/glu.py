# SConsBuildFramework - Copyright (C) 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

class Use_glu( IUse ):
	def getName(self ):
		return "glu"

	def getLIBS( self, version ):
		if self.platform == 'win' :
			libs = ['glu32']
			return libs, []
		else:
			libs = ['GLU']
			return libs, libs

	def getLicenses( self, version ):
		return []

	def getPackageType( self ):
		return 'None'
