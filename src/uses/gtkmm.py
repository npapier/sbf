# SConsBuildFramework - Copyright (C) 2014, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

class Use_gtkmm( IUse ):

	def getName( self ):
		return 'gtkmm'

	def getVersions( self ):
		return [ '2-22-0-2' ]

	def getRequirements( self, version ):
		if version == '2-22-0-2':
			return ['cairo 1-10-0', 'sigcpp2-2-8']
		else:
			return []

	def getCPPDEFINES( self, version ):
		# @todo uses version api (see SConsBuildFramework.py)
		versionNumber = int( version.replace('-', '') )
		return [ (self.getName().upper()+'_VERSION', versionNumber) ]

	def getCPPPATH( self, version ):
		if self.platform == 'win' :
			gtkmmCppPath = [	'../lib/glibmm-2.4/include', 'glibmm-2.4',
								'../lib/giomm-2.4/include', 'giomm-2.4',
								'../lib/gdkmm-2.4/include', 'gdkmm-2.4',
								'../lib/gtkmm-2.4/include', 'gtkmm-2.4',
								'../lib/libglademm-2.4/include', 'libglademm-2.4',
								'../lib/libxml++-2.6/include', 'libxml++-2.6',
								# 'lib/sigc++-2.0/include', 'include/sigc++-2.0', see sigcpp
								'../lib/pangomm-1.4/include', 'pangomm-1.4',
								'atkmm-1.6',
								'cairomm-1.0' ]

			gtkCppPath = [		'libglade-2.0',
								'../lib/gtk-2.0/include', 'gtk-2.0',
								'pango-1.0',
								'atk-1.0',
								'../lib/glib-2.0/include', 'glib-2.0',
								'gdk-pixbuf-2.0',
								'libxml2',
								#'freetype2',	see cairo
								#'cairo',		see cairo
								]
			return gtkmmCppPath + gtkCppPath
		elif self.platform == 'posix':
			gtkglextCppPath	= [	'/usr/include/gtkglext-1.0', '/usr/lib64/gtkglext-1.0/include' ]
			gtkmmCppPath	= [	'/usr/include/gtkmm-2.4', '/usr/lib64/gtkmm-2.4/include', '/usr/include/glibmm-2.4', '/usr/lib64/glibmm-2.4/include',
								'/usr/include/giomm-2.4', '/usr/lib64/giomm-2.4/include', '/usr/include/gdkmm-2.4', '/usr/lib64/gdkmm-2.4/include',
								'/usr/include/pangomm-1.4', '/usr/include/atkmm-1.6', '/usr/include/gtk-2.0', '/usr/include/sigc++-2.0',
								'/usr/lib64/sigc++-2.0/include', '/usr/include/glib-2.0', '/usr/lib64/glib-2.0/include', '/usr/lib64/gtk-2.0/include',
								'/usr/include/cairomm-1.0', '/usr/include/pango-1.0', '/usr/include/cairo', '/usr/include/pixman-1', '/usr/include/freetype2',
								'/usr/include/libpng12', '/usr/include/atk-1.0' ]

			return gtkglextCppPath + gtkmmCppPath



	def getLIBS( self, version ):
		if self.platform == 'win':
			libs = [	'glade-2.0', 'gtk-win32-2.0', 'gdk-win32-2.0', 'gdk_pixbuf-2.0',
						'pangowin32-1.0', 'pangocairo-1.0', 'pangoft2-1.0', 'pango-1.0',
						'atk-1.0', # 'cairo', see cairo
						'gobject-2.0', 'gmodule-2.0', 'glib-2.0', 'gio-2.0', 'gthread-2.0',
						'intl',
						'libxml2' ] # 'fontconfig' see cairo

			if self.config == 'release' :
				# RELEASE
				if self.cc == 'cl' and self.ccVersionNumber >= 10.0000 :
					libs += [	'glademm-vc100-2_4', 'gdkmm-vc100-2_4', 'pangomm-vc100-1_4',
								'atkmm-vc100-1_6', 'cairomm-vc100-1_0',
								'glibmm-vc100-2_4', 'giomm-vc100-2_4',
								'xml++-vc100-2_6', # 'sigc-vc100-2_0', # see sigcpp
								'gtkmm-vc100-2_4' ]
				elif self.cc == 'cl' and self.ccVersionNumber >= 9.0000 :
					libs += [	'glademm-vc90-2_4', 'gdkmm-vc90-2_4', 'pangomm-vc90-1_4',
								'atkmm-vc90-1_6', 'cairomm-vc90-1_0',
								'glibmm-vc90-2_4', 'giomm-vc90-2_4',
								'xml++-vc90-2_6', # 'sigc-vc90-2_0', # see sigcpp
								'gtkmm-vc90-2_4' ]
				elif self.cc == 'cl' and self.ccVersionNumber >= 8.0000 :
					libs += [	'glademm-vc80-2_4', 'gdkmm-vc80-2_4', 'pangomm-vc80-1_4',
								'atkmm-vc80-1_6', 'cairomm-vc80-1_0',
								'glibmm-vc80-2_4', 'giomm-vc80-2_4',
								'xml++-vc80-2_6', # 'sigc-vc80-2_0', # see sigcpp
								'gtkmm-vc80-2_4' ]
			else:
				# DEBUG
				if self.cc == 'cl' and self.ccVersionNumber >= 10.0000 :
					libs += [	'glademm-vc100-d-2_4', 'gdkmm-vc100-d-2_4', 'pangomm-vc100-d-1_4',
								'atkmm-vc100-d-1_6', 'cairomm-vc100-d-1_0',
								'glibmm-vc100-d-2_4', 'giomm-vc100-d-2_4',
								'xml++-vc100-d-2_6', 'sigc-vc100-d-2_0', # see sigcpp
								'gtkmm-vc100-d-2_4' ]
				elif self.cc == 'cl' and self.ccVersionNumber >= 9.0000 :
					libs += [	'glademm-vc90-d-2_4', 'gdkmm-vc90-d-2_4', 'pangomm-vc90-d-1_4',
								'atkmm-vc90-d-1_6', 'cairomm-vc90-d-1_0',
								'glibmm-vc90-d-2_4', 'giomm-vc90-d-2_4',
								'xml++-vc90-d-2_6', # 'sigc-vc90-d-2_0', # see sigcpp
								'gtkmm-vc90-d-2_4' ]
				elif self.cc == 'cl' and self.ccVersionNumber >= 8.0000 :
					libs += [	'glademm-vc80-d-2_4', 'gdkmm-vc80-d-2_4', 'pangomm-vc80-d-1_4',
								'atkmm-vc80-d-1_6', 'cairomm-vc80-d-1_0',
								'glibmm-vc80-d-2_4', 'giomm-vc80-d-2_4',
								'xml++-vc80-d-2_6', # 'sigc-vc80-d-2_0', # see sigcpp
								'gtkmm-vc80-d-2_4' ]

			return libs, []

		elif self.platform == 'posix':
			gtkglext	= [	'gtkglext-x11-1.0', 'gdkglext-x11-1.0',
							'GLU', 'GL', 'Xmu', 'Xt', 'SM', 'ICE',
							'pangox-1.0', 'X11' ]
			gtkmm		= [	'gtkmm-2.4', 'giomm-2.4', 'gdkmm-2.4', 'atkmm-1.6',
							'gtk-x11-2.0', 'pangomm-1.4', 'cairomm-1.0', 'glibmm-2.4',
							'sigc-2.0', 'gdk-x11-2.0', 'atk-1.0', 'gio-2.0',
							'pangoft2-1.0', 'gdk_pixbuf-2.0', 'pangocairo-1.0', 'cairo',
							'pango-1.0', 'freetype', 'fontconfig', 'gobject-2.0', 'gmodule-2.0',
							'glib-2.0' ]
			return gtkglext + gtkmm, []


	def getCPPFLAGS( self, version ):
		# compiler options
		if self.platform == 'win':
			if self.cc == 'cl' and self.ccVersionNumber >= 9.0000 :
				return ['/wd4250']
			elif self.cc == 'cl' and self.ccVersionNumber >= 8.0000 :
				return ['/wd4250', '/wd4312']
		elif self.platform == 'posix':
			return ['-Wl,--export-dynamic']

	def hasRuntimePackage( self, version ):
		return True
