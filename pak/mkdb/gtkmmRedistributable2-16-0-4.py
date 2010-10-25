#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2009, 2010, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

# ok for cl8-0 and 9-0

# See HOWTO Redistributing gtkmm on Microsoft Windows at http://live.gnome.org/gtkmm/MSWindows

# gtk
gtk_exe	= [ 'bin/gspawn-win32-helper.exe', 'bin/gspawn-win32-helper-console.exe' ]
gtk_base = [	'bin/libglade-2.0-0', 'bin/libgtk-win32-2.0-0', 'bin/libgdk-win32-2.0-0', 'bin/libgdk_pixbuf-2.0-0',
				'bin/libpangowin32-1.0-0', 'bin/libpangocairo-1.0-0', 'bin/libpangoft2-1.0-0', 'bin/libpango-1.0-0',
				'bin/libatk-1.0-0', 'bin/libcairo-2',
				'bin/libgobject-2.0-0', 'bin/libgmodule-2.0-0', 'bin/libglib-2.0-0', 'bin/libgio-2.0-0', 'bin/libgthread-2.0-0',
				'bin/intl' ]

# xml
xml_base = [ 'bin/libxml2', 'bin/iconv' ]

# gtkmm
gtkmm_base = [	'bin/glademm-vc80-2_4', 'bin/gdkmm-vc80-2_4', 'bin/pangomm-vc80-1_4',
				'bin/atkmm-vc80-1_6', 'bin/cairomm-vc80-1_0',
				'bin/glibmm-vc80-2_4', 'bin/giomm-vc80-2_4',
				'bin/xml++-vc80-2_6', 'bin/sigc-vc80-2_0',
				'bin/gtkmm-vc80-2_4' ]

# external deps
externals_base = [ 'bin/libpng12-0', 'bin/libtiff3', 'bin/jpeg62', 'bin/zlib1' ]

# Computes replacement string used to adapt package to cl version and configuration
clDict = {	8	: 'vc80-',
			9	: 'vc90-' }
			# 10	: 'vc100-' }

replaceString = clDict[CCVersionNumber]

if config == 'debug':
	replaceString += 'd-'

#
gtk_dll = [ elt + '.dll' for elt in gtk_base ]
xml_dll = [ elt + '.dll' for elt in xml_base ]
gtkmm_dll = [ elt.replace('vc80-', replaceString, 1) + '.dll' for elt in gtkmm_base ]
externals_dll = [ elt + '.dll' for elt in externals_base ]

# cl8-0exp and cl9-0exp
descriptor = {
 'urls'			: ['http://orange/files/Dev/localExt/src/gtkmm-win32-devel-2.16.0-4.zip'],

 'name'			: 'gtkmmRedist',
 'version'		: '2-16-0-4',

 'rootDir'		: 'gtkmm-win32-devel-2.16.0-4/gtkmm/',
 'license'		: ['lgpl.txt'],

 'bin'			: gtk_exe + gtk_dll + xml_dll + gtkmm_dll + externals_dll,

 'custom'		: [	'etc/pango/pango.modules', 'etc/gtk-2.0/gdk-pixbuf.loaders', 'etc/gtk-2.0/gtk.immodules', 'etc/gtk-2.0/gtkrc',
 					'lib/gtk-2.0/2.10.0/', 'share/themes/MS-Windows/gtk-2.0/gtkrc', 'share/locale/' ]
}
