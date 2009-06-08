# SConsBuildFramework - Copyright (C) 2005, 2007, 2008, 2009, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

import os
import re
import sys
import string
import SCons.Errors

from sbfUtils import getPathFromEnv, convertToList



# @todo better place (should be shared with bootstrap.py)
def getRegistry( key, subkey = '' ):
	# @todo import at this place is not recommended
	import win32api
	import win32con
	try:
		regKey = win32api.RegOpenKey( win32con.HKEY_LOCAL_MACHINE, key )
		value, dataType = win32api.RegQueryValueEx( regKey, subkey )
		regKey.Close()
		return value
	except:
		return ''

def getInstallPath( key, subkey = '', text = '' ):
	value = getRegistry( key, subkey )
	if len(value) > 0:
		print ( '%s is installed in directory : %s' % (text, value) )
	else:
		print ( '%s is not installed' % text )
	return os.path.normpath(value)


#@todo moves to sbfConfig.py ?
class sofaConfig:
	__basePath = None

	@classmethod
	def __initialize( cls ):
		# Retrieves SOFA_PATH
		cls.__basePath = getPathFromEnv('SOFA_PATH')

		if cls.__basePath is None:
			raise SCons.Errors.UserError("Unable to configure sofa.\nSOFA_PATH environment variable must be defined.")

	@classmethod
	def getBasePath( cls ):
		if cls.__basePath is None:
			cls.__initialize()
		return cls.__basePath


class gtkConfig:
	__gtkBasePath		= None
	__gtkmmBasePath		= None

	@classmethod
	def __initialize( cls ):
		if sys.platform == 'win32':
			# Retrieves gtkmm path and version from windows registry
			gtkmmRegistryPath = 'SOFTWARE\\gtkmm\\2.4'
			gtkmmBasePath = getInstallPath( gtkmmRegistryPath, 'Path', 'gtkmm' )
			if len(gtkmmBasePath) > 0:
				version = getRegistry( gtkmmRegistryPath, 'Version' )
				print ( 'Assumes gtk and gtkmm installed in the same directory.\nFound gtkmm version: %s\n' % version )
				cls.__gtkBasePath = gtkmmBasePath
				cls.__gtkmmBasePath = gtkmmBasePath

		if cls.__gtkBasePath is None:
			# Retrieves GTK_BASEPATH
			cls.__gtkBasePath	= getPathFromEnv('GTK_BASEPATH')

		if cls.__gtkmmBasePath is None:
			# Retrieves GTKMM_BASEPATH
			cls.__gtkmmBasePath	= getPathFromEnv('GTKMM_BASEPATH')

		# Post-conditions
		if cls.__gtkBasePath is None:
			raise SCons.Errors.UserError("Unable to configure gtk.")

		if cls.__gtkmmBasePath is None:
			raise SCons.Errors.UserError("Unable to configure gtkmm.")

	@classmethod
	def getBasePath( cls ):
		if cls.__gtkBasePath is None:
			cls.__initialize()
		return cls.__gtkBasePath

	@classmethod
	def getGtkmmBasePath( cls ):
		if cls.__gtkmmBasePath is None:
			cls.__initialize()
		return cls.__gtkmmBasePath


#===============================================================================
# OptionUses_allowedValues = [	### @todo allow special values like '', 'none', 'all'
#					'boost1-34-1', 'cairo1-2-6', 'cairomm1-2-4', 'colladadom2-0', 'glu', 'glut', 'gtkmm2-14', 'itk3-4-0', 'ode', 'opengl',
#					'openil', 'openilu', 'physx2-8-1', 'sdl']
#					# cg|cgFX|imageMagick6|imageMagick++6
#===============================================================================
#OptionUses_allowedValues = [	### @todo allow special values like '', 'none', 'all'
#					 ]
					# cg|cgFX|imageMagick6|imageMagick++6

#===============================================================================
# OptionUses_alias = {
#		'boost'			: 'boost1-34-1',
#		'cairo'			: 'cairo1-2-6',
#		'cairomm'		: 'cairomm1-2-4',
#		'colladadom'	: 'colladadom2-0',
#		'gtkmm'			: 'gtkmm2-14',
#		'itk'			: 'itk3-4-0',
#		'physx'			: 'physx2-8-1',
#		'wx'			: 'wx2-8-8',
#		'wxgl'			: 'wxgl2-8-8' }
#===============================================================================

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


	def getCPPDEFINES( self, version ):
		return []

	def getCPPFLAGS( self, version ):
		return []

	def getCPPPATH( self, version ):
		return []


	def getLIBS( self, version ):
		return [], []

	def getLIBPATH( self, version ):
		return [], []


	def getLicences( self, version ):															# @todo implements for derived
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
		else :
			raise SCons.Errors.UserError("Uses=[\'%s\'] not supported on platform %s (see CPPDEFINES)." % (useNameVersion, self.platform) )

		# CPPFLAGS
		cppflags = self.getCPPFLAGS( useVersion )
		if cppflags != None :
			if len(cppflags) > 0 :
				env.AppendUnique( CPPFLAGS = cppflags )
		else :
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
				else :
					env.AppendUnique( CPPPATH = cpppathAbs )
		else :
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
		else :
			raise SCons.Errors.UserError("Uses=[\'%s\'] not supported on platform %s (see LIBPATH)." % (useNameVersion, self.platform) )



