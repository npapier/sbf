// SConsBuildFramework - Copyright (C) 2014, Nicolas Papier.
// Distributed under the terms of the GNU Library General Public License (LGPL)
// as published by the Free Software Foundation.
// Author Nicolas Papier

#include "sbf/simd/simd.hpp"

#include "sbf/simd/detail/CpuInformations.hpp"
#include <sstream>

#ifdef WIN32
	#if _M_IX86_FP == 0
	#pragma message( "arch option was not used" )
	#elif _M_IX86_FP == 1
	#pragma message( "arch option:SSE was used" )
	#elif _M_IX86_FP == 2
	#pragma message( "arch option:SSE2 or AVX was used" )
	#endif
#endif



namespace sbf
{

namespace simd
{


// ******
const std::string getCPU()			{ return detail::getCPUInformations().m_cpuString; }

const int  getLogicalProcessors()	{ return detail::getCPUInformations().m_nLogicalProcessors; }
const bool hasMultithreading()		{ return detail::getCPUInformations().m_bMultithreading; }

const bool hasMMX()					{ return detail::getCPUInformations().m_hasMMX; }
const bool hasSSE()					{ return detail::getCPUInformations().m_hasSSE; }
const bool hasSSE2()				{ return detail::getCPUInformations().m_hasSSE2; }
const bool hasSSE3()				{ return detail::getCPUInformations().m_hasSSE3; }
const bool hasSSSE3()				{ return detail::getCPUInformations().m_hasSSSE3; }
const bool hasSSE41()				{ return detail::getCPUInformations().m_hasSSE41; }
const bool hasSSE42()				{ return detail::getCPUInformations().m_hasSSE42; }
const bool hasFMA()					{ return detail::getCPUInformations().m_hasFMA; }
const bool hasMOVBE()				{ return detail::getCPUInformations().m_hasMOVBE; }
const bool hasAVX()					{ return detail::getCPUInformations().m_hasAVX; }

const std::string getFullDescriptions()
{
	std::ostringstream ssStr;

	ssStr << "CPU: " << getCPU() << std::endl;

	//ssStr << "Logical processor: " << getLogicalProcessors() << std::endl;
	ssStr << "Multithreading: " << hasMultithreading() << std::endl;

	if ( hasMMX() )		ssStr << "MMX ";
	if ( hasSSE() )		ssStr << "SSE ";
	if ( hasSSE2() )	ssStr << "SSE2 ";
	if ( hasSSE3() )	ssStr << "SSE3 ";
	if ( hasSSSE3() )	ssStr << "SSSE3 ";
	if ( hasSSE41() )	ssStr << "SSE41 ";
	if ( hasSSE42() )	ssStr << "SSE42 ";
	if ( hasFMA() )		ssStr << "FMA ";
	if ( hasMOVBE() )	ssStr << "MOVBE ";
	if ( hasAVX() )		ssStr << "AVX ";

	return ssStr.str();
}


// ******
void * malloc_aligned( const size_t size, const size_t alignment )
{
#ifdef WIN32
	return _aligned_malloc(size, alignment);
#elif __MACOSX__
	// alignment is always 16
	return malloc(size);
#else // POSIX
	return memalign(alignment, size);
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
#else // POSIX
	free(memblock);
//#else // other (use valloc for page-aligned memory)
	// valloc(size);
#endif
}


// ******
void load( double * source, __m128d * destination, const int numElements )
{
	double * currentSource = source;
	__m128d *currentDestination	= destination;
	for( int i=0; i<numElements; ++i )
	{
		*currentDestination = _mm_load_sd( currentSource );
		++currentSource;
		++currentDestination;
	}
}


void store( __m128d * source, double * destination, const int numElements )
{
	__m128d *currentSource		= source;
	double *currentDestination	= destination;

	for( int i=0; i<numElements; ++i )
	{
		_mm_store_sd( currentDestination, *currentSource );
		++currentDestination;
		++currentSource;
	}
}


void load_twice( double * source, __m128d * destination, const int numElements )
{
	double * currentSource = source;
	__m128d *currentDestination = destination;
	for( int i=0; i<numElements; ++i )
	{
		*currentDestination = _mm_load1_pd( currentSource );
		++currentSource;
		++currentDestination;
	}
}


void load( double * source1, double * source2, __m128d * destination, const int numElements )
{
	__m128d nullSIMD = _mm_set1_pd( 0.f );

	double * currentSource1 = source1;
	double * currentSource2 = source2;
	__m128d *currentDestination = destination;
	for( int i=0; i<numElements; ++i )
	{
		*currentDestination = _mm_loadl_pd( nullSIMD, currentSource1 );
		*currentDestination = _mm_loadh_pd( *currentDestination, currentSource2 );
		++currentSource1;
		++currentSource2;
		++currentDestination;
	}
}


void store( __m128d * source, double * destination1, double * destination2, const int numElements )
{
	__m128d * currentSource = source;
	double * currentDestination1 = destination1;
	double * currentDestination2 = destination2;

	for( int i=0; i<numElements; ++i )
	{
		_mm_storel_pd( currentDestination1, *currentSource );
		_mm_storeh_pd( currentDestination2, *currentSource );
		++currentDestination1;
		++currentDestination2;
		++currentSource;
	}
}


} // namespace simd

} // namespace sbf
