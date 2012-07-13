# SConsBuildFramework - Copyright (C) 2005, 2007, 2008, 2009, 2010, 2011, 2012, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

import glob
import os
import string
import sys

# To be able to use sbfUses.py without SCons
try:
	import SCons.Errors
except ImportError as e:
	pass

from sbfTools import *
from sbfUtils import getPathFromEnv, getFromEnv, convertToList
from sbfVersion import splitUsesName

#@todo moves to sbfConfig.py ?
class pythonConfig:
	__basePath = None

	@classmethod
	def __initialize( cls ):
		# Retrieves python location
		cls.__basePath = locateProgram('python')

		# Post-conditions
		if cls.__basePath is None or len(cls.__basePath)==0:
			raise SCons.Errors.UserError("Unable to retrieve Python installation path.")

	@classmethod
	def getBasePath( cls ):
		if cls.__basePath is None:
			cls.__initialize()
		return cls.__basePath


class sofaConfig:
	__basePath = None
	__pluginsList = []

	@classmethod
	def __initialize( cls ):
		# Retrieves SOFA_PATH
		cls.__basePath = getPathFromEnv('SOFA_PATH')

		# Post-conditions for SOFA_PATH
		if cls.__basePath is None or len(cls.__basePath)==0:
			raise SCons.Errors.UserError("Unable to configure sofa.\nSOFA_PATH environment variable must be defined.")


		# Retrieves SOFA_PLUGINS
		sofaPlugins = getFromEnv('SOFA_PLUGINS', True)
		if len(sofaPlugins)>0:
			cls.__pluginsList = sofaPlugins.split(':')
			print ("Found SOFA_PLUGINS:'{0}'.".format(sofaPlugins))


	@classmethod
	def getBasePath( cls ):
		if cls.__basePath is None:
			cls.__initialize()
		return cls.__basePath

	@classmethod
	def getPluginsList( cls ):
		if cls.__basePath is None:
			cls.__initialize()
		return cls.__pluginsList


class gtkmmConfig:
	__gtkmmBasePath		= None

	@classmethod
	def __getVersion( cls ):
		"""Returns version string like '2.22' or '' if not found"""
		version = winGetInstallPath(win32con.HKEY_LOCAL_MACHINE, r'SOFTWARE\gtkmm\2.4\Version', enableLogging=False)
		if len(version)==0:
			version = winGetInstallPath(win32con.HKEY_LOCAL_MACHINE, r'SOFTWARE\Wow6432Node\gtkmm\2.4\Path', enableLogging=False)
		return version

	@classmethod
	def __initialize( cls ):
		if sys.platform == 'win32':
			# Retrieves gtkmm path and version from windows registry
			gtkmmBasePath = locateProgram('gtkmm')
			if len(gtkmmBasePath) > 0:
				cls.__gtkmmBasePath = gtkmmBasePath
				# Prints message in verbose mode
				if '--verbose' in sys.argv:
					# Retrieves version
					version = cls.__getVersion()
					if len(version)==0:
						version = '-'
					# Prints informations about gtkmm
					print ( 'gtkmm is installed in directory : {0}'.format(gtkmmBasePath) )
					print ( 'Assumes gtk and gtkmm installed in the same directory.\nFound gtkmm version: {0}\n'.format(version) )

		# If gtkmm has not been found, uses GTKMM_BASEPATH environment variable
		if cls.__gtkmmBasePath is None:
			# Retrieves GTKMM_BASEPATH
			cls.__gtkmmBasePath	= getPathFromEnv('GTKMM_BASEPATH')

		# Post-conditions
		if cls.__gtkmmBasePath is None or len(cls.__gtkmmBasePath)==0:
			raise SCons.Errors.UserError("Unable to configure gtkmm.")

	@classmethod
	def getBasePath( cls ):
		if cls.__gtkmmBasePath is None:
			cls.__initialize()
		return cls.__gtkmmBasePath

	@classmethod
	def getGtkmmBasePath( cls ):
		return cls.getBasePath()


###
# @todo licences
class IUse :
	platform	= None
	config		= None

	# See SConsBuildFramework class
	cc					= None
	ccVersionNumber		= None
	isExpressEdition	= None
	ccVersion			= None

	@classmethod
	def initialize( self, platform, config, cc, ccVersionNumber, isExpressEdition, ccVersion ):
		self.platform	= platform
		self.config		= config

		#
		self.cc					= cc
		self.ccVersionNumber	= ccVersionNumber
		self.isExpressEdition	= isExpressEdition
		self.ccVersion			= ccVersion

	def getName( self ):
		raise StandardError("IUse::getName() not implemented")

	# Returns the list of version supported for this package.
	# The first element of the returned list is the default version (see use alias for more informations).
	def getVersions( self ):
		return []
		#raise StandardError("IUse::getVersions() not implemented")


	# for compiler
	def getCPPDEFINES( self, version ):
		return []

	def getCPPFLAGS( self, version ):
		return []

	def getCPPPATH( self, version ):
		return []


	# for linker
	def getLIBS( self, version ):
		return [], []

	def getLIBPATH( self, version ):
		return [], []


	# for packager
	def getPackageType( self ):
		"""	None			(no package, i.e. installed in the system (opengl), without files (gtkmmext), include in another package (glibmm in gtkmm))
			NoneAndNormal	(no package (like None), but getLIBS() and getLicenses() must be redistributed. Example: sofa)
			Normal			(indicate that this 'uses' is provided by a sbf package, that getLIBS() must be redistributed and that licenses files from package must be redistributed too.).
			Full			(indicate that this 'uses' is provided by a sbf package and that all files in the package must be redistributed)."""
		return 'Normal'

	def getDbg( self, version ):
		"""@return a list of file containing debug informations (PDB on Windows platform)."""
		return []

	def getLicenses( self, version ):
		"""@return None to indicate that license file(s) could be found automatically (by using the naming rule of sbf package).
		Returns [] to explicitly specify that there is no license file at all (provided by another 'uses', like glibmm/gtkmm).
		Returns [...] to explicitly specify one or more license file(s)"""
		return []

	def getRedist( self, version ):
		"""Returns the redistributable to include in nsis setup program. A redistributable must be a zip file or an executable available in SCONS_BUILD_FRAMEWORK/rc/nsis/ directory"""
		return []

	def __call__( self, useVersion, env, skipLinkStageConfiguration = False ):
		useNameVersion = self.getName() + " " + useVersion
#print ("Configures %s" % useNameVersion)

		### Configuration of compile stage
		# CPPDEFINES
		cppdefines = self.getCPPDEFINES( useVersion )
		if cppdefines != None :
			if len(cppdefines) > 0 :
				env.AppendUnique( CPPDEFINES = cppdefines )
		else:
			raise SCons.Errors.UserError("Uses=[\'%s\'] not supported on platform %s (see CPPDEFINES)." % (useNameVersion, self.platform) )

		# CPPFLAGS
		cppflags = self.getCPPFLAGS( useVersion )
		if cppflags != None :
			if len(cppflags) > 0 :
				env.AppendUnique( CPPFLAGS = cppflags )
		else:
			raise SCons.Errors.UserError("Uses=[\'%s\'] not supported on platform %s (see CPPFLAGS)." % (useNameVersion, self.platform) )

		# CPPPATH
		cpppath = self.getCPPPATH( useVersion )
		if cpppath != None :
			if len(cpppath) > 0 :
				cpppathAbs = []
				if os.path.isabs(cpppath[0]) :
					# Nothing to do
					cpppathAbs = cpppath
				else:
					# Converts to absolute path
					for path in cpppath :
						cpppathAbs.append( os.path.join( env.sbf.myIncludesInstallExtPaths[0], path ) )		# @todo for each myIncludesInstallExtPaths[]

				if env.GetOption('weak_localext') and (self.getName() not in env['weakLocalExtExclude']):
					for path in cpppathAbs :
						env.AppendUnique( CCFLAGS = ['${INCPREFIX}' + path ] )
				else:
					env.AppendUnique( CPPPATH = cpppathAbs )
		else:
			raise SCons.Errors.UserError("Uses=[\'%s\'] not supported on platform %s (see CPPPATH)." % (useNameVersion, self.platform) )

		### Configuration of link stage
		if skipLinkStageConfiguration:
			return

		# LIBS
		libs = self.getLIBS( useVersion )
		if (libs != None) and (len(libs) == 2) :
			if len(libs[0]) > 0:
				env.AppendUnique( LIBS = libs[0] )
		else:
			raise SCons.Errors.UserError("Uses=[\'%s\'] not supported on platform %s (see LIBS)." % (useNameVersion, self.platform) )

		# LIBPATH
		libpath = self.getLIBPATH( useVersion )
		if (libpath != None) and (len(libpath) == 2) :
			if len(libpath[0]) > 0 :
				env.AppendUnique( LIBPATH = libpath[0] )
		else:
			raise SCons.Errors.UserError("Uses=[\'%s\'] not supported on platform %s (see LIBPATH)." % (useNameVersion, self.platform) )



