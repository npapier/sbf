#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2009, 2010, 2011, 2013, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

# ok for cl8-0, 9-0 and 10-0

# See HOWTO Redistributing gtkmm on Microsoft Windows at http://live.gnome.org/gtkmm/MSWindows

# @todo sigcpp from source

# gtkmm
gtkmm_base = [ 'bin/sigc-vc80-2_0' ]

# Computes replacement string used to adapt package to cl version and configuration
clDict = {	8	: 'vc80-',
			9	: 'vc90-',
			10	: 'vc100-' }

if CCVersionNumber not in clDict:
	print ("Unsupported MSVC version. Version 8, 9 or 10 required.")
	exit(1)

replaceString = clDict[CCVersionNumber]

#
gtkmm_dll = [ elt.replace('vc80-', replaceString, 1) + '.dll' for elt in gtkmm_base ]
gtkmm_debug_dll = [ elt.replace('vc80-', replaceString + 'd-', 1) + '.dll' for elt in gtkmm_base ]
gtkmm_lib = [ elt.replace('bin/', 'lib/', 1).replace('vc80-', replaceString + 'd-', 1) + '.lib' for elt in gtkmm_base ]
gtkmm_lib.extend( [ elt.replace('bin/', 'lib/', 1).replace('vc80-', replaceString, 1) + '.lib' for elt in gtkmm_base ] )

# cl8-0exp, cl9-0exp and cl10-0exp
descriptor = {
 'urls'			: ['http://orange/files/Dev/localExt/src/gtkmm-win32-devel-2.22.0-2.zip'],

 'name'			: 'sigcpp',
 'version'		: '2-2-8',

 'rootDir'		: 'gtkmm',

 # developer package
 'license'		: ['lgpl.txt'],

 'include'		: [ 'include/sigc++-2.0' ],
 'lib'			: [	GlobRegEx('lib/.*', pruneDirs='(?!sigc\+\+\-2[.]0)', pruneFiles='(?!.*[.]h)') ] +
					gtkmm_lib,

 # runtime package (release version)
 'binR'			: gtkmm_dll,

 # runtime package (debug version)
 'binD'			: gtkmm_debug_dll 
}
