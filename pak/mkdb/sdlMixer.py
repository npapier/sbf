#!/usr/bin/env python

# SConsBuildFramework - Copyright (C) 2010, 2011, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

# ok for clx.y

# http://www.libsdl.org/projects/SDL_mixer/

descriptor = {
	'urls'			: ['http://www.libsdl.org/projects/SDL_mixer/release/SDL_mixer-devel-1.2.11-VC.zip'],

	'name'			: 'sdlMixer',
	'version'		: '1-2-11',

	'rootDir'		: 'SDL_mixer-1.2.11',
	'license'		: ['README', 'COPYING'],
	'include'		: ['include/'],
	'lib'			: ['lib/SDL_mixer.lib', 'lib/SDL_mixer.dll']
}