### Several IUse implementation ###

class Use_adl( IUse ):
	def getName( self ):
		return 'adl'

	def getVersions( self ):
		return [ '3-0' ]

	def getLIBS( self, version ):
		return [], []



class Use_blowfish( IUse ):
	def getName( self ):
		return 'blowfish'

	def getVersions( self ):
		return ['1-0']

	def getLIBS( self, version ):
		if self.platform == 'win32':
			if self.config == 'release':
				return ['Blowfish'], []
			else:
				return ['Blowfish_D'], []



class Use_boost( IUse ):
	def getName( self ):
		return 'boost'

	def getVersions( self ):
		return [ '1-48-0', '1-50-0', '1-49-0', '1-47-0', '1-46-1', '1-45-0' ]

	def getCPPDEFINES( self, version ):
		if self.platform == 'win32':
			return [ 'BOOST_ALL_DYN_LINK' ]
		else:
			return []


	def getLIBS( self, version ):
		if self.platform == 'win32':

			# vc version
			if self.cc == 'cl' and self.ccVersionNumber >= 10.0000:
				vc = 'vc100'
			elif self.cc == 'cl' and self.ccVersionNumber >= 9.0000:
				vc = 'vc90'
			elif self.cc == 'cl' and self.ccVersionNumber >= 8.0000 :
				vc = 'vc80'
			else:
				return

			# configuration
			if self.config == 'release':
				conf = 'mt'
			else:
				conf = 'mt-gd'

			# boost shared libraries
			genPakLibs = [	'boost_date_time-{vc}-{conf}-{ver}', 'boost_filesystem-{vc}-{conf}-{ver}', 'boost_graph-{vc}-{conf}-{ver}',
							'boost_iostreams-{vc}-{conf}-{ver}', 'boost_math_c99-{vc}-{conf}-{ver}', 'boost_math_c99f-{vc}-{conf}-{ver}',
							'boost_math_c99l-{vc}-{conf}-{ver}', 'boost_math_tr1-{vc}-{conf}-{ver}', 'boost_math_tr1f-{vc}-{conf}-{ver}',
							'boost_math_tr1l-{vc}-{conf}-{ver}', 'boost_prg_exec_monitor-{vc}-{conf}-{ver}', 'boost_program_options-{vc}-{conf}-{ver}',
							'boost_python-{vc}-{conf}-{ver}', 'boost_random-{vc}-{conf}-{ver}', 'boost_regex-{vc}-{conf}-{ver}',
							'boost_serialization-{vc}-{conf}-{ver}', 'boost_signals-{vc}-{conf}-{ver}', 'boost_system-{vc}-{conf}-{ver}',
							'boost_thread-{vc}-{conf}-{ver}', 'boost_unit_test_framework-{vc}-{conf}-{ver}', 'boost_wave-{vc}-{conf}-{ver}',
							'boost_wserialization-{vc}-{conf}-{ver}' ]
			genPakLibs2 = [	'boost_chrono-{vc}-{conf}-{ver}' ]
			genPakLibs3 = [	'boost_locale-{vc}-{conf}-{ver}', 'boost_timer-{vc}-{conf}-{ver}' ]

			versionToVer = {	'1-48-0'	: '1_48',
								'1-49-0'	: '1_49',
								'1-50-0'	: '1_50' }
			if version in ['1-50-0', '1-49-0', '1-48-0']:
				# autolinking, so nothing to do.
				ver = versionToVer[version]
				pakLibs = [ lib.format( vc=vc, conf=conf, ver=ver ) for lib in genPakLibs + genPakLibs2 + genPakLibs3 ]
				return [], pakLibs
			elif version == '1-47-0':
				# autolinking, so nothing to do.
				ver = '1_47'
				pakLibs = [ lib.format( vc=vc, conf=conf, ver=ver ) for lib in genPakLibs + genPakLibs2 ]
				return [], pakLibs
			elif version == '1-46-1':
				# autolinking, so nothing to do.
				ver = '1_46_1'
				pakLibs = [ lib.format( vc=vc, conf=conf, ver=ver ) for lib in genPakLibs ]
				return [], pakLibs
		elif self.platform == 'posix' and version in ['1-38-0', '1-34-1']:
			libs = [	'libboost_date_time-mt',	'libboost_filesystem-mt',		'libboost_graph-mt',
						'libboost_iostreams-mt',	'libboost_prg_exec_monitor-mt',	'libboost_program_options-mt',
						'libboost_regex-mt',		'libboost_serialization-mt',
#						'libboost_python-mt',		'libboost_regex-mt',			'libboost_serialization-mt',
						'libboost_signals-mt',		'libboost_thread-mt',			'libboost_unit_test_framework-mt',
						'libboost_wave-mt',			'libboost_wserialization-mt'	]
			return libs, libs



class Use_bullet( IUse ):

	def getName( self ):
		return 'bullet'

	def getVersions( self ):
		return ['2-77', '2-76']

	def getLIBS( self, version ):
		libs = ['BulletCollision', 'BulletDynamics', 'BulletMultiThreaded', 'BulletSoftBody', 'LinearMath']
		return libs, []



#		lenv.AppendUnique( LIBS = ['cairo', 'fontconfig', 'freetype', 'png', 'z' ] )
class Use_cairo( IUse ):

	def getName( self ):
		return 'cairo'

	def getVersions( self ):
		return ['1-10-0', '1-8-6', '1-7-6', '1-2-6']


	def getCPPFLAGS( self, version ):
		if self.platform == 'win32' :
			return [ '/wd4250' ]
		else:
			return []

	def getCPPPATH( self, version ):
		if self.platform == 'win32' :
			# Sets CPPPATH
			gtkCppPath = [ 'include/cairo' ]
			cppPath = []
			for path in gtkCppPath :
				cppPath.append( os.path.join(gtkmmConfig.getBasePath(), path) )
			return cppPath
		elif self.platform == 'posix' :
			# Sets CPPPATH
			cppPath = [	'/usr/include/cairo', '/usr/include/pixman-1', '/usr/include/freetype2',
						'/usr/include/libpng12'	]
			return cppPath

	def getLIBS( self, version ):
		if self.platform == 'win32':
			libs = [ 'cairo' ]
			pakLibs = [ 'libcairo-2', 'libpangocairo-1.0-0' ]
			return libs, pakLibs
		elif self.platform == 'posix' :
			libs = [ 'cairo' ]
			return libs, libs

	def getLIBPATH( self, version ):
		if self.platform == 'win32' :
			return [ os.path.join(gtkmmConfig.getBasePath(), 'lib') ], [ os.path.join(gtkmmConfig.getBasePath(), 'bin') ]
		elif self.platform == 'posix' :
			return [], []

	def getPackageType( self ):
		return 'None'

# @todo cairomm


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


class Use_ffmpeg( IUse ):
	def getName( self ):
		return 'ffmpeg'

	def getVersions( self ):
		return [ '16537' ]


	def getLIBS( self, version ):
		libs = [ 'avcodec-52', 'avdevice-52', 'avformat-52', 'avutil-49', 'swscale-0' ]
		#libs = [ 'avcodec-52', 'avformat-52', 'avutil-49' ]
		if self.platform == 'win32':
			return libs, libs


class Use_gstFFmpeg( IUse ):
	def getName( self ):
		return 'gstffmpeg'

	def getVersions( self ):
		return [ '0-10-9' ]


	def getLIBS( self, version ):
		libs = [	'avcodec-lgpl', 'avdevice-lgpl', 'avfilter-lgpl',
					'avformat-lgpl', 'avutil-lgpl', 'swscale-lgpl'	]
		pakLibs = [	'avcodec-lgpl-52', 'avdevice-lgpl-52', 'avfilter-lgpl-1',
					'avformat-lgpl-52', 'avutil-lgpl-50', 'swscale-lgpl-0',
					'libbz2', 'z' ]
		if self.platform == 'win32':
			return libs, pakLibs



class Use_opengl( IUse ):
	def getName( self ):
		return "opengl"

	def getLIBS( self, version ):
		if self.platform == 'win32' :
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


