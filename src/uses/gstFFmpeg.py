# SConsBuildFramework - Copyright (C) 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

class Use_gstFFmpeg( IUse ):
	def getName( self ):
		return 'gstFFmpeg'

	def getVersions( self ):
		return [ '0-10-9' ]


	def getLIBS( self, version ):
		libs = [	'avcodec-lgpl', 'avdevice-lgpl', 'avfilter-lgpl',
					'avformat-lgpl', 'avutil-lgpl', 'swscale-lgpl'	]
		pakLibs = [	'avcodec-lgpl-52', 'avdevice-lgpl-52', 'avfilter-lgpl-1',
					'avformat-lgpl-52', 'avutil-lgpl-50', 'swscale-lgpl-0',
					'libbz2', 'z' ]
		if self.platform == 'win':
			return libs, pakLibs

	def hasRuntimePackage( self, version ):
		if self.platform == 'win' and self.ccVersionNumber >= 10.0000 and version == '0-10-9':
			return True
		else:
			return False
