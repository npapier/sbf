#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2013, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

# Home: openimageio.org

descriptorName = 'openimageio'

versionMajor = 1
versionMinor = 2
descriptorVersion = '{}-{}'.format(versionMajor, versionMinor)
descriptorVersionDot = '{}.{}'.format(versionMajor, versionMinor)

#print ('INFORMATIONS: Qt have to be installed in localExt')
print ('INFORMATIONS: Boost have to be installed in localExt')
print ('INFORMATIONS: ZLib have to be installed in localExt')
print ('INFORMATIONS: libPng have to be installed in localExt')
print ('INFORMATIONS: OpenEXR have to be installed in localExt')

from os.path import join 

from src.sbfCMake import getCMakeCmdConfigure, getCMakeCmdBuildDebug, getCMakeCmdBuildRelease

oiioRootBuildDir = 'oiio-RB-{}'.format(descriptorVersionDot)
absRootBuildDir = os.path.join( buildDirectory, descriptorName + descriptorVersion )
cmakeBuildRoot = join(absRootBuildDir, oiioRootBuildDir, 'cmake_build')

options = ''

#options =	' -D THIRD_PARTY_TOOLS_HOME:PATH="{}" '.format( join(absRootBuildDir, 'dist', 'windows') )

options +=	' -D ILMBASE_INCLUDE_DIR:PATH="{}" '.format( join(localExtDirectory, 'include') )
options +=	' -D OPENEXR_INCLUDE_DIR:PATH="{}" '.format( join(localExtDirectory, 'include') )
options +=	' -D ZLIB_INCLUDE_DIR="{}" '.format( join(localExtDirectory, 'include', 'zlib') )
options +=	' -D ZLIB_LIBRARY="{}" '.format( join(localExtDirectory, 'lib', 'zlibwapi.lib') )
options +=	' -D PNG_PNG_INCLUDE_DIR:PATH="{}" '.format( join(localExtDirectory, 'include') )
options +=	' -D PNG_LIBRARY={} '.format( join(localExtDirectory, 'lib', 'libpng16.lib') )
options +=	' -D JPEG_INCLUDE_DIR:PATH="{}" '.format( join(absRootBuildDir, 'dist', 'windows', 'jpeg-6b', 'include') )
options +=	' -D JPEG_LIBRARY="{}" '.format( join(absRootBuildDir, 'dist', 'windows', 'jpeg-6b', 'lib', 'jpeg.lib') )
options +=	' -D TIFF_INCLUDE_DIR:PATH="{}" '.format( join(absRootBuildDir, 'dist', 'windows', 'tiff-3.8.2', 'include') )
options +=	' -D TIFF_LIBRARY="{}" '.format( join(absRootBuildDir, 'dist', 'windows', 'tiff-3.8.2', 'lib', 'libtiff.lib') )

options += 	' -D BOOST_INCLUDEDIR:PATH="{localExt}/include" '.format( localExt=localExtDirectory )

options +=	' -D EMBEDPLUGINS=OFF '

ConfigureVisualStudioVersion(CCVersionNumber)

options += ' -D OIIO_BUILD_TESTS=OFF -D OIIO_BUILD_TOOLS=OFF '

vcxprojFiles = []

# Working plugins (loadFile() tested using bin/main project)
plugins = ['bmp', 'png', 'targa']

vcxprojToBuild =	['libOpenImageIO/OpenImageIO.vcxproj', 'python/PyOpenImageIO.vcxproj'] + [ '{0}.imageio/{0}.imageio.vcxproj'.format(plugin) for plugin in plugins ]

descriptor = {

	'urls':		[	'https://github.com/OpenImageIO/oiio/archive/RB-{}.zip'.format(descriptorVersionDot),
					'http://www.openimageio.org/external.zip' ],

	'name'		:	descriptorName,
	'version'	:	descriptorVersion,

	'rootBuildDir'	: oiioRootBuildDir,
	'builds'		: [
						# Configuration
						MakeDirectory('cmake_build'),
						ChangeDirectory('cmake_build'),
						getCMakeCmdConfigure(CCVersionNumber, options, '../src'),

						#
						SearchVcxproj(vcxprojFiles, cmakeBuildRoot),

						# /MP
						MSVC['AddMultiProcessorCompilation'](vcxprojFiles),
						# Add ZLIB_WINAPI define
						MSVC['AddPreprocessorDefinitions'](vcxprojFiles, 'ZLIB_WINAPI') ] +

						# Build Release
						[ GetMSBuildCommand(cmakeBuildRoot, vcxproj, 'build', 'Release' ) for vcxproj in vcxprojToBuild ] +

						# Build Debug
						[
						Patcher(vcxprojFiles, [	# ZLib in debug
												('zlibwapi.lib', 'zlibwapi-d.lib'),
												# libpng in debug
												('libpng16.lib', 'libpng16d.lib'),
												# OpenEXR in debug
												('Half.lib', 'Half-d.lib'), ('Iex.lib', 'Iex-d.lib'),
												('Imath.lib', 'Imath-d.lib'), ('IlmThread.lib', 'IlmThread-d.lib'),
												# OpenImageIO
												('OpenImageIO.lib', 'OpenImageIO-d.lib')
												]	),
						MSVC['ChangeTargetName'](join(cmakeBuildRoot, 'libOpenImageIO', 'OpenImageIO.vcxproj'), 'OpenImageIO', 'OpenImageIO-d')
												] +
						[ GetMSBuildCommand(cmakeBuildRoot, vcxproj, 'build', 'Debug' ) for vcxproj in vcxprojToBuild ],

	'rootDir'		: join(oiioRootBuildDir, 'cmake_build'),

	# developer package
	'license'		:	[ '../LICENSE', '../CREDITS' ],
	'include'		:	[	(GlobRegEx('../src/include/.*', pruneFiles='(?!^.*[.](h|hpp)$)', recursive=True), 'oiio/'),
							('include/version.h', 'oiio/') ],
	'lib'			:	[	'libOpenImageIO/Release/OpenImageIO.lib', 'libOpenImageIO/Debug/OpenImageIO-d.lib' ],

	# runtime package (release version)
	'binR'			:	[	# main library
							'libOpenImageIO/Release/*.dll' ] +
							# Plugins
							[(join(plugin+'.imageio', 'Release', '*.dll'), 'oiioPlugins/') for plugin in plugins] +
							# external dependencies
							# zlibwapi, libpng, ilmbase and openexr already available in local/bin
							# python module
							['python/Release/OpenImageIO.pyd'],

	# runtime package (debug version)
	'binD'			:	[	# main library
							'libOpenImageIO/Debug/*.pdb', 'libOpenImageIO/Debug/*.dll' ] +
							# Plugins
							[(join(plugin+'.imageio', 'Debug', '*.pdb'), 'oiioPlugins_D/') for plugin in plugins] +
							[(join(plugin+'.imageio', 'Debug', '*.dll'), 'oiioPlugins_D/') for plugin in plugins] +
							# external dependencies
							# zlibwapi, libpng, ilmbase and openexr already available in local/bin
							# python module
							['python/Debug/openimageio_d.pdb', 'python/Debug/OpenImageIO_d.pyd']
}

