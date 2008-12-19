# SConsBuildFramework - Copyright (C) 2005, 2007, 2008, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

import os
import re
import string
import SCons.Errors

from sbfUtils import getPathFromEnv, convertToList



#===============================================================================
# OptionUses_allowedValues = [	### @todo allow special values like '', 'none', 'all'
#					'boost1-34-1', 'cairo1-2-6', 'cairomm1-2-4', 'colladadom2-0', 'glu', 'glut', 'gtkmm2-14', 'itk3-4-0', 'ode', 'opengl',
#					'openil', 'openilu', 'physx2-8-1', 'sdl', 'sofa', 'wx2-8-8', 'wxgl2-8-8' ]
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

	def getName( self ):
		raise StandardError("IUse::getName() not implemented")

	# Returns the list of version supported for this package.
	# The first element of the returned list is the default version (see use alias for more informations).
	def getVersions( self ):
		return []
		#raise StandardError("IUse::getVersions() not implemented")


	def getCPPDEFINES( self, version ):
		return []

	def getCPPPATH( self, version ):
		return []


	def getLIBS( self, version ):
		return [], []

	def getLIBPATH( self, version ):
		return [], []


	def getLicences( self, version ):															# @todo implements for derived
		return []

	def __call__( self, useVersion, env ):
		useNameVersion = self.getName() + " " + useVersion
#print ("Configures %s" % useNameVersion)

		# CPPDEFINES
		cppdefines = self.getCPPDEFINES( useVersion )
		if cppdefines != None :
			if len(cppdefines) > 0 :
				env.AppendUnique( CPPDEFINES = cppdefines )
		else :
			raise SCons.Errors.UserError("Uses=[\'%s\'] not supported on platform %s (see CPPDEFINES)." % (useNameVersion, self.platform) )

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
						env.AppendUnique( CCFLAGS = ['-I' + path ] )
				else :
					env.AppendUnique( CPPPATH = cpppathAbs )
		else :
			raise SCons.Errors.UserError("Uses=[\'%s\'] not supported on platform %s (see CPPPATH)." % (useNameVersion, self.platform) )

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
		return ['1-34-1']

	def getCPPDEFINES( self, version ):
		if self.platform == 'win32':
			return [ 'BOOST_ALL_DYN_LINK' ]
		else:
			return []

	# @todo boost only for vc80, checks compiler and compiler version ?
	def getLIBS( self, version ):
		if self.platform == 'win32' and version == '1-34-1':
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


#===============================================================================
# def use_boost( self, lenv, elt ) :
#	if ( self.myPlatform == 'posix' ) :
#		lenv['LIBS'] += [ 'boost_date_time-gcc-mt-1_33_1', 'boost_filesystem-gcc-mt-1_33_1', 'boost_regex-gcc-mt-1_33_1', 'boost_signals-gcc-mt-1_33_1']
#		lenv['LIBS'] += [ 'boost_thread-gcc-mt-1_33_1'  , 'boost_serialization-gcc-mt-1_33_1', 'boost_iostreams-gcc-mt-1_33_1']
#		lenv['LIBS'] += [ 'boost_program_options-gcc-mt-1_33_1', 'boost_wserialization-gcc-mt-1_33_1', 'boost_python-gcc-mt-1_33_1' ]
#	elif ( self.myPlatform == 'darwin' ) :
#		lenv['LIBS'] += [ 'boost_date_time-1_33_1', 'boost_filesystem-1_33_1', 'boost_regex-1_33_1', 'boost_signals-1_33_1']
#		lenv['LIBS'] += [ 'boost_thread-1_33_1'  , 'boost_serialization-1_33_1', 'boost_iostreams-1_33_1']
#		lenv['LIBS'] += [ 'boost_program_options-1_33_1', 'boost_wserialization-1_33_1', 'boost_python-1_33_1' ]
#	#else:
#	# Nothing to do for win32 platform.
#===============================================================================


