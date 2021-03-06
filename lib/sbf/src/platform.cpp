// SConsBuildFramework - Copyright (C) 2014, Nicolas Papier.
// Distributed under the terms of the GNU Library General Public License (LGPL)
// as published by the Free Software Foundation.
// Author Nicolas Papier

#include "sbf/platform.hpp"

#include <malloc.h>



namespace sbf
{


void * malloc_aligned( const size_t size, const size_t alignment )
{
#ifdef WIN32
	return _aligned_malloc(size, alignment);
#elif __MACOSX__
	// alignment is always 16
	return malloc(size);
#elif POSIX
	return memalign(alignment, size);
#else
	#warning "Not yet implemented"
//#else // other (use valloc for page-aligned memory)
//	return valloc(size);
#endif
}


void free_aligned( void * memblock )
{
#ifdef WIN32
	_aligned_free( memblock );
#elif __MACOSX__
	free(memblock);
#elif POSIX
	free(memblock);
#else
	#warning "Not yet implemented"
//#else // other (use valloc for page-aligned memory)
	// valloc(size);
#endif
}


} // namespace sbf
