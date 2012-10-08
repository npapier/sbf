#include "sbf/pkg/Module.hpp"

#include <algorithm>
#include <iostream>
#include <boost/algorithm/string/trim.hpp>

#include "sbf/pkg/Package.hpp"


namespace sbf
{

namespace pkg
{


Module::Module( const std::string & name, const std::string & version, const boost::filesystem::path& rootPath, const boost::weak_ptr< Package > parent )
:	Component( name, version, rootPath, parent )
{}


Module::~Module()
{}


boost::shared_ptr< Module > Module::get( const std::string & name, const std::string & version )
{
	return Package::current()->findModule( name, version );
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
