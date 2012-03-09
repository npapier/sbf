// SConsBuildFramework - Copyright (C) 2012, Nicolas Papier.
// Distributed under the terms of the GNU Library General Public License (LGPL)
// as published by the Free Software Foundation.
// Author Guillaume Brocker

#ifndef _SBF_PKG_TYPES_HPP_
#define _SBF_PKG_TYPES_HPP_

#include <string>
#include "sbf/sbf.hpp"


namespace sbf
{

namespace pkg
{

/**
 * @brief	Defines possible standard paths.
 */
typedef enum
{
	BinPath,
	SharePath,
	VarPath
} PathType;


/**
 * @brief	Retrieves the string representation of the given path type.
 */
SBF_API const std::string toString( const PathType & pathType );


} // namespace pkg

} // namespace sbf


#endif // _SBF_PKG_TYPES_HPP_
