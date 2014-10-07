# SConsBuildFramework - Copyright (C) 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

class Use_sdlMixer( IUse ):
	def getName( self ):
		return 'sdlMixer'

	def getVersions( self ):
		return ['1-2-11']

	def getCPPDEFINES( self, version ):
		if self.platform == 'posix' :
			return [ ('_GNU_SOURCE',1), '_REENTRANT' ]
		else:
			return []

	def getCPPPATH( self, version ):
		if self.platform == 'posix' :
			return ['/usr/include/SDL']
		else:
			return []


	def getLIBS( self, version ):
		if self.platform == 'win':
			libsBoth = [ 'SDL_mixer' ]
			return libsBoth, libsBoth
		elif self.platform == 'posix':
			libsBoth = [ 'SDL_mixer' ]
			return libsBoth, libsBoth

	def getLIBPATH( self, version ):
		if self.platform == 'win':
			return [], []
		elif self.platform == 'posix':
			return [ '/usr/lib' ], [ '/usr/lib' ]

	def hasRuntimePackage( self, version ):
		if self.platform == 'win' and self.ccVersionNumber >= 10.0000 and version == '1-2-11':
			return True
		else:
			return False