class Use_poppler( IUse ):
	"""poppler needs freetype2, zlib and libpng from gtkmm 2.22.0-2"""

	def getName( self ):
		return 'poppler'

	def getVersions( self ):
		return ['0-16-5']

	def getLIBS( self, version ):
		if self.config == 'release' :
			return ['poppler', 'poppler-cpp'], ['poppler-cpp', 'libiconv2', 'jpeg62']
		else:
			return ['poppler-d', 'poppler-cpp-d'], ['poppler-cpp-d', 'libiconv2', 'jpeg62']


class Use_itk( IUse ):

	def getName( self ):
		return 'itk'

	def getVersions( self ):
		return ['3-4-0']


	# Already and always done by sbf on windows platform '/DNOMINMAX'


	def getCPPPATH( self, version ):
		# Sets CPPPATH
		cppPath = [	'itk', 'itk/Algorithms', 'itk/BasicFilters', 'itk/Common', 'itk/expat', 'itk/gdcm/src',
					'itk/IO', 'itk/Numerics', 'itk/Numerics/FEM', 'itk/Numerics/NeuralNetworks', 'itk/Numerics/Statistics',
					'itk/SpatialObject', 'itk/Utilities', 'itk/Utilities/MetaIO', 'itk/Utilities/NrrdIO',
					'itk/Utilities/vxl/core', 'itk/Utilities/vxl/vcl' ]

		return cppPath


	def getLIBS( self, version ):
		if (self.platform == 'win32') and (version in ['3-4-0']) :
			libs = [	'ITKAlgorithms', 'ITKBasicFilters', 'ITKCommon', 'ITKDICOMParser', 'ITKEXPAT', 'ITKFEM', 'itkgdcm',
						'ITKIO', 'itkjpeg8', 'itkjpeg12', 'itkjpeg16', 'ITKMetaIO', 'ITKniftiio', 'ITKNrrdIO', 'ITKNumerics',
						'itkopenjpeg', 'itkpng', 'ITKSpatialObject', 'ITKStatistics', 'itksys', 'itktiff', 'itkv3p_netlib',
						'itkvcl', 'itkvnl', 'itkvnl_algo', 'itkvnl_inst', 'itkzlib', 'ITKznz' ]
			pakLibs = [	'ITKCommon' ]
			return libs, pakLibs



class Use_openil( IUse ):
	def getName( self ):
		return "openil"

	def getVersions( self ):
		return ['1-7-8']


	def getLIBS( self, version ):
		if self.platform == 'win32' :
			if self.config == 'release' :
				libs = ['DevIL', 'ILU']
				return libs, libs
			else:
				libs = ['DevIL', 'ILU']
				return libs, libs #['DevILd'] @todo openil should be compiled in debug on win32 platform
		else:
			if self.config == 'release' :
				libs = ['IL', 'ILU']
				return libs, libs
			else :
				libs = ['IL', 'ILU']
				# @remark openil not compiled in debug in ubuntu 8.10
				#libs = ['ILd']
				return libs, libs


# @remarks sdl-config --cflags --libs
class Use_sdl( IUse ):
	def getName( self ):
		return "sdl"

	def getVersions( self ):
		return ['1-2-14']

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
		if self.platform == 'win32' :
			libs = [ 'SDL', 'SDLmain' ]
			pakLibs = [ 'SDL' ]
			return libs, pakLibs
		elif self.platform == 'posix' :
			return ['SDL', 'SDL']

	def getLIBPATH( self, version ):
		if self.platform == 'win32':
			return [], []
		elif self.platform == 'posix':
			return [ '/usr/lib' ], [ '/usr/lib' ]


class Use_sdlMixer( IUse ):
	def getName( self ):
		return "sdlmixer"

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
		if self.platform == 'win32':
			libsBoth = [ 'SDL_mixer' ]
			return libsBoth, libsBoth
		elif self.platform == 'posix':
			libsBoth = [ 'SDL_mixer' ]
			return libsBoth, libsBoth

	def getLIBPATH( self, version ):
		if self.platform == 'win32':
			return [], []
		elif self.platform == 'posix':
			return [ '/usr/lib' ], [ '/usr/lib' ]


class Use_glew( IUse ):
	def getName( self ):
		return "glew"

	def getVersions( self ):
		return ['1-5-1']

	def getLIBS( self, version ):
		libs = ['glew32']
		return libs, libs


class Use_glu( IUse ):
	def getName(self ):
		return "glu"

	def getLIBS( self, version ):
		if self.platform == 'win32' :
			libs = ['glu32']
			return libs, []
		else:
			libs = ['GLU']
			return libs, libs

	def getLicenses( self, version ):
		return []

	def getPackageType( self ):
		return 'None'


class Use_glm( IUse ):
	def getName(self ):
		return 'glm'

	def getVersions( self ):
		return [ '0-9-3-3', '0-8-4-1' ]


class Use_glut( IUse ):
	def getName(self ):
		return "glut"

	def getVersions( self ):
		return ['3-7']

	def getLIBS( self, version ):
		if self.platform == 'win32' :
			libs = ['glut32']
			return libs, libs
		else:
			libs = ['glut']
			return libs, libs


class Use_gtest( IUse ):
	def getName(self ):
		return "gtest"

	def getVersions( self ):
		return [ '446', '445' ]

	def getCPPDEFINES( self, version ):
		return ['SBF_GTEST', 'GTEST_LINKED_AS_SHARED_LIBRARY']

	def getLIBS( self, version ):
		if self.platform == 'win32':
			if version == '446':
				if self.config == 'release':
					libs = ['gtest']
					return libs, libs
				else:
					libs = ['gtest-d']
					return libs, libs
			elif version == '445':
				if self.config == 'release':
					libs = ['gtest-md']
					return libs, libs
				else:
					libs = ['gtest-mdd']
					return libs, libs
		else:
			libs = ['gtest']
			return libs, []


class Use_opencollada( IUse ):
	def getName(self ):
		return "opencollada"

	def getVersions( self ):
		return ['865', '864', '768', '736']

	def getCPPPATH( self, version ):
		if self.platform == 'win32':
			return [ 	'opencollada/COLLADAFramework/',
						'opencollada/COLLADABaseUtils/',
						'opencollada/COLLADABaseUtils/Math',
						'opencollada/COLLADASaxFrameworkLoader/',
						'opencollada/COLLADASaxFrameworkLoader/generated14',
						'opencollada/COLLADASaxFrameworkLoader/generated15',
						'opencollada/COLLADAStreamWriter/',
						'opencollada/GeneratedSaxParser/',
						'opencollada/MathMLSolver/',
						'opencollada/MathMLSolver/AST',
						'opencollada/LibXML/'
						'opencollada/LibXML/libxml',
						'opencollada/pcre/',
						'opencollada/libBuffer/',
						'opencollada/libBuffer/performanceTest',
						'opencollada/libftoa/',
						'opencollada/libftoa/performanceTest',
						'opencollada/libftoa/unitTest']
		else:
			return []		
		
	def getLIBS( self, version ):
		if self.platform == 'win32':
			if self.config == 'release':
				libs = ['COLLADABaseUtils', 'COLLADAFramework', 'COLLADASaxFrameworkLoader', 'COLLADAStreamWriter', 'GeneratedSaxParser', 'pcre', 'MathMLSolver', 'LibXML', 'libBuffer', 'libftoa']
				return libs, []
			else:
				libs = ['COLLADABaseUtils-d', 'COLLADAFramework-d', 'COLLADASaxFrameworkLoader-d', 'COLLADAStreamWriter-d', 'GeneratedSaxParser-d', 'pcre-d', 'MathMLSolver-d', 'LibXML-d', 'libBuffer-d', 'libftoa-d']
				return libs, []
		else:
			libs = ['COLLADABaseUtils', 'COLLADAFramework', 'COLLADASaxFrameworkLoader', 'COLLADAStreamWriter', 'GeneratedSaxParser', 'pcre', 'MathMLSolver', 'LibXML', 'libBuffer', 'libftoa']
			return libs, []



# @todo package python into a localExt
class Use_python( IUse, pythonConfig ):

	def getName( self ):
		return 'python'

	def getCPPPATH( self, version ):
		cppPath = [	os.path.join(self.getBasePath(), 'include') ]

		return cppPath

	def getVersions( self ):
		return [ '2-6' ]

	def getLIBS( self, version ):
		return [], []

	def getLIBPATH( self, version ):
		path = [ os.path.join( self.getBasePath(), 'libs' ) ]
		return path, []

	def getLicenses( self, version ):
		return []


