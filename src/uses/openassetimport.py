# SConsBuildFramework - Copyright (C) 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

class Use_openassetimport( IUse ):
	def getName( self ):
		return 'openassetimport'

	def getVersions( self ):
		return ['3-0-2', '3-0-1', '3-0']

	def getLIBS( self, version ):
		if self.platform == 'win':
			if self.config == 'release':
				return ['assimp'], ['assimp']
			else:
				return ['assimpD'], ['assimpD']
		elif self.platform == 'posix':
			return ['assimp'],['assimp']

	def hasRuntimePackage( self, version ):
		return version == '3-0-2'
