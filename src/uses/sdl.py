# SConsBuildFramework - Copyright (C) 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

class Use_sdl( IUse ):
	def getName( self ):
		return 'sdl'

	def getVersions( self ):
		return ['2-0-3', '1-2-15', '1-2-14']

	def getRequirements( self, version ):
		if version == '2-0-3' and self.platform == 'win' and self.cc != 'emcc':
			return ['angle']
		else:
			return []

	def getCPPDEFINES( self, version ):
		if self.platform == 'posix' :
			return [ ('_GNU_SOURCE',1), '_REENTRANT' ]
		else:
			return []

	def getCPPFLAGS( self, version ):
		if self.cc == 'emcc' and version == '2-0-3':
			return ['-s', 'USE_SDL=2']
		return []

	def getCPPPATH( self, version ):
		if self.platform == 'win':
			if version == '2-0-3':
				return ['SDL2']
			else:
				return []
		elif self.platform == 'posix':
			return ['SDL']


	def getLIBS( self, version ):
		if self.cc == 'emcc':	return [], []
		if self.platform == 'win' :
			if version == '2-0-3':
				libs = [ 'SDL2', 'SDL2main' ]
				return libs, []
			else:
				libs = [ 'SDL', 'SDLmain' ]
				pakLibs = [ 'SDL' ]
				return libs, pakLibs
		elif self.platform == 'posix':
			return ['SDL'], []

	def getLINKFLAGS( self, version ):
		if self.cc == 'emcc' and version == '2-0-3':
			return ['-s', 'USE_SDL=2']
		return []


	def hasDevPackage( self, version ):
		return self.cc != 'emcc'

	def hasRuntimePackage( self, version ):
		return self.cc != 'emcc'
