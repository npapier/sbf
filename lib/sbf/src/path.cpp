// SConsBuildFramework - Copyright (C) 2009, Guillaume Brocker
// Distributed under the terms of the GNU General Public License (GPL)
// as published by the Free Software Foundation.
// Author Guillaume Brocker

#include "sbf/path.hpp"

#include <cassert>



namespace sbf
{

namespace path
{


const std::string toString( const Type & type )
{
	std::string	result;
	
	switch( type )
	{
	case Var:	result = "var";   break;
	case Share:	result = "share"; break;
	default:	assert( false && "Unsupported sbf::path::Type" );
	}
	
	return result;
}



const boost::filesystem::path getTopLevel( const Type & type )
{
	const boost::filesystem::path	initialPath = boost::filesystem::initial_path();
	boost::filesystem::path			basePath;
	
	basePath = initialPath / toString(type);
	if( boost::filesystem::is_directory(basePath) )
	{
		return basePath;
	}

	basePath = initialPath / boost::filesystem::path("..") / toString(type);
	if( boost::filesystem::is_directory(basePath) )
	{
		return basePath;
	}

	return boost::filesystem::path();
}



const boost::filesystem::path get( const Type & type, const Module & module )
{
	const boost::filesystem::path	topLevelPath( getTopLevel(type) );
	
	if( topLevelPath.empty() )
	{
		return boost::filesystem::path();
	}
	else
	{
		return topLevelPath / boost::filesystem::path(module.getName()) / boost::filesystem::path(module.getVersion());
	}
}



} // namespace path

} // namespace sbf