class Use_cairo( IUse ):

	def __init__( self ):
		if self.platform == 'win32' :
			# Retrieves GTK_BASEPATH
			self.__gtkBasePath = getPathFromEnv('GTK_BASEPATH')

	def getName( self ):
		return 'cairo'

	def getVersions( self ):
		return ['1-7-6', '1-2-6']


	def getCPPDEFINES( self, version ):
		if self.platform == 'win32' :
			return [ '/vd2', '/wd4250' ]
		else:
			return []

	def getCPPPATH( self, version ):
		if self.platform == 'win32' :
			if self.__gtkBasePath is None :
				return None
			# Sets CPPPATH
			gtkCppPath = [ 'include/cairo', 'include' ]
			cppPath = []
			for path in gtkCppPath :
				cppPath.append( os.path.join(self.__gtkBasePath, path) )
			return cppPath
		elif self.platform == 'posix' :
			# Sets CPPPATH
			cppPath = [	'/usr/include/cairo', '/usr/include/pixman-1', '/usr/include/freetype2',
						'/usr/include/libpng12'	]
			return cppPath

	def getLIBS( self, version ):
		if (self.platform == 'win32') and (version in ['1-7-6', '1-2-6']) :
			libs = [ 'cairo' ]
			pakLibs = [ 'libcairo-2' ]
			return libs, pakLibs
		elif self.platform == 'posix' :
			libs = [ 'cairo' ]
			return libs, libs

	def getLIBPATH( self, version ):
		if self.platform == 'win32' :
			if self.__gtkBasePath is None :
				return None
			else:
				return [ os.path.join(self.__gtkBasePath, 'lib') ], [ os.path.join(self.__gtkBasePath, 'bin') ]
		elif self.platform == 'posix' :
			return [], []

#def use_cairo( self, lenv, elt ) :
#=======================================================================================================================
# for cairo package
#		lenv.AppendUnique( CPPPATH = os.path.join( self.myIncludesInstallExtPaths[0], 'cairo' ) )
#		lenv.AppendUnique( LIBS = ['cairo', 'fontconfig', 'freetype', 'png', 'z' ] )
#=======================================================================================================================


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


# TODO: SOFA_PATH documentation
# TODO: packages sofa into a localExt and adapts the following code to be more sbf friendly
class Use_sofa( IUse ):
	__sofa_path = None

	def __init__( self ):
		# Retrieves SOFA_PATH
		self.__sofa_path = getPathFromEnv('SOFA_PATH')
#if self.__sofa_path is None :
#	raise SCons.Errors.UserError("Unable to configure sofa")

	def getName( self ):
		return "sofa"

	def getCPPDEFINES( self, version ):
		return ['SOFA_DOUBLE', 'SOFA_DEV']

	# @todo Takes care of "lenv.GetOption('weak_localext') " ?
	def getCPPPATH( self, version ):
		cppPath = [	os.path.join(self.__sofa_path, 'modules'),
					os.path.join(self.__sofa_path, 'framework'),
					os.path.join(self.__sofa_path, 'include'),
					os.path.join(self.__sofa_path, 'extlibs/miniFlowVR/include') ]
		return cppPath

	def getLIBS( self, version ):
		if self.platform != 'win32' :
			return None

		libs = ['glew32', 'libxml2', 'Gdi32', 'Shell32']
		pakLibs = []
		if self.config == 'release' :
			libs += [	'SofaCore', 'SofaDefaultType', 'SofaComponent', 'SofaHelper', 'SofaSimulation',
						'SofaTree', 'SofaAutomateScheduler', 'miniFlowvR', 'NewMAT' ]
			pakLibs += ['SofaCore', 'SofaDefaultType', 'SofaHelper']
		else:
			libs += [	'SofaCored', 'SofaDefaultTyped', 'SofaComponentd', 'SofaHelperd', 'SofaSimulationd',
						'SofaTreed', 'SofaAutomateSchedulerd', 'miniFlowvRd', 'NewMATd' ]
			pakLibs += ['SofaCored', 'SofaDefaultTyped', 'SofaHelperd']
		return libs, pakLibs

	def getLIBPATH( self, version ):
		libPath		= []
		pakLibPath	= []

		if self.config == 'release' :
			path = os.path.join( self.__sofa_path, 'lib/win32/ReleaseVC8')
			libPath.append( path )
			pakLibPath.append( path )
		else :
			path = os.path.join( self.__sofa_path, 'lib/win32/DebugVC8')
			libPath.append( path )
			pakLibPath.append( path )

		libPath.append( os.path.join( self.__sofa_path, 'lib/win32/Common' ) )

		return libPath, pakLibPath


