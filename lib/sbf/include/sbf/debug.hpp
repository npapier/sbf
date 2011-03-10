// SConsBuildFramework - Copyright (C) 2011, Nicolas Papier.
// Distributed under the terms of the GNU Library General Public License (LGPL)
// as published by the Free Software Foundation.
// Author Nicolas Papier

#ifndef _SFB_DEBUG_HPP_
#define _SFB_DEBUG_HPP_

#include "sbf/sbf.hpp"


namespace sbf
{



enum CoreType
{
	CoreNormal,	///< Default value. Typical use case: software is deployed on client workstation and mini-dump is small to be sent be email.
	CoreFull	///< Use case: debug software on a developer workstation. Mini-dump could be big...
};

/**
 * @brief Installs a top-level exception handler of each thread of a process.
 *
 * The exception handler generates a mini-dump on windows platform for post-mortem analysis.
 *
 * @param coreType		the type of information to be generated in the core file
 */
SBF_API void installToplevelExceptionHandler( const CoreType coreType = CoreNormal );

} // namespace sbf

#endif // #ifndef _SFB_DEBUG_HPP_
