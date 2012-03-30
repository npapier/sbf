#include "sbf/pkg/Module.hpp"

#include <algorithm>
#include <iostream>
#include <boost/algorithm/string/trim.hpp>

#include "sbf/pkg/Package.hpp"


namespace sbf
{

namespace pkg
{


Module::Module( const boost::weak_ptr< Package > package, const std::string & name, const std::string & version )
:	m_package( package ),
	m_name( name ),
	m_version( version )
{}


Module::~Module()
{}


boost::shared_ptr< Module > Module::get( const std::string & name, const std::string & version )
{
	return Package::current()->findModule( name, version );
}


const std::string & Module::getName() const
{
	return m_name;
}


boost::shared_ptr< Package > Module::getPackage() const
{
	return m_package.lock();
}


const boost::filesystem::path Module::getPath( const PathType & type ) const
{
	boost::filesystem::path	result;
	
	result  = getPackage()->getPath(type);
	result /= m_name;
	result /= m_version;

	return result;
}


const boost::filesystem::path Module::getPathSafe( const PathType & type ) const
{
	const boost::filesystem::path	result = getPath( type );

	boost::filesystem::create_directories( result );
	return result;
}


const std::string & Module::getVersion() const
{
	return m_version;
}


const std::string Module::getInfoFromFile() const
{
	const boost::filesystem::path	infoPath = getPath(SharePath) / "info.sbf";
	std::string						buffer;

	if( boost::filesystem::exists( infoPath ) )
	{
		std::ifstream	in( infoPath.string().c_str() );

		while( in )
		{
			std::string	line;

			std::getline( in, line );
			boost::algorithm::trim_right( line );
			buffer += line;
			buffer += "\n";
		}
	}
	else
	{
		std::cerr << "No information file available for module " << m_name << " (" << m_version << ")." << std::endl;
	}

	return buffer;
}


const bool Module::hasInfoFile() const
{
	const boost::filesystem::path	infoPath = getPath(SharePath) / "info.sbf";

	return boost::filesystem::exists( infoPath );
}


} // namespace pkg

} // namespace sbf
