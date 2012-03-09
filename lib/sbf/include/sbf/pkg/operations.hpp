// SConsBuildFramework - Copyright (C) 2012, Nicolas Papier.
// Distributed under the terms of the GNU Library General Public License (LGPL)
// as published by the Free Software Foundation.
// Author Guillaume Brocker

#ifndef _SBF_PKG_OPERATIONS_HPP_
#define _SBF_PKG_OPERATIONS_HPP_


#include "sbf/sbf.hpp"
#include "sbf/pkg/Package.hpp"


namespace sbf
{

namespace pkg
{


/**
 * @brief	Retrieves all modules from all packages
 *
 * @param	result	a container where the collected modules will be inserted.
 */
template< typename ModuleSharedPtrContainerT >
void getAllModules( ModuleSharedPtrContainerT & result )
{
	// Walk the packages and append each package's module collection 
	// to the result collection.
	for( Package::const_iterator package = Package::begin(); package != Package::end(); ++package )
	{
		result.insert( result.end(), (*package)->moduleBegin(), (*package)->moduleEnd() );
	}
}


/**
 * @brief	Retrieves all pluggable modules from all packages
 *
 * @param	result	a container where the collected pluggable modules will be inserted.
 */
template< typename PlugableSharedPtrContainerT >
void getAllPluggables( PlugableSharedPtrContainerT & result )
{
	// Walk the packages and for each module that is a plugable, appends it to the result.
	for( Package::const_iterator package = Package::begin(); package != Package::end(); ++package )
	{
		result.insert( result.end(), (*package)->pluggableBegin(), (*package)->pluggableEnd() );
	}
}


/**
 * @brief	Loades all pluggable modules from all available packages.
 */
void SBF_API loadAllPluggables();


} // namespace pkg

} // namespace sbf


#endif // _SBF_PKG_OPERATIONS_HPP_