### Several IUse implementation ###

class Use_boost( IUse ):
	def getName( self ):
		return 'boost'

	def getVersions( self ):
		return [ '1-38-0', '1-34-1' ]

	def getCPPDEFINES( self, version ):
		if self.platform == 'win32':
			#if version in set( [ '1-38-0', '1-34-1' ] ) :
			return [ 'BOOST_ALL_DYN_LINK' ]
		else:
			return []

	def getCPPPATH( self, version ):
		if self.platform == 'win32' and version == '1-38-0' :
			return [ 'boost1-38-0' ]
		else:
			return []

	# @todo boost only for vc80, checks compiler and compiler version ?
	def getLIBS( self, version ):
		if self.platform == 'win32' :
			if version == '1-38-0':
				# autolinking, so nothing to do.
				if self.config == 'release' :
					pakLibs = [	'boost_date_time-vc80-mt-1_38', 'boost_filesystem-vc80-mt-1_38', 'boost_graph-vc80-mt-1_38',
								'boost_iostreams-vc80-mt-1_38', 'boost_math_c99-vc80-mt-1_38', 'boost_math_c99f-vc80-mt-1_38',
								'boost_math_c99l-vc80-mt-1_38', 'boost_math_tr1-vc80-mt-1_38', 'boost_math_tr1f-vc80-mt-1_38',
								'boost_math_tr1l-vc80-mt-1_38', 'boost_prg_exec_monitor-vc80-mt-1_38', 'boost_program_options-vc80-mt-1_38',
								'boost_python-vc80-mt-1_38', 'boost_regex-vc80-mt-1_38', 'boost_serialization-vc80-mt-1_38',
								'boost_signals-vc80-mt-1_38', 'boost_system-vc80-mt-1_38', 'boost_thread-vc80-mt-1_38',
								'boost_unit_test_framework-vc80-mt-1_38', 'boost_wave-vc80-mt-1_38', 'boost_wserialization-vc80-mt-1_38' ]
				else:
					pakLibs = [	'boost_date_time-vc80-mt-gd-1_38', 'boost_filesystem-vc80-mt-gd-1_38', 'boost_graph-vc80-mt-gd-1_38',
								'boost_iostreams-vc80-mt-gd-1_38', 'boost_math_c99-vc80-mt-gd-1_38', 'boost_math_c99f-vc80-mt-gd-1_38',
								'boost_math_c99l-vc80-mt-gd-1_38', 'boost_math_tr1-vc80-mt-gd-1_38', 'boost_math_tr1f-vc80-mt-gd-1_38',
								'boost_math_tr1l-vc80-mt-gd-1_38', 'boost_prg_exec_monitor-vc80-mt-gd-1_38', 'boost_program_options-vc80-mt-gd-1_38',
								'boost_python-vc80-mt-gd-1_38', 'boost_regex-vc80-mt-gd-1_38', 'boost_serialization-vc80-mt-gd-1_38',
								'boost_signals-vc80-mt-gd-1_38', 'boost_system-vc80-mt-gd-1_38', 'boost_thread-vc80-mt-gd-1_38',
								'boost_unit_test_framework-vc80-mt-gd-1_38', 'boost_wave-vc80-mt-gd-1_38', 'boost_wserialization-vc80-mt-gd-1_38' ]
				return [], pakLibs
			elif version == '1-34-1':
				if self.config == 'release' :
					libs = [	'boost_date_time-vc80-mt-1_34_1', 'boost_filesystem-vc80-mt-1_34_1', 'boost_graph-vc80-mt-1_34_1',
								'boost_iostreams-vc80-mt-1_34_1', 'boost_prg_exec_monitor-vc80-mt-1_34_1', 'boost_program_options-vc80-mt-1_34_1',
								'boost_python-vc80-mt-1_34_1', 'boost_regex-vc80-mt-1_34_1', 'boost_serialization-vc80-mt-1_34_1',
								'boost_signals-vc80-mt-1_34_1', 'boost_thread-vc80-mt-1_34_1', 'boost_unit_test_framework-vc80-mt-1_34_1',
								'boost_wave-vc80-mt-1_34_1', 'boost_wserialization-vc80-mt-1_34_1' ]
					return libs, libs
				else:
					libs = [	'boost_date_time-vc80-mt-gd-1_34_1', 'boost_filesystem-vc80-mt-gd-1_34_1', 'boost_graph-vc80-mt-gd-1_34_1',
								'boost_iostreams-vc80-mt-gd-1_34_1', 'boost_prg_exec_monitor-vc80-mt-gd-1_34_1', 'boost_program_options-vc80-mt-gd-1_34_1',
								'boost_python-vc80-mt-gd-1_34_1', 'boost_regex-vc80-mt-gd-1_34_1', 'boost_serialization-vc80-mt-gd-1_34_1',
								'boost_signals-vc80-mt-gd-1_34_1', 'boost_thread-vc80-mt-gd-1_34_1', 'boost_unit_test_framework-vc80-mt-gd-1_34_1',
								'boost_wave-vc80-mt-gd-1_34_1', 'boost_wserialization-vc80-mt-gd-1_34_1' ]
					return libs, libs
		elif self.platform == 'posix' and version == '1-34-1':
			libs = [	'libboost_date_time-mt',	'libboost_filesystem-mt',		'libboost_graph-mt',
						'libboost_iostreams-mt',	'libboost_prg_exec_monitor-mt',	'libboost_program_options-mt',
						'libboost_regex-mt',		'libboost_serialization-mt',
#						'libboost_python-mt',		'libboost_regex-mt',			'libboost_serialization-mt',
						'libboost_signals-mt',		'libboost_thread-mt',			'libboost_unit_test_framework-mt',
						'libboost_wave-mt',			'libboost_wserialization-mt'	]
			return libs, libs



