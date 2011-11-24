// SConsBuildFramework - Copyright (C) 2009, 2010, Guillaume Brocker and Nicolas Papier.
// Distributed under the terms of the GNU Library General Public License (LGPL)
// as published by the Free Software Foundation.
// Author Guillaume Brocker and Nicolas Papier

#ifndef _SFB_GLOBAL_HPP
#define _SFB_GLOBAL_HPP

#include <boost/shared_ptr.hpp>

#include "sbf/sbf.hpp"

namespace sbf
{

namespace log
{

struct ILogging;

/**
 * @brief	Holds the global logger which is sbf::Logging by default.
 */
struct SBF_API GlobalLogger
{
	/**
	 * @brief	Access to the global debug logger.
	 *
	 * @remark	While the logger instance is managed by a shared pointer,
	 * 			a reference to it is returned for convenience.
	 */
	static ILogging& get();

	/**
	 * @brief	Installs a new logger.
	 *
	 * @param	logger	a shared pointer to the new logger
	 *
	 * @pre		logger != 0
	 */
	static void set( boost::shared_ptr< ILogging > logger );

	/**
	 * @brief	Installs a new logger that don't need construction time parameters.
	 */
	template< typename LoggingType >
	static void set()
	{
		set( boost::shared_ptr< LoggingType >( new LoggingType()) );
	}

	/**
	 * @brief Determines whether the vgsdk assertion system is enabled.
	 *
	 * @return true if vgsdk assertion system is enabled, false otherwise.
	 */
	static const bool isAssertEnabled();

	/**
	 * @brief Enables or disables the vgsdk assertion system depending on the value of the parameter isEnabled.
	 *
	 * @param isEnabled		true when the vgsdk assertion system must be enabled, false otherwise
	 */
	static void setAssertEnabled( const bool enabled = true );

private:

	static boost::shared_ptr< ILogging >	m_globalLogger;

	static bool								m_assertEnabled;
};



/**
 * @brief	Access to the global logger.
 *
 * @return	a reference to the global logger
 *
 * @see		Global::get
 */
SBF_API ILogging& get();

/**
 * @brief	Installs a global logger.
 *
 * @param	logger	a shared pointer to a new logger
 *
 * @see		Global::set
 */
SBF_API void set( boost::shared_ptr< ILogging > logger );

/**
 * @brief	Installs a new logger that don't need construction time parameters.
 */
template< typename LoggingType >
void set()
{
	GlobalLogger::set< LoggingType >();
}


/**
 * @brief Determines whether the vgsdk assertion system is enabled.
 *
 * @return true if vgsdk assertion system is enabled, false otherwise.
 */
SBF_API const bool isAssertEnabled();

/**
 * @brief Enables or disables the vgsdk assertion system depending on the value of the parameter isEnabled.
 *
 * @param isEnabled		true when the vgsdk assertion system must be enabled, false otherwise
 */
SBF_API void setAssertEnabled( const bool enabled = true );


} // namespace log

} // namespace sbf

#endif //#ifndef _SFB_GLOBAL_HPP
