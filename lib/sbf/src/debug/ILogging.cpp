// VGSDK - Copyright (C) 2004, 2011, Nicolas Papier.
// Distributed under the terms of the GNU Library General Public License (LGPL)
// as published by the Free Software Foundation.
// Author Nicolas Papier

#include "sbf/debug/ILogging.hpp"

#include "sbf/debug/GlobalLogger.hpp"

#ifdef _WIN32
 #include <windows.h>
#endif



namespace sbf
{

namespace debug
{

ILogging::~ILogging()
{
}


void ILogging::logAssert( const bool expression, const char * message, ... /*const char * strExpression, const char *file, unsigned int line, arg(s) for message... */) const
{
	// logs assertion
	if ( !expression )
	{
		va_list args;
		va_start( args, message );

		//logDebug( "Assertion failed: %s, file %s, line %i: %s", strExpression, file, line, message, args );
		std::string logDebugMessage = "Assertion failed: %s, file %s, line %i: ";
		logDebugMessage += std::string(message);
		logDebug( logDebugMessage.c_str(), args );

		va_end( args );
	}
	// else nothing to do

#ifdef _DEBUG
	if ( !expression && isAssertEnabled() )
	{
#ifdef _WIN32
		if ( IsDebuggerPresent() )
		{
			DebugBreak();
		}
		//else nothing to do
#else
		assert( false );
#endif
	}
#endif
}

} // namespace debug

} // namespace sbf