#		lenv.AppendUnique( LIBS = ['cairo', 'fontconfig', 'freetype', 'png', 'z' ] )
class Use_cairo( IUse ):

	def getName( self ):
		return 'cairo'

	def getVersions( self ):
		return ['1-8-6', '1-7-6', '1-2-6']


	def getCPPFLAGS( self, version ):
		if self.platform == 'win32' :
			return [ '/vd2', '/wd4250' ]
		else:
			return []

	def getCPPPATH( self, version ):
		if self.platform == 'win32' :
			# Sets CPPPATH
			gtkCppPath = [ 'include/cairo', 'include' ]
			cppPath = []
			for path in gtkCppPath :
				cppPath.append( os.path.join(gtkConfig.getBasePath(), path) )
			return cppPath
		elif self.platform == 'posix' :
			# Sets CPPPATH
			cppPath = [	'/usr/include/cairo', '/usr/include/pixman-1', '/usr/include/freetype2',
						'/usr/include/libpng12'	]
			return cppPath

	def getLIBS( self, version ):
		if (self.platform == 'win32') and (version in ['1-8-6', '1-7-6', '1-2-6']) :
			libs = [ 'cairo' ]
			pakLibs = [ 'libcairo-2' ]
			return libs, pakLibs
		elif self.platform == 'posix' :
			libs = [ 'cairo' ]
			return libs, libs

	def getLIBPATH( self, version ):
		if self.platform == 'win32' :
			return [ os.path.join(gtkConfig.getBasePath(), 'lib') ], [ os.path.join(gtkConfig.getBasePath(), 'bin') ]
		elif self.platform == 'posix' :
			return [], []


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


class Use_opengl( IUse ):
	def getName( self ):
		return "opengl"

	def getLIBS( self, version ):
		if self.platform == 'win32' :
			# opengl32	: OpenGL and wgl functions
			# gdi32		: Pixelformat and swap related functions
			libs = [ 'opengl32', 'gdi32']
			return libs, []
		else:
			libs = ['GL']
			return libs, []



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

	def getLIBS( self, version ):
		if self.platform == 'win32' :
			if self.config == 'release' :
				libs = ['DevIL']
				return libs, libs
			else:
				libs = ['DevIL']
				return libs, libs #['DevILd'] @todo openil should be compiled in debug on win32 platform
		else:
			if self.config == 'release' :
				libs = ['IL']
				return libs, libs
			else :
				libs = ['IL']
				# @remark openil not compiled in debug in ubuntu 8.10
				#libs = ['ILd']
				return libs, libs


class Use_openilu( IUse ):
	def getName( self ):
		return "openilu"

	def getLIBS( self, version ):
		if self.platform == 'win32' :
			if self.config == 'release' :
				libs = ['ILU']
				return libs, libs
			else :
				libs = ['ILU']
				return libs, libs #['ILUd'] @todo openilu should be compiled in debug on win32 platform
		else:
			if self.config == 'release' :
				libs = ['ILU']
				return libs, libs
			else :
				# @remark openil not compiled in debug in ubuntu 8.10
				libs = ['ILU']
				#libs = ['ILUd']
				return libs, libs