class Use_physfs( IUse ):
	def getName(self ):
		return "physfs"

	def getVersions( self ):
		return [ '2-0-2', '2-0-1' ]

	def getCPPDEFINES( self, version ):
		return []

	def getLIBS( self, version ):
		if self.platform == 'win32':
			if self.config == 'release':
				libs = ['physfs']
				return libs, libs
			else:
				libs = ['physfs-d']
				return libs, libs
		else:
			libs = ['physfs']
			return libs, []


class Use_qt( IUse ):
	cppModules = ['QtCore', 'QtGui']
	linkModules = ['QtCore', 'QtGui']
	linkVersionPostfix = '4'

	def getName( self ):
		return 'qt'

	def getVersions( self ):
		return ['4-8-1']

	def getCPPDEFINES( self, version ):
		cppDefines = [ 'QT_NO_KEYWORDS', 'UNICODE', 'QT_DLL', 'QT_LARGEFILE_SUPPORT', 'QT_THREAD_SUPPORT' ]
		cppDefines += [ 'QT_HAVE_MMX', 'QT_HAVE_3DNOW', 'QT_HAVE_SSE', 'QT_HAVE_MMXEXT', 'QT_HAVE_SSE2']
		cppDefines += [ 'QT_CORE_LIB', 'QT_GUI_LIB' ]
		if self.config == 'release':
			cppDefines += ['QT_NO_DEBUG']
		#else nothing to do

		return cppDefines

	def getCPPPATH( self, version ):
		return self.cppModules

	def getLIBS( self, version ):
		if self.platform == 'win32':
			if self.config == 'release':
				libs = [ module + self.linkVersionPostfix for module in self.linkModules ]
				pakLibs = libs
				return libs, pakLibs
			else:
				libs = [ module + 'd' + self.linkVersionPostfix for module in self.linkModules ]
				pakLibs = libs
				return libs, pakLibs

	def getPackageType( self ):
		return 'Normal'


class Use_scintilla( IUse ):
	def getName( self ):
		return 'scintilla'

	def getVersions( self ):
		return [ '3-2-0']

	def getCPPPATH( self, version ):
		return ['Scintilla']

	def getLIBS( self, version ):
		if self.platform == 'win32':
			if self.config == 'release':
				libs = ['ScintillaEdit3']
				return libs, libs
			else:
				libs = ['ScintillaEditd3']
				return libs, libs


# @todo getSvnRevision()
# @todo SOFA_PATH documentation
# TODO: packages sofa into a localExt and adapts the following code to be more sbf friendly
class Use_sofa( IUse, sofaConfig ):

	def getName( self ):
		return 'sofa'

	def getCPPDEFINES( self, version ):
		definesList = ['SOFA_DOUBLE', 'SOFA_DEV', '_SCL_SECURE_NO_WARNINGS', '_CRT_SECURE_NO_WARNINGS', 'SOFA_NO_VECTOR_ACCESS_FAILURE', 'SOFA_SUPPORT_MAPPED_MASS']
		
		pluginsDefine = ''
		for plugin in self.getPluginsList():
			if len(pluginsDefine)>0:
				pluginsDefine += ':' + plugin
			else:
				pluginsDefine += plugin

		definesList += [("SOFA_PLUGINS", "\\\"%s\\\"" % pluginsDefine)]

		return definesList

	def getCPPFLAGS( self, version ):
		if self.platform == 'win32' :
			return ['/wd4250', '/wd4251', '/wd4275', '/wd4996', '/wd4800']
		else:
			return []

	def getCPPPATH( self, version ):
		cppPath = [	os.path.join(self.getBasePath(), 'applications'),
					os.path.join(self.getBasePath(), 'modules'),
					os.path.join(self.getBasePath(), 'framework'),
					os.path.join(self.getBasePath(), 'include'),
					os.path.join(self.getBasePath(), 'extlibs/taucs_mt/src'),
					os.path.join(self.getBasePath(), 'extlibs/tinyxml'),
					os.path.join(self.getBasePath(), 'extlibs/miniFlowVR/include') ]

		if self.platform == 'posix':
			cppPath += ['/usr/include/libxml2']

		return cppPath

	def getLIBS( self, version ):
		if self.platform == 'win32' :
			libs = []
			pakLibs = ['glew32', 'glut32']

			libsBoth = [  'sofa_advanced_interaction', 'sofa_advanced_constraint', 'sofa_base_collision', 'sofa_base_linear_solver', 'sofa_base_mechanics', 'sofa_base_topology', 'sofa_base_visual', 'sofabgl'
						, 'sofa_boundary_condition', 'sofa_constraint', 'sofacore', 'sofadefaulttype', 'sofa_deformable', 'sofa_engine' , 'sofa_explicit_ode_solver'
						, 'sofa_graph_component', 'sofa_haptics', 'sofa_implicit_ode_solver', 'sofa_loader', 'sofa_mesh_collision', 'sofa_misc_collision', 'sofa_misc_collision_dev', 'sofa_misc_mapping'
						, 'sofa_object_interaction', 'sofa_rigid', 'sofa_simple_fem', 'sofa_sph_fluid', 'sofa_taucs_solver', 'sofa_topology_mapping', 'sofa_user_interaction', 'sofa_volumetric_data'
						, 'sofahelper', 'sofagui', 'sofasimulation', 'sofatree' ]

			# optional plugins (sofa-dt)
			libsBoth += self.getPluginsList()

			# shared library
			#libsBoth += [ 'sofa_eigen2_solver' ]

			staticLibs = ['miniFlowVR', 'newmat', 'taucs_mt', 'tinyxml']

			sofaVersion = '_1_0'
			libsBoth = [ lib + sofaVersion for lib in libsBoth ]
			staticLibs = [ lib + sofaVersion for lib in staticLibs ]

			if self.config == 'release' :
				libs += libsBoth + staticLibs
				pakLibs += libsBoth
			else:
				libsBothDebug = [ lib + 'd' for lib in libsBoth ]
				staticLibsDebug = [ lib + 'd' for lib in staticLibs ]
				libs += libsBothDebug + staticLibsDebug
				pakLibs += libsBothDebug
			return libs, pakLibs
		elif self.platform == 'posix' :
			libs = ['xml2', 'z']
			pakLibs = []
			libs += ['libminiFlowVR', 'libnewmat', 'libsofacomponentanimationloop', 'libsofacomponent', 'libsofacomponentbase', 'libsofacomponentbehaviormodel', 'libsofacomponentcollision', 'libsofacomponentconstraintset', 'libsofacomponentcontextobject', 'libsofacomponentcontroller', 'libsofacomponentfem', 'libsofacomponentforcefield', 'libsofacomponentinteractionforcefield', 'libsofacomponentlinearsolver', 'libsofacomponentmapping', 'libsofacomponentmass', 'libsofacomponentmisc', 'libsofacomponentodesolver', 'libsofacomponentprojectiveconstraintset', 'libsofacomponentvisualmodel',
					'libsofacore', 'libsofadefaulttype', 'libsofahelper', 'libsofagui', 'libsofasimulation', 'libsofatree']
			pakLibs += ['libminiFlowVR', 'libnewmat', 'libsofacomponent', 'libsofacomponentanimationloop', 'libsofacomponentbase', 'libsofacomponentbehaviormodel', 'libsofacomponentcollision', 'libsofacomponentcontextobject', 'libsofacomponentcontroller', 'libsofacomponentfem', 'libsofacomponentforcefield', 'libsofacomponentinteractionforcefield', 'libsofacomponentlinearsolver', 'libsofacomponentmapping', 'libsofacomponentmass',  'libsofacomponentmisc', 'libsofacomponentodesolver', 'libsofacomponentvisualmodel',
						'libsofacore', 'libsofadefaulttype', 'libsofahelper', 'libsofasimulation', 'libsofatree']
			return libs, pakLibs

	def getLIBPATH( self, version ):
		libPath = []
		pakLibPath = []

		if self.platform == 'win32':
			if self.config == 'release' :
				if self.cc == 'cl':
					path = os.path.join( self.getBasePath(), 'lib' )
				libPath.append( path )
				pakLibPath.append( path )
			else:
				if self.cc == 'cl':
					path = os.path.join( self.getBasePath(), 'lib' )
				libPath.append( path )
				pakLibPath.append( path )
			#
			#commonPath = os.path.join( self.getBasePath(), 'lib/win32/Common' )
			#libPath.append( commonPath )
			#
		#	pluginsPath = os.path.join( self.getBasePath(), 'lib/sofa-plugins' )
		#	libPath.append( pluginsPath )
		#	pakLibPath.append( pluginsPath )
			return libPath, pakLibPath

		elif self.platform == 'posix' :
			path = os.path.join( self.getBasePath(), 'lib')
			libPath.append( path )
			pakLibPath.append( path )
			return libPath, pakLibPath

	def getPackageType( self ):
		return 'NoneAndNormal'

	def getDbg( self, version ):
		path = os.path.join( self.getBasePath(), 'lib' )
		dbgFiles = glob.glob( join(path,'*.pdb') )
		dbgFilesD = glob.glob( join(path,'*_[0-9]_[0-9]d.pdb') )
		dbgFilesR = glob.glob( join(path,'*_[0-9]_[0-9].pdb') )
		assert( len(dbgFiles) == len(dbgFilesD) + len(dbgFilesR) )

		if self.config == 'release':
			return dbgFilesR
		else:
			return dbgFilesD

	def getLicenses( self, version ):
		# sofa framework license
		licenses = [ os.path.join( self.getBasePath(), 'LICENCE.txt' ) ]
		# plugins licenses
		pluginsDir = os.path.join( self.getBasePath(), 'applications', 'plugins' )
		for plugin in self.getPluginsList():
			licenses.append( join(pluginsDir, plugin, plugin + '.txt') )
		return licenses



