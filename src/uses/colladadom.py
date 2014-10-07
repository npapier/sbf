# SConsBuildFramework - Copyright (C) 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

class Use_colladadom( IUse ):
	def getName( self ):
		return "colladadom"

	def getVersions( self ):
		return [ '2-1', '2-0' ]


	def getCPPDEFINES( self, version ):
		# Linking with the COLLADA DOM shared library
		return [ 'DOM_DYNAMIC' ]

	def getCPPPATH( self, version ):
		if version == '2-1' :
			return [ 'collada-dom2-1', os.path.join('collada-dom2-1', '1.4') ]
		elif version == '2-0' :
			return [ 'collada-dom_2-0', os.path.join('collada-dom_2-0', '1.4') ]

	def getLIBS( self, version ):
		if version == '2-1' :
			if self.config == 'release' :
				libs = [ 'libcollada14dom21' ]
				return libs, libs
			else :
				libs = [ 'libcollada14dom21-d' ]
				return libs, libs
		elif version == '2-0' :
			if self.config == 'release' :
				libs = [ 'libcollada14dom20' ]
				return libs, libs
			else :
				libs = [ 'libcollada14dom20-d' ]
				return libs, libs