# @remarks sdl-config --cflags --libs
class Use_sdl( IUse ):
	def getName( self ):
		return "sdl"

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
		return [ '/usr/lib' ], [ '/usr/lib' ]


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


class Use_glut( IUse ):
	def getName(self ):
		return "glut"

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

	def getLIBS( self, version ):
		if self.platform == 'win32':
			if self.config == 'release':
				libs = ['gtest']
				return libs, []
			else:
				libs = ['gtestd']
				return libs, []
		else:
			libs = ['gtest']
			return libs, []


# @todo SOFA_PATH documentation
# TODO: packages sofa into a localExt and adapts the following code to be more sbf friendly
class Use_sofa( IUse ):

	def getName( self ):
		return 'sofa'

	def getCPPDEFINES( self, version ):
		return ['SOFA_DOUBLE', 'SOFA_DEV']

	def getCPPFLAGS( self, version ):
		if self.platform == 'win32' :
			return ['/wd4250', '/wd4251', '/wd4275', '/wd4996']
		else:
			return []

	def getCPPPATH( self, version ):
		cppPath = [	os.path.join(sofaConfig.getBasePath(), 'modules'),
					os.path.join(sofaConfig.getBasePath(), 'framework'),
					os.path.join(sofaConfig.getBasePath(), 'include'),
					os.path.join(sofaConfig.getBasePath(), 'extlibs/miniFlowVR/include') ]

		if self.platform == 'posix':
			cppPath += ['/usr/include/libxml2']

		return cppPath

	def getLIBS( self, version ):
		if self.platform == 'win32' :
			libs = ['glew32', 'Gdi32', 'Shell32']
			pakLibs = []
			if self.config == 'release' :
				libs += ['miniFlowVR', 'newmat', 'sofaautomatescheduler', 'sofacomponent', 'sofacomponentbase', 'sofacomponentbehaviormodel', 'sofacomponentcollision', 'sofacomponentconstraint', 'sofacomponentcontextobject', 'sofacomponentcontroller', 'sofacomponentfem', 'sofacomponentforcefield', 'sofacomponentinteractionforcefield', 'sofacomponentlinearsolver', 'sofacomponentmapping', 'sofacomponentmass', 'sofacomponentmastersolver', 'sofacomponentmisc', 'sofacomponentodesolver', 'sofacomponentvisualmodel',
						 'sofacore', 'sofadefaulttype', 'sofahelper', 'sofasimulation', 'sofatree', 'tinyxml']
				pakLibs += ['sofaautomatescheduler', 'sofacomponent', 'sofacomponentbase', 'sofacomponentbehaviormodel', 'sofacomponentcollision', 'sofacomponentconstraint', 'sofacomponentcontextobject', 'sofacomponentcontroller', 'sofacomponentfem', 'sofacomponentforcefield', 'sofacomponentinteractionforcefield', 'sofacomponentlinearsolver', 'sofacomponentmapping', 'sofacomponentmass', 'sofacomponentmastersolver', 'sofacomponentmisc', 'sofacomponentodesolver', 'sofacomponentvisualmodel',
							'sofacore', 'sofadefaulttype', 'sofahelper', 'sofasimulation', 'sofatree']
			else:
				libs += ['miniFlowVRd', 'newmatd', 'sofaautomateschedulerd', 'sofacomponentd', 'sofacomponentbased', 'sofacomponentbehaviormodeld', 'sofacomponentcollisiond', 'sofacomponentconstraintd', 'sofacomponentcontextobjectd', 'sofacomponentcontrollerd', 'sofacomponentfemd', 'sofacomponentforcefieldd', 'sofacomponentinteractionforcefieldd', 'sofacomponentlinearsolverd', 'sofacomponentmappingd', 'sofacomponentmassd', 'sofacomponentmastersolverd', 'sofacomponentmiscd', 'sofacomponentodesolverd', 'sofacomponentvisualmodeld',
						 'sofacored', 'sofadefaulttyped', 'sofahelperd', 'sofasimulationd', 'sofatreed']
				pakLibs += ['sofaautomateschedulerd', 'sofacomponentd', 'sofacomponentbased', 'sofacomponentbehaviormodeld', 'sofacomponentcollisiond', 'sofacomponentconstraintd', 'sofacomponentcontextobjectd', 'sofacomponentcontrollerd', 'sofacomponentfemd', 'sofacomponentforcefieldd', 'sofacomponentinteractionforcefieldd', 'sofacomponentlinearsolverd',  'sofacomponentmappingd', 'sofacomponentmassd', 'sofacomponentmastersolverd', 'sofacomponentmiscd', 'sofacomponentodesolverd', 'sofacomponentvisualmodeld',
							'sofacored', 'sofadefaulttyped', 'sofahelperd', 'sofasimulationd', 'sofatreed', 'tinyxmld']
			return libs, pakLibs
		elif self.platform == 'posix' :
			libs = ['xml2', 'z']
			pakLibs = []
			libs += ['libminiFlowVR', 'libnewmat', 'libsofaautomatescheduler', 'libsofacomponent', 'libsofacomponentbase', 'libsofacomponentbehaviormodel', 'libsofacomponentcollision', 'libsofacomponentconstraint', 'libsofacomponentcontextobject', 'libsofacomponentcontroller', 'libsofacomponentfem', 'libsofacomponentforcefield', 'libsofacomponentinteractionforcefield', 'libsofacomponentlinearsolver', 'libsofacomponentmapping', 'libsofacomponentmass', 'libsofacomponentmastersolver', 'libsofacomponentmisc', 'libsofacomponentodesolver', 'libsofacomponentvisualmodel',
					'libsofacore', 'libsofadefaulttype', 'libsofahelper', 'libsofasimulation', 'libsofatree']
			pakLibs += ['libminiFlowVR', 'libnewmat', 'libsofaautomatescheduler', 'libsofacomponent', 'libsofacomponentbase', 'libsofacomponentbehaviormodel', 'libsofacomponentcollision', 'libsofacomponentconstraint', 'libsofacomponentcontextobject', 'libsofacomponentcontroller', 'libsofacomponentfem', 'libsofacomponentforcefield', 'libsofacomponentinteractionforcefield', 'libsofacomponentlinearsolver', 'libsofacomponentmapping', 'libsofacomponentmass', 'libsofacomponentmastersolver', 'libsofacomponentmisc', 'libsofacomponentodesolver', 'libsofacomponentvisualmodel',
						'libsofacore', 'libsofadefaulttype', 'libsofahelper', 'libsofasimulation', 'libsofatree']
			return libs, pakLibs

	def getLIBPATH( self, version ):
		libPath		= []
		pakLibPath	= []

		if self.platform == 'win32' :
			if self.config == 'release' :
				if self.cc == 'cl' and self.ccVersionNumber >= 9.0000 :
					path = os.path.join( sofaConfig.getBasePath(), 'lib/win32/ReleaseVC9')
				elif self.cc == 'cl' and self.ccVersionNumber >= 8.0000 :
					path = os.path.join( sofaConfig.getBasePath(), 'lib/win32/ReleaseVC8')
				libPath.append( path )
				pakLibPath.append( path )
			else :
				if self.cc == 'cl' and self.ccVersionNumber >= 9.0000 :
					path = os.path.join( sofaConfig.getBasePath(), 'lib/win32/DebugVC9')
				elif self.cc == 'cl' and self.ccVersionNumber >= 8.0000 :
					path = os.path.join( sofaConfig.getBasePath(), 'lib/win32/DebugVC8')
				libPath.append( path )
				pakLibPath.append( path )

			libPath.append( os.path.join( sofaConfig.getBasePath(), 'lib/win32/Common' ) )
			return libPath, pakLibPath

		elif self.platform == 'posix' :
			path = os.path.join( sofaConfig.getBasePath(), 'lib/linux')
			libPath.append( path )
			pakLibPath.append( path )
			return libPath, pakLibPath



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

	__allowedValues = [	'cairomm1-2-4', 'ode', 'physx2-8-1' ]
	__alias			= {
			'cairomm'		: 'cairomm1-2-4',
			'physx'			: 'physx2-8-1'	}

	__initialized	= False

	@classmethod
	def getAll( self ):
		return [	Use_boost(), Use_cairo(), Use_colladadom(), Use_glu(), Use_glut(), Use_gtest(), Use_gtkmm(), Use_opengl(), Use_itk(),
					Use_openil(), Use_openilu(), Use_sdl(), Use_sofa(), Use_wxWidgets(), Use_wxWidgetsGL()	]

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
	# Extracts (name, version) from 'nameVersion', 'name version' or 'name'
	def extract( self, name ):
		nameMatch = re.compile( r'^([a-zA-Z]+)[ \t]*([\d-]*)' ).match(name)					# @todo improves pattern to check version format
		if nameMatch == None :
			raise SCons.Errors.UserError("uses=['%s']. The following schemas must be used ['name'], ['nameVersion'] or ['name version']." % name)
		else:
			return nameMatch.groups()

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
#=======================================================================================================================
#	for value in list_of_values :
#		if value not in allowed_values :
#			invalid_values += ' ' + value
#=======================================================================================================================
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
def use_cairomm( self, lenv, elt ) :
	# Configures cairo
