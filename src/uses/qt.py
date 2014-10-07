# SConsBuildFramework - Copyright (C) 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

# @todo management of modules
# Qt modules:
#	core (included by default)	QtCore module
#	gui (included by default)	QtGui module
#	network						QtNetwork module
#	opengl						QtOpenGL module
#	phonon						Phonon Multimedia Framework
#	sql							QtSql module
#	svg							QtSvg module
#	xml							QtXml module
#	webkit						WebKit integration
#	qt3support					Qt3Support module

# @todo see Makefile.Release and Debug
# @todo CFLAGS = -nologo -Zm200 -Zc:wchar_t- -O2 -MD -W3 $(DEFINES)
# @todo CXXFLAGS = -nologo -Zm200 -Zc:wchar_t- -O2 -MD -GR -EHsc -W3 -w34100 -w34189 $(DEFINES)
# @todo LFLAGS = /LIBPATH:"c:\QtSDK\Desktop\Qt\4.8.0\msvc2010\lib" /NOLOGO /DYNAMICBASE /NXCOMPAT /INCREMENTAL:NO /DLL /MANIFEST /MANIFESTFILE:"release\vgQt.intermediate.manifest"
class Use_qt( IUse ):
	cppModules = ['QtCore', 'QtGui']
	linkModules = ['QtCore', 'QtGui']
	linkVersionPostfix = '4'

	def getName( self ):
		return 'qt'

	def getVersions( self ):
		if self.platform == 'win':
			return ['4-8-5', '4-8-6']
		else:
			return ['4-8-6']

	def getCPPDEFINES( self, version ):
		cppDefines = [ 'QT_NO_KEYWORDS', 'UNICODE', 'QT_THREAD_SUPPORT' ] # no more needed for 4.8.5: QT_LARGEFILE_SUPPORT
		cppDefines += [ 'QT_HAVE_MMX', 'QT_HAVE_3DNOW', 'QT_HAVE_SSE', 'QT_HAVE_MMXEXT', 'QT_HAVE_SSE2']
		cppDefines += [ 'QT_CORE_LIB', 'QT_GUI_LIB' ]
		if self.config == 'release':
			cppDefines += ['QT_NO_DEBUG']
		#else nothing to do
		if self.platform == 'win':
			cppDefines += [ 'QT_DLL' ]
		elif self.platform == 'posix':
			cppDefines += [ 'QT_SHARED' ]

		return cppDefines

	def getCPPPATH( self, version ):
		return self.cppModules
			
	def getLIBPATH( self, version ):
		return [],[]

	def getLIBS( self, version ):
		if self.platform == 'win':
			if self.config == 'release':
				libs = [ module + self.linkVersionPostfix for module in self.linkModules ]
			else:
				libs = [ module + 'd' + self.linkVersionPostfix for module in self.linkModules ]
		elif self.platform == 'posix':
			libs = self.linkModules
			
		return libs, []

	def hasRuntimePackage( self, version ):
		return True
