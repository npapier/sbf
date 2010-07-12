# SConsBuildFramework - Copyright (C) 2010, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

# ok for clx.y

# http://www.libsdl.org
descriptor = {
	'urls'			: ['http://www.libsdl.org/release/SDL-devel-1.2.14-VC8.zip'],

	'name'			: 'sdl',
	'version'		: '1-2-14',

	'rootDir'		: 'SDL-1.2.14',
	'license'		: ['README-SDL.txt', 'COPYING'],
	'include'		: ['include/'],
	'lib'			: ['lib/*.dll', 'lib/*.lib']
}