# ??? use_cairo( self, lenv, elt ) ???

	# Retrieves GTKMM_BASEPATH
	gtkmmBasePath	= getPathFromEnv('GTKMM_BASEPATH')
	if gtkmmBasePath is None :
		raise SCons.Errors.UserError("Unable to configure '%s'." % elt)

	# Sets CPPPATH
	gtkmmCppPath = ['include/cairomm-1.0']

	if lenv.GetOption('weak_localext') :
		for cppPath in gtkmmCppPath :
			lenv.AppendUnique( CCFLAGS = ['${INCPREFIX}' + os.path.join(gtkmmBasePath, cppPath)] )
	else :
		for cppPath in gtkmmCppPath :
			lenv.AppendUnique( CPPPATH = os.path.join(gtkmmBasePath, cppPath) )

	# Sets LIBS and LIBPATH
	if self.myPlatform == 'win32' :
		if self.myConfig == 'release' :
			lenv.AppendUnique( LIBS = [	'cairomm-1.0' ] )
		else:
			lenv.AppendUnique( LIBS = [	'cairomm-1.0d' ] )
#			lenv.AppendUnique( LIBS = [	'cairomm-vc80-1_0' ] )
#		else:
#			lenv.AppendUnique( LIBS = [	'cairomm-vc80-d-1_0' ] )

		lenv.AppendUnique( LIBPATH = [ os.path.join(gtkmmBasePath, 'lib') ] )
	else :
		raise SCons.Errors.UserError("Uses=[\'%s\'] not supported on platform %s." % (elt, self.myPlatform) )



