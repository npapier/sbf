# SConsBuildFramework - Copyright (C) 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

class Use_sdl( IUse ):
	def getName( self ):
		return 'sdl'

	def getVersions( self ):
		#return ['2-0-3', '1-2-15', '1-2-14']
		return ['1-2-15', '2-0-3', '1-2-14']

	def getRequirements( self, version ):
		if version == '2-0-3':
			return ['angle 2-0-0']
		else:
			return []

	def getCPPDEFINES( self, version ):
		if self.platform == 'posix' :
			return [ ('_GNU_SOURCE',1), '_REENTRANT' ]
		else:
			return []

	def getCPPPATH( self, version ):
		if self.platform == 'posix' :
			return ['SDL']
		else:
			if version == '2-0-3':
				return ['SDL2']
			else:
				return []


	def getLIBS( self, version ):
		if self.platform == 'win' :
			if version == '2-0-3':
				libs = [ 'SDL2', 'SDL2main' ]
				return libs, []
			else:
				libs = [ 'SDL', 'SDLmain' ]
				pakLibs = [ 'SDL' ]
				return libs, pakLibs
		elif self.platform == 'posix':
			return ['SDL', 'SDL']

	def hasRuntimePackage( self, version ):
		return True