# SConsBuildFramework - Copyright (C) 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

class Use_opengl( IUse ):
	def getName( self ):
		return "opengl"

#	def getCPPDEFINES( self, version ):
#		return [ 'GL_GLEXT_LEGACY' ]

	def getLIBS( self, version ):
		if self.platform == 'win' :
			# opengl32	: OpenGL and wgl functions
			# gdi32		: Pixelformat and swap related functions
			# user32	: ChangeDisplaySettings* functions
			libs = [ 'opengl32', 'gdi32', 'user32' ]
			return libs, []
		else:
			libs = ['GL']
			return libs, []

	def getLicenses( self, version ):
		return []


	def getPackageType( self ):
		return 'None'