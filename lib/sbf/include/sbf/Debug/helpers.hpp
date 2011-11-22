// SConsBuildFramework - Copyright (C) 2009, 2010, Guillaume Brocker and Nicolas Papier.
// Distributed under the terms of the GNU Library General Public License (LGPL)
// as published by the Free Software Foundation.
// Author Guillaume Brocker and Nicolas Papier

#ifndef _SBF_HELPERS_HPP
#define _SBF_HELPERS_HPP

#include "sbf/debug/GlobalLogger.hpp"
#include "sbf/debug/ILogging.hpp"


///@todo Disables some log function in debug

#define sbfLogError( arg1, ... )				sbf::debug::get().logError( (arg1), __VA_ARGS__ )

#define sbfLogWarning( arg1, ... )				sbf::debug::get().logWarning( (arg1), __VA_ARGS__)

#define sbfLogStatus( arg1, ... )				sbf::debug::get().logStatus( (arg1), __VA_ARGS__ )

#define sbfLogMessage( arg1, ... )				sbf::debug::get().logMessage( (arg1), __VA_ARGS__ )

#define sbfLogTrace( arg1, ... )				sbf::debug::get().logTrace( (arg1), __VA_ARGS__ )

#define sbfLogTraceUI( arg1, ... )				sbf::debug::get().logTrace( "[UI] " arg1, __VA_ARGS__ )
#define sbfLogTraceIO( arg1, ... )				sbf::debug::get().logTrace( "[IO] " arg1, __VA_ARGS__ )

#ifdef _DEBUG
#define sbfLogDebug( arg1, ... )				sbf::debug::get().logDebug( (arg1), __VA_ARGS__ )
#else
#define sbfLogDebug( arg1, ... )				sbf::debug::get().logDebug( (arg1), __VA_ARGS__ )
#endif



#define sbfAssert( expression )					sbf::debug::get().logAssert( (expression), "", (#expression), __FILE__, __LINE__ )
#define sbfAssertN( expression, message, ... )	sbf::debug::get().logAssert( (expression), (message), (#expression), __FILE__, __LINE__, __VA_ARGS__ )



#endif //#ifndef _SBF_HELPERS_HPP
