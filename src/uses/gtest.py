# SConsBuildFramework - Copyright (C) 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

class Use_gtest( IUse ):
	def getName(self ):
		return 'gtest'

	def getVersions( self ):
		return [ '1-7-0', '446' ]

	def getCPPDEFINES( self, version ):
		defines = ['SBF_GTEST', 'GTEST_LINKED_AS_SHARED_LIBRARY']
		if self.ccVersionNumber >= 11.0000:
			defines.append( ('_VARIADIC_MAX', 10) )
		return defines

	def getLIBS( self, version ):
		if self.platform == 'win':
			if self.config == 'release':
				libs = ['gtest']
				return libs, libs
			else:
				libs = ['gtest-d']
				return libs, libs
		else:
			libs = ['gtest']
			return libs, []

	def hasRuntimePackage( self, version ):
		if self.platform == 'win' and self.ccVersionNumber >= 10.0000:
			return True
		else:
			return False
