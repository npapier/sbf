#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2009, 2010, 2011, 2013, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

# ok for cl8-0, 9-0 and 10-0

# @todo cairo from source

# See HOWTO Redistributing gtkmm on Microsoft Windows at http://live.gnome.org/gtkmm/MSWindows

# gtk
gtk_base_dll = [ 'bin/libcairo-2' ]
gtk_base_lib = [ 'lib/cairo' ]

# fontconfig
xml_base_dll = [ 'bin/libfontconfig-1', 'bin/libexpat-1' ]
xml_base_lib = [ 'lib/fontconfig', 'lib/expat' ]

# external deps
externals_base = [ 'bin/libpng14-14', 'bin/zlib1', 'bin/freetype6' ]

#
gtk_dll = [ elt + '.dll' for elt in gtk_base_dll ]
gtk_lib = [ elt + '.lib' for elt in gtk_base_lib ]

xml_dll = [ elt + '.dll' for elt in xml_base_dll ]
xml_lib = [ elt + '.lib' for elt in xml_base_lib ]

externals_dll = [ elt + '.dll' for elt in externals_base ]

# cl8-0exp, cl9-0exp and cl10-0exp
descriptor = {
 'urls'			: ['http://orange/files/Dev/localExt/src/gtkmm-win32-devel-2.22.0-2.zip'],

 'name'			: 'cairo',
 'version'		: '1-10-0',

 'rootDir'		: 'gtkmm',

 # developer package
 'license'		: ['lgpl.txt'],

 'include'		: [	GlobRegEx('include/^cairo$'),
					GlobRegEx('include/fontconfig'),
					GlobRegEx('include/freetype2'),
					GlobRegEx('include/libpng14'),
					'include/z*.h' ],
 'lib'			: gtk_lib + xml_lib,

 # runtime package
 'bin'				: gtk_dll + xml_dll + externals_dll,
}
