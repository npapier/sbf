// SConsBuildFramework - Copyright (C) 2014, Nicolas Papier.
// Distributed under the terms of the GNU Library General Public License (LGPL)
// as published by the Free Software Foundation.
// Author Nicolas Papier

#ifndef _SBF_SIMD_SIMD_HPP_
#define _SBF_SIMD_SIMD_HPP_

#include <string>
#include "sbf/sbf.hpp"


namespace sbf
{

namespace simd
{


/**
 * @name Retrieving informations about CPU
 *
 * Cpu brand name, supported instruction sets...
 */
//@{

/**
 * @brief Returns the CPU brand name
 */
SBF_API const std::string getCPU();

/**
 * @brief Returns the number of logical processors
 *
 * @remarks The returned value is rounded up to the next power of 2
 */
SBF_API const int  getLogicalProcessors();

/**
 * @brief Returns if multithreading is available
 */
SBF_API const bool hasMultithreading();


/**
 * @brief Returns if MMX instruction set is available
 */
SBF_API const bool hasMMX();

/**
 * @brief Returns if SSE instruction set is available
 */
SBF_API const bool hasSSE();

/**
 * @brief Returns if SSE2 instruction set is available
 */
SBF_API const bool hasSSE2();

/**
 * @brief Returns if SSE3 instruction set is available
 */
SBF_API const bool hasSSE3();

/**
 * @brief Returns if SSSE2 instruction set is available
 */
SBF_API const bool hasSSSE3();

/**
 * @brief Returns if SSE 4.1 instruction set is available
 */
SBF_API const bool hasSSE41();

/**
 * @brief Returns if SSE 4.2 instruction set is available
 */
SBF_API const bool hasSSE42();

/**
 * @brief Returns if FMA instruction set is available
 */
SBF_API const bool hasFMA();

/**
 * @brief Returns if MOVBE instruction set is available
 */
SBF_API const bool hasMOVBE();

/**
 * @brief Returns if AVX instruction set is available
 */
SBF_API const bool hasAVX();


/**
 * @brief Returns a string containing a printable description of the capabilities of the cpu (see previous functions).
 */
SBF_API const std::string getFullDescriptions();
//@}


/**
 * @name Alignment related topic
 *
 * Control the alignment of user-defined data using ALIGN() and ALIGNED_STRUCT() macros.
 *
 * Allocation and deallocation of aligned (16 byte aligned) memory using malloc() and free() functions.
 */
//@{
#ifdef _MSC_VER					// Visual C++ compiler
	#define ALIGN(x)			__declspec(align(x))
	#define ALIGNED_STRUCT(x)	__declspec(align(x)) struct
#elif defined(__GNUG__) || defined(__clang__)		// The GNU C++ compiler defines __GNUG__, clang defines __clang__
	#define ALIGN(x)			__attribute__((aligned(x)))
	#define ALIGNED_STRUCT(x)	struct __attribute__((aligned(x)))
#else
	#define ALIGN(x)
	#define ALIGNED_STRUCT(x)	struct
#endif


/**
 * @brief Allocates aligned memory
 *
 * @param size			number of bytes that have to be allocated
 * @param alignment		specifies the desired alignment
 */
SBF_API void * malloc_aligned( const size_t size, const size_t alignment = 16 );

/**
 * @brief Frees the given block of memory
 *
 * @remarks Uses it only for memory allocated using malloc_aligned().
 */
SBF_API  void free_aligned( void * memblock );
//@}


/**
 * @name Data copying interface
 */
//@{


/**
 * @brief Copies numElements from source to destination
 *
 * for i in [0, numElements[, 
 *		destination[i].r0 = source[i]
 *		destination[i].r1 = 0
 */
SBF_API void load( double * source, __m128d * destination, const int numElements );

/**
 * @brief Copies numElements from source to destination
 *
 * for i in [0, numElements[, 
 * 		destination[i] = source[i].r0
 */
SBF_API void store( __m128d * source, double * destination, const int numElements );

/**
 * @brief Copies numElements from source to destination
 *
 * for i in [0, numElements[,
 * 		destination[i].r0 = source[i]
 *		destination[i].r1 = source[i]
 */
SBF_API void load_twice( double * source, __m128d * destination, const int numElements );

/**
 * @brief Copies numElements from source1 and source2 to destination
 *
 * for i in [0, numElements[,
 *		destination[i].r0 = source1[i]
 * 		destination[i].r1 = source2[i]
 */
SBF_API void load( double * source1, double * source2, __m128d * destination, const int numElements );

/**
 * @brief Copies numElements from source to destination1 and destination2
 *
 * for i in [0, numElements[,
 *		destination1[i] = source[i].r0
 *		destination2[i] = source[i].r1
 */
SBF_API void store( __m128d * source, double * destination1, double * destination2, const int numElements );
//@}


} // namespace simd

} // namespace sbf

#endif // _SBF_SIMD_SIMD_HPP_
