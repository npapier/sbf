// SConsBuildFramework - Copyright (C) 2014, Nicolas Papier.
// Distributed under the terms of the GNU Library General Public License (LGPL)
// as published by the Free Software Foundation.
// Author Nicolas Papier

#include "sbf/simd/detail/CpuInformations.hpp"

#include <string.h>

#ifdef _MSC_VER
#include <intrin.h>
#endif

#if defined(__GNUC__) || defined(__clang__)
#include <cpuid.h>
#endif


namespace sbf
{

namespace simd
{

namespace detail
{


enum CPUIDFunction
{
	CPUID_VENDOR	= 0x00000000,
	CPUID_FEATURES	= 0x00000001
};


void getCPUID( const CPUIDFunction func, unsigned int&a, unsigned int &b, unsigned int &c, unsigned int &d )
{
#if defined(_MSC_VER)
	int info[4];
	__cpuid(info, static_cast<int>(func));
	a = static_cast<unsigned int>(info[0]);
	b = static_cast<unsigned int>(info[1]);
	c = static_cast<unsigned int>(info[2]);
	d = static_cast<unsigned int>(info[3]);
#elif defined(__GNUC__) || defined(__clang__)
	__get_cpuid(func, &a, &b, &c, &d);
#else
	a = b = c = d = 0;
#endif
}


// see http://msdn.microsoft.com/fr-fr/library/hskdteyh(v=vs.110).aspx
CPUInformations::CPUInformations()
{
	// Get CPU informations
	unsigned int a, b, c, d;
	getCPUID( CPUID_VENDOR, a, b, c, d );

	// Decode CPU string
	char CPUString[0x20];
	memset(CPUString, 0, sizeof(CPUString));
	*((int*)CPUString) = b;
	*((int*)(CPUString+4)) = d;
	*((int*)(CPUString+8)) = c;
	m_cpuString = std::string(CPUString);

	// Get additional CPU informations
	int nbIds = a;
	if ( nbIds >= 1 )
	{
		getCPUID( CPUID_FEATURES, a, b, c, d );
	}
	else
	{
		a = b = c = d = 0;
	}

	// Decode feature flags
	m_nLogicalProcessors	= ((b >> 16) & 0xff);
	m_bMultithreading		= (d & (1 << 28)) != 0;
	m_hasMMX				= (d & (1 << 23)) != 0;
	m_hasSSE				= (d & (1 << 25)) != 0;
	m_hasSSE2				= (d & (1 << 26)) != 0;
	m_hasSSE3				= (c & (1 << 0)) != 0;
	m_hasSSSE3				= (c & (1 << 9)) != 0;
	m_hasSSE41				= (c & (1 << 19)) != 0;
	m_hasSSE42				= (c & (1 << 20)) != 0;
	m_hasFMA				= (c & (1 <<12)) != 0;
	m_hasMOVBE				= (c & (1 <<22)) != 0;
	m_hasAVX				= (c & (1 << 28)) != 0;
}


const CPUInformations& getCPUInformations()
{
	static CPUInformations cpuInfos;

	return cpuInfos;
}



} // namespace detail

} // namespace simd

} // namespace sbf
