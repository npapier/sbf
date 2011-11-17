// SConsBuildFramework - Copyright (C) 2009, 2010, Guillaume Brocker and Nicolas Papier.
// Distributed under the terms of the GNU Library General Public License (LGPL)
// as published by the Free Software Foundation.
// Author Guillaume Brocker and Nicolas Papier

#ifndef _SBF_ILOGGING_HPP
#define _SBF_ILOGGING_HPP

#include <cstdarg>
#include "sbf/sbf.hpp"



namespace sbf
{

/**
 * @brief Defines interface for logging facilities.
 */
struct SBF_API ILogging
{
	/**
	 * @brief Virtual destructor
	 */
	virtual ~ILogging();
	
	/**
	 * @name Logging facilities methods
	 */
	//@{
	virtual void logFatalError	( const char *szFormat, ... ) const=0;
	virtual void logError		( const char *szFormat, ... ) const=0;
	virtual void logWarning		( const char *szFormat, ... ) const=0;
	virtual void logMessage		( const char *szFormat, ... ) const=0;

	virtual void logVerbose		( const char *szFormat, ... ) const=0;
	virtual void logStatus		( const char *szFormat, ... ) const=0;

	virtual void logSysError	( const char *szFormat, ... ) const=0;

	virtual void logDebug		( const char *szFormat, ... ) const=0;
	virtual void logDebug		( const char *szFormat, va_list args ) const=0;
	virtual void logTrace		( const char *szFormat, ... ) const=0;


	virtual void flush			() const=0;
	//@}


	/**
	 * @name vgsdk assertion system
	 */
	//@{

	/**
	 * @brief Raises a vgsdk assertion if expression is false, otherwise do noting.
	 *
	 * Assertion(s) are logged using logDebug() in debug and release configuration.
	 * If and only if library has been built in debug configuration, it raises an 
	 * assertion (i.e. assert(false)) or causes a breakpoint exception to occur in the current process (on windows platform).
	 */
	void logAssert( const bool expression, const char * message, ... /*const char * strExpression, const char *file, unsigned int line, arg(s) for message... */) const;
	//@}
};



} // namespace sbf

#endif // #ifndef _SBF_ILOGGING_HPP