def getPathsForSofa( debugAndRelease = False ):
	sofaUse = UseRepository.getUse('sofa')
	if sofaUse is None:
		return []

	if debugAndRelease:
		configBak = sofaUse.config

		sofaUse.config = 'debug'
		paths = set(sofaUse.getLIBPATH( '' )[0])

		sofaUse.config = 'release'
		paths |= set(sofaUse.getLIBPATH( '' )[0])

		sofaUse.config = configBak
	else:
		paths = set(sofaUse.getLIBPATH( '' )[0])

	return list(paths)


class Use_usb2brd( IUse ):
	def getName(self ):
		return "usb2brd"

	def getVersions( self ):
		return [ '1-0-15' ]

	def getLIBS( self, version ):
		if self.platform == 'win32':
			libs = ['usb2brd']
			return libs, []


#@todo Adds support to both ANSI and Unicode version of wx
#@todo Adds support static/dynamic and db stuff (see http://www.wxwidgets.org/wiki/index.php/MSVC_.NET_Setup_Guide)
class Use_wxWidgets( IUse ):
	def getName( self ):
		return 'wx'

	def getVersions( self ):
		return ['2-8-8']

	def getCPPDEFINES( self, version ):
		if self.platform == 'win32':
			return [ 'WXUSINGDLL', '__WIN95__' ]
		else:
			return [ ('_FILE_OFFSET_BITS', 64), '_LARGE_FILES', '__WXGTK__' ]

	def getCPPFLAGS( self, version ):
		if self.platform == 'win32':
			return []
		else:
			return ['-pthread', '-Wl,-Bsymbolic-functions']

	def getCPPPATH( self, version ):
		if self.platform == 'win32':
			return []
		else:
			return ['/usr/lib/wx/include/gtk2-unicode-release-2.8', '/usr/include/wx-2.8']

	def getLIBS( self, version ):
		if self.platform == 'win32' and version == '2-8-8' :
			if self.config == 'release' :
				libs = [	'wxbase28', 'wxbase28_net', 'wxbase28_xml', 'wxmsw28_adv', 'wxmsw28_aui', 'wxmsw28_core',
							'wxmsw28_html', 'wxmsw28_media', 'wxmsw28_qa', 'wxmsw28_richtext', 'wxmsw28_xrc' ]
				pakLibs = [	'wxbase28_net_vc_custom', 'wxbase28_odbc_vc_custom', 'wxbase28_vc_custom', 'wxbase28_xml_vc_custom',
							'wxmsw28_adv_vc_custom', 'wxmsw28_aui_vc_custom', 'wxmsw28_core_vc_custom', #'wxmsw28_gl_vc_custom',
							'wxmsw28_html_vc_custom', 'wxmsw28_media_vc_custom', 'wxmsw28_qa_vc_custom', 'wxmsw28_richtext_vc_custom',
							'wxmsw28_xrc_vc_custom' ]
				return libs, pakLibs
			else:
				libs = [	'wxbase28d', 'wxbase28d_net', 'wxbase28d_xml', 'wxmsw28d_adv', 'wxmsw28d_aui', 'wxmsw28d_core',
							'wxmsw28d_html', 'wxmsw28d_media', 'wxmsw28d_qa', 'wxmsw28d_richtext', 'wxmsw28d_xrc' ]
				pakLibs = [ 'wxbase28d_net_vc_custom', 'wxbase28d_odbc_vc_custom', 'wxbase28d_vc_custom', 'wxbase28d_xml_vc_custom',
							'wxmsw28d_adv_vc_custom', 'wxmsw28d_aui_vc_custom', 'wxmsw28d_core_vc_custom', #'wxmsw28d_gl_vc_custom',
							'wxmsw28d_html_vc_custom', 'wxmsw28d_media_vc_custom', 'wxmsw28d_qa_vc_custom', 'wxmsw28d_richtext_vc_custom',
							'wxmsw28d_xrc_vc_custom' ]
				return libs, pakLibs
		elif self.platform == 'posix' and version == '2-8-8' :
			# ignore self.config, always uses release version
			libs = [	'wx_gtk2u_richtext-2.8', 'wx_gtk2u_aui-2.8', 'wx_gtk2u_xrc-2.8', 'wx_gtk2u_qa-2.8',
						'wx_gtk2u_html-2.8', 'wx_gtk2u_adv-2.8', 'wx_gtk2u_core-2.8', 'wx_baseu_xml-2.8',
						'wx_baseu_net-2.8', 'wx_baseu-2.8'	]
			return libs, []
#
#and GL ?
#===============================================================================
#	elif self.myPlatform == 'darwin' :
#		raise SCons.Errors.UserError("Uses=[\'%s\'] not supported on platform %s." % (elt, self.myPlatform) )
#	else :
#		if elt == 'wx2-8' :
#			if self.myConfig == 'release' :
#				env.ParseConfig('wx-config-gtk2-unicode-release-2.8 --cppflags --libs')
#			else:
#				env.ParseConfig('wx-config-gtk2-unicode-debug-2.8 --cppflags --libs')
#		elif elt == 'wxgl2-8' :
#			if self.myConfig == 'release' :
#				env.ParseConfig('wx-config-gtk2-unicode-release-2.8 --gl-libs')
#			else:
#				env.ParseConfig('wx-config-gtk2-unicode-debug-2.8 --gl-libs')
#		else :
#			raise SCons.Errors.UserError("Uses=[\'%s\'] not supported on platform %s." % (elt, self.myPlatform) )
#===============================================================================


class Use_wxWidgetsGL( IUse ):
	def getName( self ):
		return "wxgl"

	def getVersions( self ):
		return ['2-8-8']

	def getLIBS( self, version ):
		if self.platform == 'win32' and version == '2-8-8' :
			if self.config == 'release' :
				libs = [ 'wxmsw28_gl' ]
				pakLibs = [ 'wxmsw28_gl_vc_custom' ]
				return libs, pakLibs
			else:
				libs = [ 'wxmsw28d_gl' ]
				pakLibs = [ 'wxmsw28d_gl_vc_custom' ]
				return libs, pakLibs
		else :
			return None
###



#
class UseRepository :
	__verbosity		= None
#__platform		= None
#__config		= None

	__repository	= {}

	__allowedValues = [	'physx2-8-1' ]
	__alias			= {
			'physx'			: 'physx2-8-1'	}

	__initialized	= False

	@classmethod
	def getAll( self ):
		return [	Use_adl(), Use_blowfish(), Use_boost(), Use_bullet(), Use_cairo(), Use_colladadom(), Use_ffmpeg(), Use_glibmm(), Use_gstFFmpeg(), Use_glew(), Use_glu(),
					Use_glm(), Use_glut(), Use_gtest(), Use_gtkmm(), Use_gtkmmext(), Use_itk(), Use_opencollada(), Use_opengl(), Use_openil(), Use_qt(), Use_scintilla(),
					Use_sdl(), Use_sdlMixer(), Use_physfs(), Use_poppler(), Use_python(), Use_sigcpp(), Use_sofa(), Use_usb2brd(), Use_wxWidgets(), Use_wxWidgetsGL() ]

	@classmethod
	def initialize( self, sbf ):
		if self.__initialized == True :
			raise SCons.Errors.InternalError("Try to initialize UseRepository twice.")

		# Initializes verbosity, platform and config
		self.__verbosity	= sbf.myEnv.GetOption('verbosity')
