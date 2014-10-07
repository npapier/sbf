# SConsBuildFramework - Copyright (C) 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

class Use_python( IUse ):
	def getName( self ):
		return 'python'

	def getVersions( self ):
		return [ '2-7-3' ]

	def getCPPPATH( self, version ):
		if self.platform == 'win':
			cppPath = ['Python']
		else:
			cppPath = ['/usr/include/python2.7']
		return cppPath

	def getLIBS( self, version ):
		if self.platform == 'win':
			if self.config == 'release':
				libs = ['python27']
			else:
				libs = ['python27_d']
		else:
			libs = ['python2.7']
		return libs, []

	def hasDevPackage( self, version ):
		return not self.platform == 'posix'

	def hasRuntimePackage( self, version ):
		return not self.platform == 'posix'
