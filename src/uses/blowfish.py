# SConsBuildFramework - Copyright (C) 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

class Use_blowfish( IUse ):
	def getName( self ):
		return 'blowfish'

	def getVersions( self ):
		return ['1-0']

	def getLIBS( self, version ):
		lib = '{}_{}_{}_{}'.format(self.getName(), version, self.platform, self.ccVersion) # @todo idem Use_cityhash() =
		if self.config == 'release':
			return [lib], []
		else:
			return [lib+'_D'], []

	def hasRuntimePackage( self, version ):
		return True