# TODO: GTK_BASEPATH and GTKMM_BASEPATH documentation, package gtkmm ?
# @todo support pakLibs
class Use_gtkmm( IUse ):

	def getName( self ):
		return 'gtkmm'

	def getVersions( self ):
		# @todo Don't forget to check SconsBuildFramework.py:buildProject() : usesSet = usesSet.difference(...
		return [ '2-16-0', '2-14-3', '2-14-1' ]


	def getCPPPATH( self, version ):
		gtkmmCppPath = [	'lib/glibmm-2.4/include', 'include/glibmm-2.4',
							'lib/giomm-2.4/include', 'include/giomm-2.4',
							'lib/gtkmm-2.4/include', 'include/gtkmm-2.4',
							'lib/gdkmm-2.4/include', 'include/gdkmm-2.4',
							'lib/libglademm-2.4/include', 'include/libglademm-2.4',
							'lib/libxml++-2.6/include', 'include/libxml++-2.6',
							'lib/sigc++-2.0/include', 'include/sigc++-2.0',
							'include/pangomm-1.4', 'include/atkmm-1.6', 'include/cairomm-1.0' ]

		gtkCppPath = [		'lib/gtkglext-1.0/include', 'include/gtkglext-1.0', 'include/libglade-2.0', 'lib/gtk-2.0/include',
							'include/gtk-2.0', 'include/pango-1.0', 'include/atk-1.0', 'lib/glib-2.0/include',
							'include/glib-2.0', 'include/libxml2', 'include/cairo', 'include' ]

		path =	[ os.path.join(gtkConfig.getGtkmmBasePath(), item)	for item in gtkmmCppPath ]
		path +=	[ os.path.join(gtkConfig.getBasePath(), item)	for item in gtkCppPath ]

		return path


	def getLIBS( self, version ):
		if self.platform == 'win32' :
			libs = ['glade-2.0',
					'gtk-win32-2.0', 'libxml2', 'gdk-win32-2.0', 'atk-1.0', 'gdk_pixbuf-2.0',
					'pangowin32-1.0', 'pangocairo-1.0', 'pango-1.0', 'cairo', 'gobject-2.0',
					'gmodule-2.0', 'glib-2.0', 'gio-2.0', 'gthread-2.0', 'intl', 'iconv']
			pakLibs = []

			if version in ['2-16-0', '2-14-3']:
				if self.config == 'release' :
					if self.cc == 'cl' and self.ccVersionNumber >= 9.0000 :
						libs += [	'glademm-vc90-2_4', 'xml++-vc90-2_6', 'gtkmm-vc90-2_4', 'gdkmm-vc90-2_4', 'atkmm-vc90-1_6',
									'pangomm-vc90-1_4', 'glibmm-vc90-2_4', 'giomm-vc90-2_4', 'cairomm-vc90-1_0', 'sigc-vc90-2_0' ]
					elif self.cc == 'cl' and self.ccVersionNumber >= 8.0000 :
						libs += [	'glademm-vc80-2_4', 'xml++-vc80-2_6', 'gtkmm-vc80-2_4', 'gdkmm-vc80-2_4', 'atkmm-vc80-1_6',
									'pangomm-vc80-1_4', 'glibmm-vc80-2_4', 'giomm-vc80-2_4', 'cairomm-vc80-1_0', 'sigc-vc80-2_0' ]
				else:
					if self.cc == 'cl' and self.ccVersionNumber >= 9.0000 :
						libs += [	'glademm-vc90-d-2_4', 'xml++-vc90-d-2_6', 'gtkmm-vc90-d-2_4', 'gdkmm-vc90-d-2_4', 'atkmm-vc90-d-1_6',
									'pangomm-vc90-d-1_4', 'glibmm-vc90-d-2_4', 'giomm-vc90-d-2_4', 'cairomm-vc90-d-1_0', 'sigc-vc90-d-2_0' ]
					elif self.cc == 'cl' and self.ccVersionNumber >= 8.0000 :
						libs += [	'glademm-vc80-d-2_4', 'xml++-vc80-d-2_6', 'gtkmm-vc80-d-2_4', 'gdkmm-vc80-d-2_4', 'atkmm-vc80-d-1_6',
									'pangomm-vc80-d-1_4', 'glibmm-vc80-d-2_4', 'giomm-vc80-d-2_4', 'cairomm-vc80-d-1_0', 'sigc-vc80-d-2_0' ]
			elif version == '2-14-1':
				if self.config == 'release' :
					libs += [	'glademm-2.4', 'xml++-2.6', 'gtkmm-2.4', 'gdkmm-2.4', 'atkmm-1.6',
								'pangomm-1.4', 'glibmm-2.4', 'giomm-2.4', 'cairomm-1.0', 'sigc-2.0' ]
				else:
					libs += [	'glademm-2.4d', 'xml++-2.6d', 'gtkmm-2.4d', 'gdkmm-2.4d', 'atkmm-1.6d',
								'pangomm-1.4d', 'glibmm-2.4d', 'giomm-2.4d', 'cairomm-1.0d', 'sigc-2.0d' ]
			else:
				return

			return libs, pakLibs
		#if self.platform == 'posix' :
		#	pass
		#	lenv.ParseConfig('pkg-config gthread-2.0 --cflags --libs')
		#	lenv.ParseConfig('pkg-config gtkmm-2.4 --cflags --libs')
		#	lenv.ParseConfig('pkg-config gtkglext-1.0 --cflags --libs')



	def getLIBPATH( self, version ):
		libPath		= []
		pakLibPath	= []

		if self.platform == 'win32' :
			path = os.path.join( gtkConfig.getBasePath(), 'lib' )
			libPath.append( path )
			pakLibPath.append( path )

			path = os.path.join( gtkConfig.getGtkmmBasePath(), 'bin' )
			libPath.append( path )
			pakLibPath.append( path )

		return libPath, pakLibPath

	def getCPPFLAGS( self, version ):
		if self.platform == 'win32':
			if version == '2-16-0':
				if self.cc == 'cl' and self.ccVersionNumber >= 9.0000 :
					return ['/vd2', '/wd4250']
				elif self.cc == 'cl' and self.ccVersionNumber >= 8.0000 :
					return ['/vd2', '/wd4250', '/wd4312']
			else:
				return ['/vd2', '/wd4250']
		else:
			return []



