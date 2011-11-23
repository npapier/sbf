// SConsBuildFramework - Copyright (C) 2009, 2010, Guillaume Brocker and Nicolas Papier.
// Distributed under the terms of the GNU Library General Public License (LGPL)
// as published by the Free Software Foundation.
// Author Guillaume Brocker and Nicolas Papier

#ifndef _SBF_LOGGING_HPP
#define _SBF_LOGGING_HPP

#include "sbf/log/ILogging.hpp"



namespace sbf
{

namespace log
{

/**
 * @brief Implements logging interface based on standard outputs.
 */
struct SBF_API Logging : public ILogging
{
	/**
	 * @name Logging facilities methods
	 */
	//@{
	void logFatalError	( const char *szFormat, ... ) const;
	void logError		( const char *szFormat, ... ) const;
	void logWarning		( const char *szFormat, ... ) const;
	void logMessage		( const char *szFormat, ... ) const;

	void logVerbose		( const char *szFormat, ... ) const;
	void logStatus		( const char *szFormat, ... ) const;

	void logSysError	( const char *szFormat, ... ) const;

	void logDebug		( const char *szFormat, ... ) const;
	void logDebug		( const char *szFormat, va_list args ) const;
	void logTrace		( const char *szFormat, ... ) const;

	void flush			() const;
	//@}
};

} // namespace log

} // namespace sbf

#endif // #ifndef _SBF_LOGGING_HPP