#self.__platform	= sbf.myPlatform
#self.__config		= sbf.myConfig

		IUse.initialize(	sbf.myPlatform, sbf.myConfig,
							sbf.myCC, sbf.myCCVersionNumber, sbf.myIsExpressEdition, sbf.myCCVersion )

		#
		self.__initialized = True

	@classmethod
	def add(	self,
				listOfIUseImplementation ):

		# Initializes repository
		if self.__verbosity :
			print ("Adds in UseRepository :"),
		for use in listOfIUseImplementation :
			# Adds to repository
			name = use.getName()

			self.__repository[ name ] = use
			if self.__verbosity :
				print name,

			# Configures allowed values and alias
			versions = use.getVersions()
			if len(versions) == 0 :
				# This 'use' is for package without version
				# Configures allowed values
				self.__allowedValues.append( name )
			else :
				# This 'use' is for package with at least one explicit version number

				# Configures alias
				self.__alias[name] = name + versions[0]

				# Configures allowed values
				for version in versions :
					self.__allowedValues.append( name + version )

		self.__allowedValues = sorted(self.__allowedValues)
		if self.__verbosity :
			print


	@classmethod
	def isInitialized( self ):
		return self.__initialized

	@classmethod
	def getUse( self, name ):
		if name in self.__repository :
			return self.__repository[name]
		else:
			return None

	@classmethod
	def getAllowedValues( self ):
		return self.__allowedValues[:]

	@classmethod
	def getAlias( self ):
		return self.__alias.copy()



###### Options : validators and converters ######
def usesValidator( key, val, env ) :

	# Splits the string val to obtain a list of values (the words are separated by arbitrary strings of whitespace characters)
	list_of_values = val.split()

	invalid_values = [ value for value in list_of_values if value not in UseRepository.getAllowedValues() ] #OptionUses_allowedValues

	if len(invalid_values) > 0 :
		raise SCons.Errors.UserError("Invalid value(s) for option uses:%s" % invalid_values)


def usesConverter( val ) :
	list_of_values = convertToList( val )

	result = []

	alias = UseRepository.getAlias()							# @todo OPTME, a copy is done !!!

	for value in list_of_values :
		if value in alias:
			# Converts incoming value and appends to result
			result.append( alias[value] )
		else :
			# Appends to result
			result.append( value )

	return result

###### use_package (see option named 'uses') ######

class Use_glibmm( IUse ):

	def getName( self ):
		return 'glibmm'

	def getVersions( self ):
		return [ '2-26-0' ]


	def getCPPPATH( self, version ):
		if self.platform == 'win32' :
			gtkmmCppPath = [ 'lib/glibmm-2.4/include', 'include/glibmm-2.4' ]

			gtkCppPath = [ 'lib/glib-2.0/include', 'include/glib-2.0' ]

			path =	[ os.path.join(gtkmmConfig.getGtkmmBasePath(), item)	for item in gtkmmCppPath ]
			path +=	[ os.path.join(gtkmmConfig.getBasePath(), item)	for item in gtkCppPath ]

			return path
		elif self.platform == 'posix':
			gtkmmCppPath	= [	'/usr/include/glibmm-2.4', '/usr/lib64/glibmm-2.4/include' ]

			return gtkmmCppPath


	def getLIBS( self, version ):
		if self.platform == 'win32':
			libs = [ 'glib-2.0' ]

			if version in ['2-26-0']:
				if self.config == 'release' :
					# RELEASE
					if self.cc == 'cl' and self.ccVersionNumber >= 10.0000 :
						libs += [	'glibmm-vc100-2_4' ]
					elif self.cc == 'cl' and self.ccVersionNumber >= 9.0000 :
						libs += [	'glibmm-vc90-2_4' ]
					elif self.cc == 'cl' and self.ccVersionNumber >= 8.0000 :
						libs += [	'glibmm-vc80-2_4' ]
				else:
					# DEBUG
					if self.cc == 'cl' and self.ccVersionNumber >= 10.0000 :
						libs += [	'glibmm-vc100-d-2_4' ]
					elif self.cc == 'cl' and self.ccVersionNumber >= 9.0000 :
						libs += [	'glibmm-vc90-d-2_4' ]
					elif self.cc == 'cl' and self.ccVersionNumber >= 8.0000 :
						libs += [	'glibmm-vc80-d-2_4' ]
			else:
				return

			return libs, []

		elif self.platform == 'posix':
			gtkmm		= [	'glibmm-2.4', 'glib-2.0' ]
			return gtkmm, []


	def getLIBPATH( self, version ):
		libPath		= []
		pakLibPath	= []

		if self.platform == 'win32' :
			path = os.path.join( gtkmmConfig.getBasePath(), 'lib' )
			libPath.append( path )
		#else self.platform == 'posix':
		#	libPath += '/usr/lib64'

		return libPath, pakLibPath


	def getCPPFLAGS( self, version ):
		# compiler options
		if self.platform == 'win32':
			if version in ['2-26-0']:
				if self.cc == 'cl' and self.ccVersionNumber >= 9.0000 :
					return ['/wd4250']
				elif self.cc == 'cl' and self.ccVersionNumber >= 8.0000 :
					return ['/wd4250', '/wd4312']
			else:
				return ['/wd4250']
		elif self.platform == 'posix':
			return ['-Wl,--export-dynamic']

	def getPackageType( self ):
		return 'None'


# TODO: GTK_BASEPATH and GTKMM_BASEPATH documentation, package gtkmm ?
# @todo support pakLibs
#
# pkg-config gtkglext-1.0 --cflags --libs
# pkg-config gtkmm-2.4 --cflags --libs
# pkg-config gthread-2.0 --cflags --libs
# @todo fedora != ubuntu/debian
# @todo 64 vs 32