# TODO: GTK_BASEPATH and GTKMM_BASEPATH documentation, package gtkmm ?
def use_gtkmm( self, lenv, elt ) :
	if self.myPlatform == 'posix' :
		lenv.ParseConfig('pkg-config gthread-2.0 --cflags --libs')
		lenv.ParseConfig('pkg-config gtkmm-2.4 --cflags --libs')
		lenv.ParseConfig('pkg-config gtkglext-1.0 --cflags --libs')
		return

	# Retrieves GTK_BASEPATH and GTKMM_BASEPATH
	gtkBasePath		= getPathFromEnv('GTK_BASEPATH')
	gtkmmBasePath	= getPathFromEnv('GTKMM_BASEPATH')
	if	(gtkBasePath is None) or (gtkmmBasePath is None ) :
		raise SCons.Errors.UserError("Unable to configure '%s'." % elt)

	# Sets CPPPATH
	gtkmmCppPath = ['lib/glibmm-2.4/include', 'include/glibmm-2.4',
					'lib/giomm-2.4/include', 'include/giomm-2.4',
					'lib/gtkmm-2.4/include', 'include/gtkmm-2.4',
					'lib/gdkmm-2.4/include', 'include/gdkmm-2.4',
					'lib/libglademm-2.4/include', 'include/libglademm-2.4',
					'lib/libxml++-2.6/include', 'include/libxml++-2.6',
					'lib/sigc++-2.0/include', 'include/sigc++-2.0',
					'include/pangomm-1.4', 'include/atkmm-1.6', 'include/cairomm-1.0']


	if lenv.GetOption('weak_localext') :
		for cppPath in gtkmmCppPath :
			lenv.AppendUnique( CCFLAGS = ['${INCPREFIX}' + os.path.join(gtkmmBasePath, cppPath)] )
	else :
		for cppPath in gtkmmCppPath :
			lenv.AppendUnique( CPPPATH = os.path.join(gtkmmBasePath, cppPath) )



	gtkCppPath = [	'lib/gtkglext-1.0/include', 'include/gtkglext-1.0', 'include/libglade-2.0', 'lib/gtk-2.0/include',
					'include/gtk-2.0', 'include/pango-1.0', 'include/atk-1.0', 'lib/glib-2.0/include',
					'include/glib-2.0', 'include/libxml2', 'include/cairo', 'include' ]

	if lenv.GetOption('weak_localext') :
		for cppPath in gtkCppPath :
			lenv.AppendUnique( CCFLAGS = ['${INCPREFIX}' + os.path.join(gtkBasePath, cppPath)] )
	else :
		for cppPath in gtkCppPath :
			lenv.AppendUnique( CPPPATH = os.path.join(gtkBasePath, cppPath) )


	# Sets LIBS, LIBPATH and CPPFLAGS
	if self.myPlatform == 'win32' :
