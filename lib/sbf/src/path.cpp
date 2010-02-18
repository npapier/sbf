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



const boost::filesystem::path getTopLevelSafe( const Type & type )
{
	namespace bfs = boost::filesystem;


	bfs::path	basePath = getTopLevel( type );
	
	if( basePath.empty() )
	{
		// Retrieves the initial path.
		const bfs::path	initialPath	= bfs::initial_path();

		// Builds the therical desired toplevel path relatively to the bin directory.
		if( initialPath.filename() == "bin" )
		{
			basePath = initialPath / ".." / toString(type);
		}
		else if( bfs::exists(initialPath/"bin") )
		{
			basePath = initialPath / toString(type);
		}

		// Builds the toplevel path.
		if( !bfs::create_directories(basePath) )
		{
			basePath.clear();
		}
	}
	
	return basePath;
}



const boost::filesystem::path get( const Type & type, const Module & module )
{
	namespace bfs = boost::filesystem;


	const bfs::path	topLevelPath( getTopLevel(type) );
	
	if( topLevelPath.empty() )
	{
		return bfs::path();
	}
	else
	{
		return topLevelPath / bfs::path(module.getName()) / bfs::path(module.getVersion());
	}
}



const boost::filesystem::path getSafe( const Type & type, const Module & module )
{
	namespace bfs = boost::filesystem;


	// Gets the top level path
	const bfs::path	topLevelPath( getTopLevelSafe(type) );
	
	if( topLevelPath.empty() )
	{
		return bfs::path();
	}
	

	// Builds the desired path.
	bfs::path	path = topLevelPath / bfs::path(module.getName()) / bfs::path(module.getVersion());
	
	if( bfs::create_directories(path) == false )
	{
		path.clear();
	}
	
	return path;
}



const bool mkdirs( const std::string path )
{
	namespace bfs = boost::filesystem;

	if ( !path.empty() && !bfs::exists( path )  )
	{
		return bfs::create_directories( path );
	}
	else
	{
		return false;
	}
}


} // namespace path

} // namespace sbf

