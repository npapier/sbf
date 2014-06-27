// SConsBuildFramework - Copyright (C) 2014, Nicolas Papier.
// Distributed under the terms of the GNU Library General Public License (LGPL)
// as published by the Free Software Foundation.
// Author Nicolas Papier

#ifndef _SBF_PLATFORM_HPP_
#define _SBF_PLATFORM_HPP_

#include "sbf/sbf.hpp"

namespace sbf
{


/**
 * @name Compiler inlining control
 *
 * The FORCE_INLINE macro instruct the compiler to insert a copy of the function code each time the function is called.
 */
//@{
#ifdef _MSC_VER					// Visual C++ compiler
	#define FORCE_INLINE			__forceinline
#elif defined(__GNUG__) || defined(__clang__)		// The GNU C++ compiler defines __GNUG__, clang defines __clang__
	#define FORCE_INLINE			inline
#else
	#define FORCE_INLINE			inline
#endif
//@}


/**
 * @name Memory alignment related topic
 *
 * Control the alignment of user-defined data using ALIGN() and ALIGNED_STRUCT() macros.
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
SBF_API void free_aligned( void * memblock );

//@}


} // namespace sbf

#endif // _SBF_PLATFORM_HPP_
