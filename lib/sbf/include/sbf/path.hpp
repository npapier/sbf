// SConsBuildFramework - Copyright (C) 2009, Guillaume Brocker
// Distributed under the terms of the GNU General Public License (GPL)
// as published by the Free Software Foundation.
// Author Guillaume Brocker

#ifndef _SBF_PATH_HPP_
#define _SBF_PATH_HPP_

#include <string>
#include <boost/filesystem/path.hpp>

#include "sbf/sbf.hpp"
#include "sbf/Module.hpp"



namespace sbf
{

namespace path
{



/**
 * @brief	Defines possible standard paths.
 */
typedef enum
{
	Share,
	Var
} Type;



/**
 * @brief	Retrieves the string representation of the given path type.
 */
SBF_API const std::string toString( const Type & type );

/**
 * @brief	Retrieves the system path for the given type.
 *
 * @return	the absolute system path, empty if none
 */
SBF_API const boost::filesystem::path getTopLevel( const Type & type );

/**
 * @brief	Retrieves the system path for the given type, and creates the path if none exists.
 *
 * @return	the absolute system path, empty if none
 */
SBF_API const boost::filesystem::path getTopLevelSafe( const Type & type );

/**
 * @brief	Retrieves the system path for the given type and module.
 *
 * @param	type		the path type
 * @param	module	a module (the current by default)
 *
 * @return	the absolute system path, empty if none
 */
SBF_API const boost::filesystem::path get( const Type & type, const Module & module = Module() );

/**
 * @brief	Retrieves the system path for the given type and module, and creates the path if none exists.
 *
 * @param	type	the path type
 * @param	module	a module (the current by default)
 *
 * @return	the absolute system path, empty if an error occured
 */
SBF_API const boost::filesystem::path getSafe( const Type & type, const Module & module = Module() );

/**
 * @brief	Creates folders recursively if don't exists.
 *
 * @param	path		the path
 *
 * @return	true folder were create
 */
SBF_API const bool mkdirs( const std::string path );


} // namespace path

} // namespace sbf


#endif // _SBF_PATH_HPP_