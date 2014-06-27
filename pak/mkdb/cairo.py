#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2009, 2010, 2011, 2013, 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

# ok for cl* (32/64 bits)

# Actually cairo is extracted from http://www.gtk.org/download/
# @todo cairo from source

# Previously: See HOWTO Redistributing gtkmm on Microsoft Windows at http://live.gnome.org/gtkmm/MSWindows

# cairo
cairo_base_dll = [ 'bin/libcairo-2' ]
cairo_base_lib = [ 'lib/cairo' ]

# fontconfig
xml_base_dll = [ 'bin/libfontconfig-1', 'bin/libexpat-1' ]
xml_base_lib = [ 'lib/fontconfig', 'lib/expat' ]

# external deps
if arch == 'x86-32':
	externals_base = [ 'bin/freetype6', 'bin/libpng14-14', 'bin/zlib1' ]
else:
	externals_base = [ 'bin/libfreetype-6', 'bin/libpng14-14', 'bin/zlib1' ]

#
cairo_dll = [ elt + '.dll' for elt in cairo_base_dll ]
cairo_lib = [ elt + '.lib' for elt in cairo_base_lib ]
#
xml_dll = [ elt + '.dll' for elt in xml_base_dll ]
xml_lib = [ elt + '.lib' for elt in xml_base_lib ]
#
externals_dll = [ elt + '.dll' for elt in externals_base ]

if platform == 'win':
	if arch == 'x86-32':
		platformArch = 'win32'
	else:
		platformArch = 'win64'
else:
	print ('Unsupported platform {}'.format(platform))
	exit(1)


descriptor = {
 'urls'			: [
	# cairo (http://cairographics.org/releases/cairo-1.10.2.tar.gz)
	#	from gtk 3.x and 2.x (same package)
	'http://ftp.gnome.org/pub/gnome/binaries/{platformArch}/dependencies/cairo_1.10.2-1_{platformArch}.zip'.format(platformArch=platformArch),
	'http://ftp.gnome.org/pub/gnome/binaries/{platformArch}/dependencies/cairo-dev_1.10.2-1_{platformArch}.zip'.format(platformArch=platformArch),

	# fontconfig (http://www.fontconfig.org/release/fontconfig-2.10.2.tar.gz)
	#	from gtk2.x
	'http://ftp.gnome.org/pub/gnome/binaries/{platformArch}/dependencies/fontconfig_2.8.0-2_{platformArch}.zip'.format(platformArch=platformArch),
	'http://ftp.gnome.org/pub/gnome/binaries/{platformArch}/dependencies/fontconfig-dev_2.8.0-2_{platformArch}.zip'.format(platformArch=platformArch),
	#	from gtk3.x
	#'http://win32builder.gnome.org/packages/3.6/fontconfig_2.10.2-1_{platformArch}.zip'.format(platformArch=platformArch),
	#'http://win32builder.gnome.org/packages/3.6/fontconfig-dev_2.10.2-1_{platformArch}.zip'.format(platformArch=platformArch),

	# expat (needed by fontconfig). See http://expat.sourceforge.net/
	#	from gtk2.x (no more used by gtk3.x)
	'http://ftp.gnome.org/pub/gnome/binaries/{platformArch}/dependencies/expat_2.0.1-1_{platformArch}.zip'.format(platformArch=platformArch),
	'http://ftp.gnome.org/pub/gnome/binaries/{platformArch}/dependencies/expat-dev_2.0.1-1_{platformArch}.zip'.format(platformArch=platformArch),

	# freetype (http://downloads.sourceforge.net/project/freetype/freetype2/2.4.11/freetype-2.4.11.tar.bz2)
	#	from gtk2.x
	'http://ftp.gnome.org/pub/gnome/binaries/{platformArch}/dependencies/freetype_2.4.2-1_{platformArch}.zip'.format(platformArch=platformArch),
	'http://ftp.gnome.org/pub/gnome/binaries/{platformArch}/dependencies/freetype-dev_2.4.2-1_{platformArch}.zip'.format(platformArch=platformArch),
	#	from gtk3.x
	#'http://win32builder.gnome.org/packages/3.6/freetype_2.4.11-1_{platformArch}.zip'.format(platformArch=platformArch),
	#'http://win32builder.gnome.org/packages/3.6/freetype-dev_2.4.11-1_{platformArch}.zip'.format(platformArch=platformArch),

	# png (http://sourceforge.net/projects/libpng/files/libpng15/older-releases/1.5.14/libpng-1.5.14.tar.xz/download)
	#	from gtk2.x
	'http://ftp.gnome.org/pub/gnome/binaries/{platformArch}/dependencies/libpng_1.4.3-1_{platformArch}.zip'.format(platformArch=platformArch),
	'http://ftp.gnome.org/pub/gnome/binaries/{platformArch}/dependencies/libpng-dev_1.4.3-1_{platformArch}.zip'.format(platformArch=platformArch),
	#	from gtk3.x
	#'http://win32builder.gnome.org/packages/3.6/libpng_1.5.14-1_{platformArch}.zip'.format(platformArch=platformArch),
	#'http://win32builder.gnome.org/packages/3.6/libpng-dev_1.5.14-1_{platformArch}.zip'.format(platformArch=platformArch),

	# zlib (http://www.zlib.net/zlib127.zip)
	#	from gtk3.x
	'http://win32builder.gnome.org/packages/3.6/zlib_1.2.7-1_{platformArch}.zip'.format(platformArch=platformArch),
	'http://win32builder.gnome.org/packages/3.6/zlib-dev_1.2.7-1_{platformArch}.zip'.format(platformArch=platformArch) ],
 'name'			: 'cairo',
 'version'		: '1-10-0',

 # developer package
 'license'		: [	'share/doc/cairo_1.10.2-1_{platformArch}/COPYING'.format(platformArch=platformArch),
					'share/doc/cairo_1.10.2-1_{platformArch}/COPYING-LGPL-2.1'.format(platformArch=platformArch),
					'share/doc/cairo_1.10.2-1_{platformArch}/COPYING-MPL-1.1'.format(platformArch=platformArch) ],

 'include'		: [	GlobRegEx('include/^cairo$'),
					GlobRegEx('include/fontconfig'),
					GlobRegEx('include/freetype2'),
					GlobRegEx('include/libpng14'),
					'include/z*.h' ],
 'lib'			: cairo_lib + xml_lib,

 # runtime package
 'bin'				: cairo_dll + xml_dll + externals_dll,
}
