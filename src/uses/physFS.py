# SConsBuildFramework - Copyright (C) 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

class Use_physFS( IUse ):
	def getName(self ):
		return 'physFS'

	def getVersions( self ):
		return [ '2-0-2', '2-0-1' ]

	def getLIBS( self, version ):
		if self.platform == 'win':
			if self.config == 'release':
				libs = ['physfs']
				return libs, libs
			else:
				libs = ['physfs-d']
				return libs, libs
		else:
			libs = ['physfs']
			return libs, libs

	def hasRuntimePackage( self, version ):
		if self.platform == 'win':
			return self.ccVersionNumber >= 10.0 and version == '2-0-2'
		else:
			return True