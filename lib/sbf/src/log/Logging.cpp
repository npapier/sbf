// SConsBuildFramework - Copyright (C) 2009, 2010, Guillaume Brocker and Nicolas Papier.
// Distributed under the terms of the GNU Library General Public License (LGPL)
// as published by the Free Software Foundation.
// Author Guillaume Brocker and Nicolas Papier

#include "sbf/log/Logging.hpp"

#include <stdio.h>
#include <stdarg.h>

#include <string>

namespace sbf
{

namespace log
{


void Logging::logFatalError( const char *szFormat, ... ) const
{
	va_list marker;
	va_start( marker, szFormat );

	fprintf( stderr, "Fatal Error: " );
	vfprintf( stderr, szFormat, marker );
	fprintf( stderr, "\n" );

	va_end( marker );
}


void Logging::logError( const char *szFormat, ... ) const
{
	va_list marker;
	va_start( marker, szFormat );

	fprintf( stderr, "Error: " );
	vfprintf( stderr, szFormat, marker );
	fprintf( stderr, "\n" );

	va_end( marker );
}


void Logging::logWarning( const char *szFormat, ... ) const
{
	va_list marker;
	va_start( marker, szFormat );

	fprintf( stderr, "Warning: " );
	vfprintf( stderr, szFormat, marker );
	fprintf( stderr, "\n" );

	va_end( marker );
}


void Logging::logMessage( const char *szFormat, ... ) const
{
	va_list marker;
	va_start( marker, szFormat );

	vfprintf( stdout, szFormat, marker );
	fprintf( stdout, "\n" );

	va_end( marker );
}


void Logging::logVerbose( const char *szFormat, ... ) const
{

#ifdef _DEBUG
	va_list marker;
	va_start( marker, szFormat );

	vfprintf( stdout, szFormat, marker );
	fprintf( stdout, "\n" );

	va_end( marker );
#endif

}


void Logging::logStatus( const char *szFormat, ... ) const
{
	va_list marker;
	va_start( marker, szFormat );

	vfprintf( stdout, szFormat, marker );
	fprintf( stdout, "\n" );

	va_end( marker );
}


void Logging::logSysError( const char *szFormat, ... ) const
{
	va_list marker;
	va_start( marker, szFormat );

	fprintf( stderr, "Sys Error: " );
	vfprintf( stderr, szFormat, marker );
	fprintf( stderr, "\n" );

	va_end( marker );
}


void Logging::logDebug( const char *szFormat, ... ) const
{
#ifdef _DEBUG
	va_list marker;
	va_start( marker, szFormat );

	fprintf( stderr, "Debug: " );
	vfprintf( stderr, szFormat, marker );
	fprintf( stderr, "\n" );

	va_end( marker );
#endif
}


void Logging::logDebug( const char *szFormat, va_list args ) const
{
#ifdef _DEBUG
	fprintf( stderr, "Debug: " );
	vfprintf( stderr, szFormat, args );
	fprintf( stderr, "\n" );
#endif
}


void Logging::logTrace( const char *szFormat, ... ) const
{

#ifdef _DEBUG
	va_list marker;
	va_start( marker, szFormat );

	fprintf( stdout, "Trace: " );
	vfprintf( stdout, szFormat, marker );
	fprintf( stdout, "\n" );

	va_end( marker );
#endif

}


void Logging::flush() const
{
	fflush( stdout );
	fflush( stderr );
}


} // namespace log

} // namespace sbf