class Use_gtkmm( IUse ):

	def getName( self ):
		return 'gtkmm'

	def getVersions( self ):
		return [ '2-22-0-2', '2-16-0', '2-14-3', '2-14-1' ]


	def getCPPDEFINES( self, version ):
		# @todo uses version api (see SConsBuildFramework.py)
		versionNumber = int( version.replace('-', '') )
		return [ (self.getName().upper()+'_VERSION', versionNumber) ]

	def getCPPPATH( self, version ):
		if self.platform == 'win32' :
			gtkmmCppPath = [	'lib/glibmm-2.4/include', 'include/glibmm-2.4',
								'lib/giomm-2.4/include', 'include/giomm-2.4',
								'lib/gdkmm-2.4/include', 'include/gdkmm-2.4',
								'lib/gtkmm-2.4/include', 'include/gtkmm-2.4',
								'lib/libglademm-2.4/include', 'include/libglademm-2.4',
								'lib/libxml++-2.6/include', 'include/libxml++-2.6',
								'lib/sigc++-2.0/include', 'include/sigc++-2.0',
								'lib/pangomm-1.4/include', 'include/pangomm-1.4',
								'include/atkmm-1.6',
								'include/cairomm-1.0' ]

			gtkCppPath = [		'include/libglade-2.0',
								'lib/gtk-2.0/include', 'include/gtk-2.0',
								'include/pango-1.0',
								'include/atk-1.0',
								'lib/glib-2.0/include', 'include/glib-2.0',
								'include/gdk-pixbuf-2.0',
								'include/libxml2',
								'include/freetype2',
								'include/cairo',
								'include' ]

			path =	[ os.path.join(gtkmmConfig.getGtkmmBasePath(), item)	for item in gtkmmCppPath ]
			path +=	[ os.path.join(gtkmmConfig.getBasePath(), item)	for item in gtkCppPath ]

			return path
		elif self.platform == 'posix':
			gtkglextCppPath	= [	'/usr/include/gtkglext-1.0', '/usr/lib64/gtkglext-1.0/include' ]
			gtkmmCppPath	= [	'/usr/include/gtkmm-2.4', '/usr/lib64/gtkmm-2.4/include', '/usr/include/glibmm-2.4', '/usr/lib64/glibmm-2.4/include',
								'/usr/include/giomm-2.4', '/usr/lib64/giomm-2.4/include', '/usr/include/gdkmm-2.4', '/usr/lib64/gdkmm-2.4/include',
								'/usr/include/pangomm-1.4', '/usr/include/atkmm-1.6', '/usr/include/gtk-2.0', '/usr/include/sigc++-2.0',
								'/usr/lib64/sigc++-2.0/include', '/usr/include/glib-2.0', '/usr/lib64/glib-2.0/include', '/usr/lib64/gtk-2.0/include',
								'/usr/include/cairomm-1.0', '/usr/include/pango-1.0', '/usr/include/cairo', '/usr/include/pixman-1', '/usr/include/freetype2',
								'/usr/include/libpng12', '/usr/include/atk-1.0' ]

			return gtkglextCppPath + gtkmmCppPath



	def getLIBS( self, version ):
		if self.platform == 'win32':
			libs = [ 'glade-2.0', 'gtk-win32-2.0', 'gdk-win32-2.0', 'gdk_pixbuf-2.0',
					'pangowin32-1.0', 'pangocairo-1.0', 'pangoft2-1.0', 'pango-1.0',
					'atk-1.0', 'cairo',
					'gobject-2.0', 'gmodule-2.0', 'glib-2.0', 'gio-2.0', 'gthread-2.0',
					'intl' ]
			if version == '2-22-0-2':
				libs += [ 'libxml2', 'fontconfig' ]
			elif version in [ '2-16-0', '2-14-3', '2-14-1' ]:
				libs += [ 'libxml2', 'iconv' ]
			else:
				return

			if version in ['2-22-0-2', '2-16-0', '2-14-3']:
				if self.config == 'release' :
					# RELEASE
					if self.cc == 'cl' and self.ccVersionNumber >= 10.0000 :
						libs += [	'glademm-vc100-2_4', 'gdkmm-vc100-2_4', 'pangomm-vc100-1_4',
									'atkmm-vc100-1_6', 'cairomm-vc100-1_0',
									'glibmm-vc100-2_4', 'giomm-vc100-2_4',
									'xml++-vc100-2_6', 'sigc-vc100-2_0',
									'gtkmm-vc100-2_4' ]
					elif self.cc == 'cl' and self.ccVersionNumber >= 9.0000 :
						libs += [	'glademm-vc90-2_4', 'gdkmm-vc90-2_4', 'pangomm-vc90-1_4',
									'atkmm-vc90-1_6', 'cairomm-vc90-1_0',
									'glibmm-vc90-2_4', 'giomm-vc90-2_4',
									'xml++-vc90-2_6', 'sigc-vc90-2_0',
									'gtkmm-vc90-2_4' ]
					elif self.cc == 'cl' and self.ccVersionNumber >= 8.0000 :
						libs += [	'glademm-vc80-2_4', 'gdkmm-vc80-2_4', 'pangomm-vc80-1_4',
									'atkmm-vc80-1_6', 'cairomm-vc80-1_0',
									'glibmm-vc80-2_4', 'giomm-vc80-2_4',
									'xml++-vc80-2_6', 'sigc-vc80-2_0',
									'gtkmm-vc80-2_4' ]
				else:
					# DEBUG
					if self.cc == 'cl' and self.ccVersionNumber >= 10.0000 :
						libs += [	'glademm-vc100-d-2_4', 'gdkmm-vc100-d-2_4', 'pangomm-vc100-d-1_4',
									'atkmm-vc100-d-1_6', 'cairomm-vc100-d-1_0',
									'glibmm-vc100-d-2_4', 'giomm-vc100-d-2_4',
									'xml++-vc100-d-2_6', 'sigc-vc100-d-2_0',
									'gtkmm-vc100-d-2_4' ]
					elif self.cc == 'cl' and self.ccVersionNumber >= 9.0000 :
						libs += [	'glademm-vc90-d-2_4', 'gdkmm-vc90-d-2_4', 'pangomm-vc90-d-1_4',
									'atkmm-vc90-d-1_6', 'cairomm-vc90-d-1_0',
									'glibmm-vc90-d-2_4', 'giomm-vc90-d-2_4',
									'xml++-vc90-d-2_6', 'sigc-vc90-d-2_0',
									'gtkmm-vc90-d-2_4' ]
					elif self.cc == 'cl' and self.ccVersionNumber >= 8.0000 :
						libs += [	'glademm-vc80-d-2_4', 'gdkmm-vc80-d-2_4', 'pangomm-vc80-d-1_4',
									'atkmm-vc80-d-1_6', 'cairomm-vc80-d-1_0',
									'glibmm-vc80-d-2_4', 'giomm-vc80-d-2_4',
									'xml++-vc80-d-2_6', 'sigc-vc80-d-2_0',
									'gtkmm-vc80-d-2_4' ]
			elif version == '2-14-1':
				if self.config == 'release' :
					libs += [	'glademm-2.4', 'xml++-2.6', 'gtkmm-2.4', 'gdkmm-2.4', 'atkmm-1.6',
								'pangomm-1.4', 'glibmm-2.4', 'giomm-2.4', 'cairomm-1.0', 'sigc-2.0' ]
				else:
					libs += [	'glademm-2.4d', 'xml++-2.6d', 'gtkmm-2.4d', 'gdkmm-2.4d', 'atkmm-1.6d',
								'pangomm-1.4d', 'glibmm-2.4d', 'giomm-2.4d', 'cairomm-1.0d', 'sigc-2.0d' ]
			else:
				return

			return libs, []

		elif self.platform == 'posix':
			gtkglext	= [	'gtkglext-x11-1.0', 'gdkglext-x11-1.0',
							'GLU', 'GL', 'Xmu', 'Xt', 'SM', 'ICE',
							'pangox-1.0', 'X11' ]
			gtkmm		= [	'gtkmm-2.4', 'giomm-2.4', 'gdkmm-2.4', 'atkmm-1.6',
							'gtk-x11-2.0', 'pangomm-1.4', 'cairomm-1.0', 'glibmm-2.4',
							'sigc-2.0', 'gdk-x11-2.0', 'atk-1.0', 'gio-2.0',
							'pangoft2-1.0', 'gdk_pixbuf-2.0', 'pangocairo-1.0', 'cairo',
							'pango-1.0', 'freetype', 'fontconfig', 'gobject-2.0', 'gmodule-2.0',
							'glib-2.0' ]
			return gtkglext + gtkmm, []


	def getLIBPATH( self, version ):
		libPath		= []
		pakLibPath	= []

		if self.platform == 'win32' :
			path = os.path.join( gtkmmConfig.getBasePath(), 'lib' )
			libPath.append( path )
		#else self.platform == 'posix':
		#	libPath += '/usr/lib64'

		return libPath, pakLibPath


	def getCPPFLAGS( self, version ):
		# compiler options
		if self.platform == 'win32':
			if version in ['2-22-0-2', '2-16-0']:
				if self.cc == 'cl' and self.ccVersionNumber >= 9.0000 :
					return ['/wd4250']
				elif self.cc == 'cl' and self.ccVersionNumber >= 8.0000 :
					return ['/wd4250', '/wd4312']
			else:
				return ['/wd4250']
		elif self.platform == 'posix':
			return ['-Wl,--export-dynamic']


	def getPackageType( self ):
		return 'Full'

	def getRedist( self, version ):
		return []
		if self.platform == 'win32':
			if version == '2-22-0-2':
				if self.cc == 'cl' and self.ccVersionNumber >= 10.0000 :
					if self.config == 'release':
						return ['gtkmmRedist2-22-0-2_win32_cl10-0Exp.zip']
					else:
						return ['gtkmmRedist2-22-0-2_win32_cl10-0Exp_D.zip']
				elif self.cc == 'cl' and self.ccVersionNumber >= 9.0000 :
					if self.config == 'release':
						return ['gtkmmRedist2-22-0-2_win32_cl9-0Exp.zip']
					else:
						return ['gtkmmRedist2-22-0-2_win32_cl9-0Exp_D.zip']
				elif self.cc == 'cl' and self.ccVersionNumber >= 8.0000 :
					if self.config == 'release':
						return ['gtkmmRedist2-22-0-2_win32_cl8-0Exp.zip']
					else:
						return ['gtkmmRedist2-22-0-2_win32_cl8-0Exp_D.zip']
				else:
					SCons.Errors.UserError("Uses=[\'%s\'] not supported on platform %s." % (elt, self.myPlatform) )
			elif version == '2-16-0':
				if self.cc == 'cl' and self.ccVersionNumber >= 9.0000 :
					if self.config == 'release':
						return ['gtkmmRedist2-16-0-4_win32_cl9-0Exp.zip']
					else:
						return ['gtkmmRedist2-16-0-4_win32_cl9-0Exp_D.zip']
				elif self.cc == 'cl' and self.ccVersionNumber >= 8.0000 :
					if self.config == 'release':
						return ['gtkmmRedist2-16-0-4_win32_cl8-0Exp.zip']
					else:
						return ['gtkmmRedist2-16-0-4_win32_cl8-0Exp_D.zip']
				else:
					SCons.Errors.UserError("Uses=[\'%s\'] not supported on platform %s." % (elt, self.myPlatform) )