#			lenv.AppendUnique( LIBS = [	'glademm-2.4', 'xml++-2.6', 'gtkmm-2.4', 'glade-2.0', 'gdkmm-2.4', 'atkmm-1.6',
#										'pangomm-1.4', 'glibmm-2.4', 'cairomm-1.0', 'sigc-2.0',
#										'gtk-win32-2.0', 'xml2', 'gdk-win32-2.0', 'atk-1.0', 'gdk_pixbuf-2.0',
#										'pangowin32-1.0', 'pangocairo-1.0', 'pango-1.0', 'cairo', 'gobject-2.0',
#										'gmodule-2.0', 'glib-2.0', 'intl', 'iconv' ] )

		if self.myConfig == 'release' :
			lenv.AppendUnique( LIBS = [	'glademm-2.4', 'xml++-2.6', 'gtkmm-2.4', 'gdkmm-2.4', 'atkmm-1.6',
										'pangomm-1.4', 'glibmm-2.4', 'giomm-2.4', 'cairomm-1.0', 'sigc-2.0' ] )
		else:
			lenv.AppendUnique( LIBS = [	'glademm-2.4d', 'xml++-2.6d', 'gtkmm-2.4d', 'gdkmm-2.4d', 'atkmm-1.6d',
										'pangomm-1.4d', 'glibmm-2.4d', 'giomm-2.4d', 'cairomm-1.0d', 'sigc-2.0d' ] )

		lenv.AppendUnique( LIBS = [	'glade-2.0',
									'gtk-win32-2.0', 'libxml2', 'gdk-win32-2.0', 'atk-1.0', 'gdk_pixbuf-2.0',
									'pangowin32-1.0', 'pangocairo-1.0', 'pango-1.0', 'cairo', 'gobject-2.0',
									'gmodule-2.0', 'glib-2.0', 'gio-2.0', 'gthread-2.0', 'intl', 'iconv' ] )

#		lenv.AppendUnique( LIBS = [ 'gtkglext-win32-1.0', 'gdkglext-win32-1.0' ] )

		lenv.AppendUnique( LIBPATH = [	os.path.join(gtkBasePath, 'lib'),
										os.path.join(gtkmmBasePath, 'lib') ] )

		lenv.AppendUnique( CPPFLAGS = [ '/vd2', '/wd4250' ] )
	else :
		raise SCons.Errors.UserError("Uses=[\'%s\'] not supported on platform %s." % (elt, self.myPlatform) )



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

		### configure cairomm ###
		if elt == 'cairomm1-2-4' :
			use_cairomm( self, lenv, elt )

		### configure ODE ###
		elif elt == 'ode' :
			lenv['LIBS'] += ['ode']

		### configure PhysX ###
		elif elt == 'physx2-8-1' :
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

			useName, useVersion = UseRepository.extract( useNameVersion )
			use = UseRepository.getUse( useName )

			if use != None :
				# Tests if the version is supported
				supportedVersions = use.getVersions()
				if (len(supportedVersions) == 0) or (useVersion in supportedVersions) :
					# Configures environment with the 'use'
					use( useVersion, lenv, skipLinkStageConfiguration )
				else :
					raise SCons.Errors.UserError("Uses=[\'%s\'] version %s not supported." % (useNameVersion, useVersion) )
			else :
				raise SCons.Errors.UserError("Unknown uses=['%s']" % useNameVersion)
