# SConsBuildFramework - Copyright (C) 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

class Use_sdl( IUse ):
	def getName( self ):
		return 'sdl'

	def getVersions( self ):
		return ['1-2-15', '1-2-14']

	def getCPPDEFINES( self, version ):
		if self.platform == 'posix' :
			return [ ('_GNU_SOURCE',1), '_REENTRANT' ]
		else:
			return []

	def getCPPPATH( self, version ):
		if self.platform == 'posix' :
			return ['SDL']
		else:
			return []


	def getLIBS( self, version ):
		if self.platform == 'win' :
			libs = [ 'SDL', 'SDLmain' ]
			pakLibs = [ 'SDL' ]
			return libs, pakLibs
		elif self.platform == 'posix':
			return ['SDL', 'SDL']

	def hasRuntimePackage( self, version ):
		return True