class Use_gtkmmext( IUse ):

	def getName( self ):
		return 'gtkmmext'

	def getVersions( self ):
		return [ '1-0' ]

	def getCPPFLAGS( self, version ):
		# compiler options
		if self.platform == 'win32':
			if self.cc == 'cl' and self.ccVersionNumber >= 8.0000 :
				return ['/vd2']
		else:
			return []


	def getPackageType( self ):
		return 'None'


class Use_sigcpp( IUse ):

	def getName( self ):
		return 'sigcpp'

	def getVersions( self ):
		return [ '2-8-2' ]


	def getCPPPATH( self, version ):
		if self.platform == 'win32' :
			sigcppPath = [	'lib/sigc++-2.0/include', 'include/sigc++-2.0' ]

			path = [ os.path.join(gtkmmConfig.getGtkmmBasePath(), item) for item in sigcppPath ]

			return path
		elif self.platform == 'posix':
			sigcppPath = [ '/usr/include/sigc++-2.0','/usr/lib64/sigc++-2.0/include' ]

			return sigcppPath



	def getLIBS( self, version ):
		if self.platform == 'win32':
			if version in ['2-8-2']:
				if self.config == 'release' :
					# RELEASE
					if self.cc == 'cl' and self.ccVersionNumber >= 10.0000 :
						libs = [ 'sigc-vc100-2_0' ]
					elif self.cc == 'cl' and self.ccVersionNumber >= 9.0000 :
						libs = [ 'sigc-vc90-2_0' ]
					elif self.cc == 'cl' and self.ccVersionNumber >= 8.0000 :
						libs = [ 'sigc-vc80-2_0' ]
				else:
					# DEBUG
					if self.cc == 'cl' and self.ccVersionNumber >= 10.0000 :
						libs = [ 'sigc-vc100-d-2_0' ]
					elif self.cc == 'cl' and self.ccVersionNumber >= 9.0000 :
						libs = [ 'sigc-vc90-d-2_0' ]
					elif self.cc == 'cl' and self.ccVersionNumber >= 8.0000 :
						libs = [ 'sigc-vc80-d-2_0' ]
			else:
				return

			return libs, []

		elif self.platform == 'posix':
			sigcpp = [ 'sigc-2.0' ]
			return sigcpp, []


	def getLIBPATH( self, version ):
		libPath		= []
		pakLibPath	= []

		if self.platform == 'win32' :
			path = os.path.join( gtkmmConfig.getBasePath(), 'lib' )
			libPath.append( path )
		#else self.platform == 'posix':
		#	libPath += '/usr/lib64'

		return libPath, pakLibPath


	def getPackageType( self ):
		return 'None'


def use_physx( self, lenv, elt ) :
	# Retrieves PHYSX_BASEPATH
	physxBasePath = getPathFromEnv('PHYSX_BASEPATH')
	if physxBasePath is None :
		raise SCons.Errors.UserError("Unable to configure '%s'." % elt)

	# Sets CPPPATH
	physxCppPath	=	[ 'SDKs\Foundation\include', 'SDKs\Physics\include', 'SDKs\PhysXLoader\include' ]
	physxCppPath	+=	[ 'SDKs\Cooking\include', 'SDKs\NxCharacter\include' ]

	if lenv.GetOption('weak_localext') :
		for cppPath in physxCppPath :
			lenv.AppendUnique( CCFLAGS = ['${INCPREFIX}' + os.path.join(physxBasePath, cppPath)] )
	else :
		for cppPath in physxCppPath :
			lenv.AppendUnique( CPPPATH = os.path.join(physxBasePath, cppPath) )

	# Sets LIBS and LIBPATH
	lenv.AppendUnique( LIBS = [	'PhysXLoader', 'NxCooking', 'NxCharacter' ] )
	if self.myPlatform == 'win32' :
		lenv.AppendUnique( LIBPATH = [ os.path.join(physxBasePath, 'SDKs\lib\Win32') ] )
	else :
		raise SCons.Errors.UserError("Uses=[\'%s\'] not supported on platform %s." % (elt, self.myPlatform) )


#===============================================================================
# #@todo Adds support to both ANSI and Unicode version of wx
# #@todo Adds support static/dynamic and db stuff (see http://www.wxwidgets.org/wiki/index.php/MSVC_.NET_Setup_Guide)
# def use_wxWidgets( self, lenv, elt ) :
#	if	self.myPlatform == 'win32' :
#
#		lenv.Append( CPPDEFINES = [ 'WXUSINGDLL', '__WIN95__' ] )
#
#		if self.myType == 'exec' and (not elt.startswith('wxgl')):
#			lenv.Append( LINKFLAGS = '/SUBSYSTEM:WINDOWS' )
#
#		if elt == 'wx2-8' :
#			if self.myConfig == 'release' :
#				lenv.Append( LIBS = [	'wxbase28', 'wxbase28_net', 'wxbase28_xml', 'wxmsw28_adv', 'wxmsw28_aui', 'wxmsw28_core',
#										'wxmsw28_html', 'wxmsw28_media', 'wxmsw28_qa', 'wxmsw28_richtext', 'wxmsw28_xrc'	] )
#									# wxbase28_odbc, wxmsw28_dbgrid
#			else :
#				lenv.Append( LIBS = [	'wxbase28d', 'wxbase28d_net', 'wxbase28d_xml', 'wxmsw28d_adv', 'wxmsw28d_aui', 'wxmsw28d_core',
#										'wxmsw28d_html', 'wxmsw28d_media', 'wxmsw28d_qa', 'wxmsw28d_richtext', 'wxmsw28d_xrc'	] )
#									# wxbase28d_odbc, wxmsw28d_dbgrid
#		elif elt == 'wxgl2-8' :
#			if self.myConfig == 'release' :
#				lenv.Append( LIBS = [	'wxmsw28_gl'	] )
#			else :
#				lenv.Append( LIBS = [	'wxmsw28d_gl'	] )
#		else :
#			raise SCons.Errors.UserError("Uses=[\'%s\'] not supported on platform %s." % (elt, self.myPlatform) )
#	elif self.myPlatform == 'darwin' :
#		raise SCons.Errors.UserError("Uses=[\'%s\'] not supported on platform %s." % (elt, self.myPlatform) )
#	else :
#		if elt == 'wx2-8' :
#			if self.myConfig == 'release' :
#				env.ParseConfig('wx-config-gtk2-unicode-release-2.8 --cppflags --libs')
#			else:
#				env.ParseConfig('wx-config-gtk2-unicode-debug-2.8 --cppflags --libs')
#		elif elt == 'wxgl2-8' :
#			if self.myConfig == 'release' :
#				env.ParseConfig('wx-config-gtk2-unicode-release-2.8 --gl-libs')
#			else:
#				env.ParseConfig('wx-config-gtk2-unicode-debug-2.8 --gl-libs')
#		else :
#			raise SCons.Errors.UserError("Uses=[\'%s\'] not supported on platform %s." % (elt, self.myPlatform) )
#===============================================================================



def uses( self, lenv, uses, skipLinkStageConfiguration = False ):
	#
#print '%s uses: %s' % (lenv['sbf_project'], lenv['uses'])
	for elt in uses :
		# Converts to lower case
		elt = string.lower( elt )

		# @todo FIXME hack for wx @todo move to IUse getLINKFLAGS()
		if skipLinkStageConfiguration == False :
			if self.myPlatform == 'win32' and elt == 'wx2-8-8' and self.myType == 'exec' :
				lenv.Append( LINKFLAGS = '/SUBSYSTEM:WINDOWS' )

		### configure PhysX ###
		if elt == 'physx2-8-1' :
			use_physx( self, lenv, elt )

#===============================================================================
#		### configure wxWidgets ###
#		elif elt in ['wx2-8', 'wxgl2-8'] :
#			use_wxWidgets( self, lenv, elt )
#===============================================================================

		### Updates environment using UseRepository
		else :
#print "incoming use : %s", elt
			useNameVersion = elt

			useName, useVersion = splitUsesName( useNameVersion )
			#print useNameVersion, useName, useVersion
			use = UseRepository.getUse( useName )

			if use:
				# Tests if the version is supported
				supportedVersions = use.getVersions()
				if (len(supportedVersions) == 0) or (useVersion in supportedVersions) :
					# Configures environment with the 'use'
					use( useVersion, lenv, skipLinkStageConfiguration )
				else :
					raise SCons.Errors.UserError("Uses=[\'%s\'] version %s not supported." % (useNameVersion, useVersion) )
			else :
				raise SCons.Errors.UserError("Unknown uses=['%s']" % useNameVersion)
