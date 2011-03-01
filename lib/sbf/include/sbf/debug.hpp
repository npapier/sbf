// SConsBuildFramework - Copyright (C) 2011, Nicolas Papier.
// Distributed under the terms of the GNU Library General Public License (LGPL)
// as published by the Free Software Foundation.
// Author Nicolas Papier

#ifndef _SFB_DEBUG_HPP_
#define _SFB_DEBUG_HPP_

#include "sbf/sbf.hpp"


namespace sbf
{

// @todo sbfAssert()

/**
 * @brief Installs a top-level exception handler of each thread of a process.
 *
 * The exception handler generates a mini-dump on windows platform for post-mortem analysis.
 */
SBF_API void installToplevelExceptionHandler();

/**
 * @todo doc
 */
SBF_API int generateMiniDump( void * input );


} // namespace sbf

#endif // #ifndef _SFB_DEBUG_HPP_
