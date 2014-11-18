#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2012, 2014, Nicolas Papier, Alexandre Di Pino.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier
# Author Alexandre Di Pino

# @remark This package is used by sdl 2.0.3 (to allow OpenGL ES 2.0 rendering using angle backend when WGL_EXT_create_context_es2_profile or EGL is not supported)
# AMD support egl, NVidia support WGL_EXT_create_context_es2_profile and Intel needs angle.

# @todo compile angle (to support x86-64 platform and use a DirectX 11 backend)
descriptorName = 'angle'
descriptorVersion = '2-0-0'
projectFolderName = descriptorName + descriptorVersion

from os.path import join

builds = [ GetMSBuildCommand('projects/build', 'all.sln', targets = 'libEGL', config = 'Release', logFile = None, maxcpucount = cpuCount, platform = 'Win32' ) ]

descriptor = {
 'urls'			: [	# OpenGL ES 2.0 Headers
					#	OpenGL ES 2.0 Header File
#					'https://www.khronos.org/registry/gles/api/GLES2/gl2.h',
					#	OpenGL ES Extension Header File
#					'https://www.khronos.org/registry/gles/api/GLES2/gl2ext.h',
					#	OpenGL ES 2.0 Platform-Dependent Macros
#					'https://www.khronos.org/registry/gles/api/GLES2/gl2platform.h'
					# Khronos Shared Platform Header
#					'https://www.khronos.org/registry/egl/api/KHR/khrplatform.h'
					#	EGL Headers
#					'https://www.khronos.org/registry/egl/api/EGL/egl.h',
#					'https://www.khronos.org/registry/egl/api/EGL/eglext.h',
#					'https://www.khronos.org/registry/egl/api/EGL/eglplatform.h',
					# Precompiled angle from Google Chrome
					#'$SRCPAKPATH/precompiledAngleFromGoogleChrome{}.zip'.format(descriptorVersion),
					# Source of angle es2only-legacy branch
					'$SRCPAKPATH/angle-es2only-legacy.tar.gz' ], # see https://chromium.googlesource.com/angle/angle/+/es2only-legacy

 'name'				: descriptorName,
 'version'			: descriptorVersion,

 #'rootBuildDir'	: descriptorName,
 'builds'			: builds,

 # packages developer and runtime
 'rootDir'		: 'projects/build/Release_Win32',

 # developer package
 'license'		: ['../../../README.chromium', '../../../LICENSE'],
 'include'		: ['../../../include/'],
 'lib'			: ['lib/libEGL.lib', 'lib/libGLESv2.lib'],

 # runtime package
 'bin'			: ['libEGL.dll', 'libGLESv2.dll', 'd3dcompiler_46.dll'],
}
