#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2009, 2010, 2011, 2013, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

# ok for cl8-0, 9-0 and 10-0

# See HOWTO Redistributing gtkmm on Microsoft Windows at http://live.gnome.org/gtkmm/MSWindows

# gtk
gtk_exe	= [ 'bin/gspawn-win32-helper.exe', 'bin/gspawn-win32-helper-console.exe' ]
gtk_base_dll = [	'bin/libglade-2.0-0', 'bin/libgtk-win32-2.0-0', 'bin/libgdk-win32-2.0-0', 'bin/libgdk_pixbuf-2.0-0',
					'bin/libpangowin32-1.0-0', 'bin/libpangocairo-1.0-0', 'bin/libpangoft2-1.0-0', 'bin/libpango-1.0-0',
					'bin/libatk-1.0-0', #'bin/libcairo-2', see cairo.py
					'bin/libgobject-2.0-0', 'bin/libgmodule-2.0-0', 'bin/libglib-2.0-0', 'bin/libgio-2.0-0', 'bin/libgthread-2.0-0',
					'bin/intl' ]

gtk_base_lib = [	'lib/glade-2.0', 'lib/gtk-win32-2.0', 'lib/gdk-win32-2.0', 'lib/gdk_pixbuf-2.0',
					'lib/pangowin32-1.0', 'lib/pangocairo-1.0', 'lib/pangoft2-1.0', 'lib/pango-1.0',
					'lib/atk-1.0', #'lib/cairo', see cairo.py
					'lib/gobject-2.0', 'lib/gmodule-2.0', 'lib/glib-2.0', 'lib/gio-2.0', 'lib/gthread-2.0',
					'lib/intl' ]

# xml +  expat
# fontconfig see cairo.py
xml_base_dll = [ 'bin/libxml2-2' ]	# 'bin/libfontconfig-1', 'bin/libexpat-1'
xml_base_lib = [ 'lib/libxml2' ]	# 'lib/fontconfig', 'lib/expat'

# gtkmm
gtkmm_base = [	'bin/glademm-vc80-2_4', 'bin/gdkmm-vc80-2_4', 'bin/pangomm-vc80-1_4',
				'bin/atkmm-vc80-1_6', 'bin/cairomm-vc80-1_0',
				'bin/glibmm-vc80-2_4', 'bin/giomm-vc80-2_4',
				'bin/xml++-vc80-2_6', #'bin/sigc-vc80-2_0', see sigcpp
				'bin/gtkmm-vc80-2_4' ]

# external deps (see cairo.py)
#externals_base = [ 'bin/libpng14-14', 'bin/zlib1', 'bin/freetype6' ]

# Computes replacement string used to adapt package to cl version and configuration
clDict = {	8	: 'vc80-',
			9	: 'vc90-',
			10	: 'vc100-' }

if CCVersionNumber not in clDict:
	print ("Unsupported MSVC version. Version 8, 9 or 10 required.")
	exit(1)

replaceString = clDict[CCVersionNumber]

#
gtk_dll = [ elt + '.dll' for elt in gtk_base_dll ]
gtk_lib = [ elt + '.lib' for elt in gtk_base_lib ]

xml_dll = [ elt + '.dll' for elt in xml_base_dll ]
xml_lib = [ elt + '.lib' for elt in xml_base_lib ]

gtkmm_dll = [ elt.replace('vc80-', replaceString, 1) + '.dll' for elt in gtkmm_base ]
gtkmm_debug_dll = [ elt.replace('vc80-', replaceString + 'd-', 1) + '.dll' for elt in gtkmm_base ]
gtkmm_lib = [ elt.replace('bin/', 'lib/', 1).replace('vc80-', replaceString + 'd-', 1) + '.lib' for elt in gtkmm_base ]
gtkmm_lib.extend( [ elt.replace('bin/', 'lib/', 1).replace('vc80-', replaceString, 1) + '.lib' for elt in gtkmm_base ] )

#externals_dll = [ elt + '.dll' for elt in externals_base ]

# cl8-0exp, cl9-0exp and cl10-0exp
descriptor = {
 'urls'			: ['http://orange/files/Dev/localExt/src/gtkmm-win32-devel-2.22.0-2.zip'],

 'name'			: 'gtkmm',
 'version'		: '2-22-0-2',

 'rootDir'		: 'gtkmm',

 # developer package
 'license'		: ['lgpl.txt'],

 'include'		: [ GlobRegEx('include/.*', pruneDirs='(?:^cairo$)|(?:fontconfig)|(?:freetype2)|(?:libpng14)|(?:sigc.+)', pruneFiles='(?:png[.]h)|(?:pngconf[.]h)|(?:zconf[.]h)|(?:zlib[.]h)')],
 'lib'			: [	GlobRegEx('lib/.*', pruneDirs='sigc\+\+\-2[.]0', pruneFiles='(?!.*[.]h)', recursive=True) ] +
					gtk_lib + xml_lib + gtkmm_lib,

 # runtime package
 'bin'				: gtk_exe + gtk_dll + xml_dll, # + externals_dll, see cairo.py
 'runtimeCustom'	: [	'etc/pango/pango.modules', 'etc/gtk-2.0/gtk.immodules', 'etc/gtk-2.0/gtkrc',
						'lib/gtk-2.0/2.10.0/', 'share/themes/MS-Windows/gtk-2.0/gtkrc', 'share/locale/' ],

 # runtime package (release version)
 'binR'			: gtkmm_dll,

 # runtime package (debug version)
 'binD'			: gtkmm_debug_dll
}
