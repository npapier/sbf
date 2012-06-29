#include "sbf/pkg/Component.hpp"

#include <iostream>
#include <boost/filesystem/convenience.hpp>


namespace sbf
{

namespace pkg
{


Component::Component( const std::string & name, const std::string & version, const boost::weak_ptr< Package > parent )
:	m_parent( parent ),
	m_name( name ),
	m_version( version )
{}


const std::string & Component::getName() const
{
	return m_name;
}


const std::string Component::getNameAndVersion() const
{
	return m_version.empty() ? m_name : m_name+"_"+m_version;
}


const boost::shared_ptr< Package > Component::getParent() const
{
	return m_parent.lock();
}


const boost::filesystem::path Component::getPathSafe( const PathType & type ) const
{
	const boost::filesystem::path	result = getPath(type);

	try
	{
		boost::filesystem::create_directories( result );
	}
	catch( const std::exception & e )
	{
		std::cerr << "Error while creating directories. " << e.what() << std::endl;
	}
	return result;
}	


const std::string & Component::getVersion() const
{
	return m_version;
}



} // namespace pkg

} // namespace sbf