#@todo Adds support to both ANSI and Unicode version of wx
#@todo Adds support static/dynamic and db stuff (see http://www.wxwidgets.org/wiki/index.php/MSVC_.NET_Setup_Guide)
class Use_wxWidgets( IUse ):
	def getName( self ):
		return "wx"

	def getVersions( self ):
		return ['2-8-8']

	def getCPPDEFINES( self, version ):
		if self.platform == 'win32':
			return [ 'WXUSINGDLL', '__WIN95__' ]
		else :
			return None

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
#-I/usr/lib/wx/include/gtk2-unicode-release-2.8 -I/usr/include/wx-2.8 -D_FILE_OFFSET_BITS=64 -D_LARGE_FILES -D__WXGTK__
#-pthread -Wl,-Bsymbolic-functions  
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
	__platform		= None
	__config		= None

	__repository	= {}

	__allowedValues = [	'cairomm1-2-4', 'gtkmm2-14', 'itk3-4-0', 'ode',
						'physx2-8-1' ]
	__alias			= {
			'cairomm'		: 'cairomm1-2-4',
			'gtkmm'			: 'gtkmm2-14',
			'itk'			: 'itk3-4-0',
			'physx'			: 'physx2-8-1'	}

	__initialized	= False

	@classmethod
	def initialize( self, sbf,
					listOfIUseImplementation = [Use_boost(), Use_cairo(), Use_colladadom(), Use_glu(), Use_glut(), Use_opengl(),
												Use_openil(), Use_openilu(), Use_sdl(), Use_sofa(), Use_wxWidgets(), Use_wxWidgetsGL()] ):

		if self.__initialized == True :
			raise SCons.Errors.InternalError("Try to initialize UseRepository twice.")

		# Initializes platform and config
		self.__platform	= sbf.myPlatform
		self.__config	= sbf.myConfig

		IUse.platform	= sbf.myPlatform
		IUse.config		= sbf.myConfig

		# Initializes repository
		print ("Adds in UseRepository :"),
		for use in listOfIUseImplementation :
			# Adds to repository
			name = use.getName()

			self.__repository[ name ] = use
			print name,											# ??? verbose

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
		print

		#
		self.__initialized = True

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
			lenv.AppendUnique( CCFLAGS = ['-I' + os.path.join(gtkmmBasePath, cppPath)] )
	else :
		for cppPath in gtkmmCppPath :
			lenv.AppendUnique( CPPPATH = os.path.join(gtkmmBasePath, cppPath) )

	# Sets LIBS and LIBPATH
	if self.myPlatform == 'win32' :
		if self.myConfig == 'release' :
			lenv.AppendUnique( LIBS = [	'cairomm-1.0' ] )
		else:
			lenv.AppendUnique( LIBS = [	'cairomm-1.0d' ] )

		lenv.AppendUnique( LIBPATH = [ os.path.join(gtkmmBasePath, 'lib') ] )
	else :
		raise SCons.Errors.UserError("Uses=[\'%s\'] not supported on platform %s." % (elt, self.myPlatform) )


# TODO: GTK_BASEPATH and GTKMM_BASEPATH documentation, package gtkmm ?
def use_gtkmm( self, lenv, elt ) :
	if self.myPlatform == 'posix' :
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
			lenv.AppendUnique( CCFLAGS = ['-I' + os.path.join(gtkmmBasePath, cppPath)] )
	else :
		for cppPath in gtkmmCppPath :
			lenv.AppendUnique( CPPPATH = os.path.join(gtkmmBasePath, cppPath) )



	gtkCppPath = [	'lib/gtkglext-1.0/include', 'include/gtkglext-1.0', 'include/libglade-2.0', 'lib/gtk-2.0/include',
					'include/gtk-2.0', 'include/pango-1.0', 'include/atk-1.0', 'lib/glib-2.0/include',
					'include/glib-2.0', 'include/libxml2', 'include/cairo', 'include' ]

	if lenv.GetOption('weak_localext') :
		for cppPath in gtkCppPath :
			lenv.AppendUnique( CCFLAGS = ['-I' + os.path.join(gtkBasePath, cppPath)] )
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

def use_itk( self, lenv, elt ) :
	# Already and always done by sbf on windows platform '/DNOMINMAX'

	# includes
	itkIncludes = [	'itk', 'itk/Algorithms', 'itk/BasicFilters', 'itk/Common', 'itk/expat', 'itk/gdcm/src',
					'itk/IO', 'itk/Numerics', 'itk/Numerics/FEM', 'itk/Numerics/NeuralNetworks', 'itk/Numerics/Statistics',
					'itk/SpatialObject', 'itk/Utilities', 'itk/Utilities/MetaIO', 'itk/Utilities/NrrdIO',
					'itk/Utilities/vxl/core', 'itk/Utilities/vxl/vcl' ]

	if lenv.GetOption('weak_localext') :
		for cppPath in self.myIncludesInstallExtPaths :
			for include in itkIncludes :
				lenv.Append( CCFLAGS = ['-I' + os.path.join(cppPath, include) ] )
	else :
		for cppPath in self.myIncludesInstallExtPaths :
			for include in itkIncludes :
				lenv.Append( CPPPATH = os.path.join(cppPath, include) )

	# libs
	itkLibs = [	'ITKAlgorithms', 'ITKBasicFilters', 'ITKCommon', 'ITKDICOMParser', 'ITKEXPAT', 'ITKFEM', 'itkgdcm',
				'ITKIO', 'itkjpeg8', 'itkjpeg12', 'itkjpeg16', 'ITKMetaIO', 'ITKniftiio', 'ITKNrrdIO', 'ITKNumerics',
				'itkopenjpeg', 'itkpng', 'ITKSpatialObject', 'ITKStatistics', 'itksys', 'itktiff', 'itkv3p_netlib',
				'itkvcl', 'itkvnl', 'itkvnl_algo', 'itkvnl_inst', 'itkzlib', 'ITKznz' ]

	lenv.Append( LIBS = itkLibs )

