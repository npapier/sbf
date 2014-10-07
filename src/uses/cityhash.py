# SConsBuildFramework - Copyright (C) 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

class Use_cityhash( IUse ):
	def getName( self ):
		return 'cityhash'

	def getVersions( self ):
		return ['1-1-0']

	def getLIBS( self, version ):
		lib = '{0}_{1}_{2}_{3}'.format(self.getName(), version, self.platform, self.ccVersion)
		if self.config == 'release':
			return [lib], []
		else:
			return [lib+'_D'], []

	def hasRuntimePackage( self, version ):
		if self.platform == 'win' and self.ccVersionNumber >= 11.0000 and version == '1-1-0':
			return True
		else:
			return False