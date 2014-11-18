# SConsBuildFramework - Copyright (C) 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

class Use_angle( IUse ):
	def getName( self ):
		return 'angle'

	def getVersions( self ):
		return ['2-0-0']

	def getLIBS( self, version ):
		libs = ['libEGL', 'libGLESv2']
		return libs, []

	def hasRuntimePackage( self, version ):
		return True