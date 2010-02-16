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



const boost::filesystem::path getSafe( const Type & type, const Module & module )
{
	namespace bfs = boost::filesystem;

	const bfs::path	path( get(type, module) );

	if ( bfs::exists( path ) == false )
	{
		bfs::create_directories( path );
	}
	
	return path;
}



const bool mkdirs( const std::string path )
{
	namespace bfs = boost::filesystem;

	if ( bfs::exists( path ) == false )
	{
		bfs::create_directories( path );
		return true;
	}
	else
	{
		return false;
	}
}


} // namespace path

} // namespace sbf