#===============================================================================
# def use_openIL( self, lenv, elt ) :
#	if ( self.myPlatform == 'win32' ) :
#		if ( self.myConfig == 'release' ) :
#			lenv['LIBS']	+= ['DevIL']
#		else :
#			lenv['LIBS']	+= ['DevIL'] #['DevILd'] @todo openil should be compiled in debug on win32 platform
#	else :
#		if ( self.myConfig == 'release' ) :
#			lenv['LIBS']	+= ['IL']
#		else :
#			lenv['LIBS']	+= ['ILd']
#===============================================================================

#===============================================================================
# def use_openILU( self, lenv, elt ) :
#	if ( self.myPlatform == 'win32' ) :
#		if ( self.myConfig == 'release' ) :
#			lenv['LIBS']	+= ['ILU']
#		else :
#			lenv['LIBS']	+= ['ILU'] #['DevILd'] @todo openil should be compiled in debug on win32 platform
#	else :
#		if ( self.myConfig == 'release' ) :
#			lenv['LIBS']	+= ['ILU']
#		else :
#			lenv['LIBS']	+= ['ILUd']
#===============================================================================

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
			lenv.AppendUnique( CCFLAGS = ['-I' + os.path.join(physxBasePath, cppPath)] )
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



def uses( self, lenv ):
	#
#print '%s uses: %s' % (lenv['sbf_project'], lenv['uses'])
	for elt in lenv['uses'] :
		# Converts to lower case
		elt = string.lower( elt )

		# @todo FIXME hack for wx @todo move to IUse getLINKFLAGS()
		if self.myPlatform == 'win32' and elt == 'wx2-8-8' and self.myType == 'exec' :
			lenv.Append( LINKFLAGS = '/SUBSYSTEM:WINDOWS' )

		### configure boost ###
		#if elt == 'boost1-33-1' :
		#	use_boost( self, lenv, elt )

#===============================================================================
#		### configure cairo ###
#		if elt == 'cairo1-2-6' :
#			use_cairo( self, lenv, elt )
#===============================================================================

		### configure cairomm ###
		if elt == 'cairomm1-2-4' :
			use_cairomm( self, lenv, elt )

#===============================================================================
#		### configure colladadom ###
#		elif elt == 'colladadom2-0' :
#			use_colladadom( self, lenv, elt )
#===============================================================================

		### configure gtk/gtkmm ###
		elif elt == 'gtkmm2-14' :
			use_gtkmm( self, lenv, elt );

		### configure itk ###
		elif elt == 'itk3-4-0' :
			use_itk( self, lenv, elt )

		### configure ODE ###
		elif elt == 'ode' :
			lenv['LIBS'] += ['ode']

#===============================================================================
#		### configure openIL ###
#		elif elt == 'openil' :
#			use_openIL( self, lenv, elt )
#===============================================================================

#===============================================================================
#		### configure openILU ###
#		elif elt == 'openilu' :
#			use_openILU( self, lenv, elt )
#===============================================================================

		### configure PhysX ###
		elif elt == 'physx2-8-1' :
			use_physx( self, lenv, elt )

#===============================================================================
#		### configure sdl ###
#		elif elt == 'sdl' :
#			use_sdl( self, lenv, elt )
#===============================================================================

#===============================================================================
#		### configure sofa ###
#		elif elt == 'sofa' :
#			use_sofa( self, lenv, elt )
#===============================================================================

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
					use( useVersion, lenv )
				else :
					raise SCons.Errors.UserError("Uses=[\'%s\'] version %s not supported." % (useNameVersion, useVersion) )
			else :
				raise SCons.Errors.UserError("Unknown uses=['%s']" % useNameVersion)
