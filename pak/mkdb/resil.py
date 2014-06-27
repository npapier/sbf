#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2009, 2010, 2011, 2013, 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

# ok for cl*[Exp] (32/64 bits)

# http://sourceforge.net/projects/resil (resil is a fork of devil library available at http://openil.sourceforge.net/)

from os.path import join

descriptorName = 'resil'
descriptorVersion = '1-8-2'
descriptorDotVersion = descriptorVersion.replace('-', '.')
projectSourceFolderName = 'ResIL-{}'.format(descriptorDotVersion)

if platform != 'win':
	print ("Platform '{}' not yet supported".format(platform))
	exit(1)

ConfigureVisualStudioVersion(CCVersionNumber)

if arch == 'x86-32':
	platform = 'Win32'
	libPath = 'Release-msvcrt'
else:
	platform = 'x64'
	libPath = 'x64/Release-msvcrt'

slnPath = join('projects/msvc11') # from ResIL-1.8.2_patch_sln.zip
slnFile = 'ResIL.sln'
vcxprojFiles = []

libsNameSO = ['ResIL', 'ILU', 'zlib1']
libsNameLIB = ['ResIL', 'ILU', ]

# @todo submit this patch
il_internalPath = """// BEGIN PATCH to support non unicode resil on Windows platform
#ifndef _UNICODE
	#define WIN32_LEAN_AND_MEAN  // Exclude rarely-used stuff from Windows headers
	#include <windows.h>
	#ifdef _WIN32
		#define wcslen	strlen
		#define wcscpy	strcpy
	#endif
#endif
// END PATCH
"""

descriptor = {
	'urls'			: [	'http://downloads.sourceforge.net/resil/{0}/ResIL-{0}.zip'.format(descriptorDotVersion),
						'http://orange/files/Dev/localExt/PUBLIC/src/ResIL-1.8.2_patch_sln.zip'
						],

	'rootBuildDir'	: projectSourceFolderName,
	'builds'		: [	#
						SearchVcxproj(vcxprojFiles, slnPath),

						# Fixes vcproj files
						#	Configures which version of cl have to be invoke.
						MSVC['SetPlatformToolset']( vcxprojFiles, CCVersionNumber ),

						#	Fixes version passed to linker (have to be x.y)
						MSVC['ChangeLinkVersion'](join(slnPath, 'zlib.vcxproj'), '1.2.8', '1.2'),
						MSVC['ChangeLinkVersion'](join(slnPath, 'IL.vcxproj'), '1.8.2', '1.8'),
						MSVC['ChangeLinkVersion'](join(slnPath, 'ILU.vcxproj'), '1.7.9', '1.8'),
						MSVC['ChangeLinkVersion'](join(slnPath, 'ILU.vcxproj'), '1.8.0', '1.8'),

						#	Removes /NODEFAULTLIB (i.e. <IgnoreAllDefaultLibraries>true</IgnoreAllDefaultLibraries>)
						ChangeContentOfAnXMLElement(vcxprojFiles, 'IgnoreAllDefaultLibraries', 'true', 'false'),

						#	Compile without UNICODE support enabled
						#    <CharacterSet>Unicode</CharacterSet> => <CharacterSet>NotSet</CharacterSet>
						#@todo use ChangeContentOfAnXMLElement()
						Patcher(vcxprojFiles, [('^(.*\<CharacterSet\>).*(\</CharacterSet\>)$', '\\1{}\\2'.format('NotSet'))] ),

						# Patch source files

						# il_internal.h
						#	patch line 78 // Windows-specific
						Patcher( join('src-IL/include/il_internal.h'), [('^(.*// Windows-specific.*$)', '\\1\\n{}'.format(il_internalPath))] ),

						# il_io.cpp
# @todo submit patch replace L"pal" by IL_TEXT("pal")
						#	patch line 655
						#	wcscpy(&palFN[fnLen-3], L"pal");
						#	=>
						#	wcscpy(&palFN[fnLen-3], IL_TEXT("pal") );
						Patcher( join('src-IL/src/il_io.cpp'), [('^(.*)L\"pal\"(.*)$', '\\1IL_TEXT(\"pal\")\\2')] ),

						# Build
						GetMSBuildCommand(slnPath, slnFile, 'ILU', 'Release-msvcrt', maxcpucount = cpuCount, platform = platform )
						],

	'name'			: descriptorName,
	'version'		: descriptorVersion,

	# packages developer and runtime
	'rootDir'		: projectSourceFolderName,

	# developer package
	'license'		: ['COPYING', 'AUTHORS', 'CREDITS'],
	'include'		: [('include/IL/','IL/')],
	'lib'			: [ join(slnPath, libPath, '{}.lib'.format(lib)) for lib in libsNameLIB ],

	# runtime package
	'bin'			: [ join(slnPath, libPath, '{}.dll'.format(lib)) for lib in libsNameSO ],
}
