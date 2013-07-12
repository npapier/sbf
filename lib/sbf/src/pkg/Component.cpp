#include "sbf/pkg/Component.hpp"

#include <iostream>
#include <boost/filesystem/convenience.hpp>
#include <boost/property_tree/xml_parser.hpp>

#include "sbf/pkg/Package.hpp"


namespace sbf
{

namespace pkg
{


Component::Component( const std::string & name, const std::string & version, const boost::filesystem::path & rootPath, const boost::weak_ptr< Package > parent )
:	m_parent( parent ),
	m_name( name ),
	m_rootPath( rootPath ),
	m_version( version )
{
	namespace bpt = boost::property_tree;
	namespace bfs = boost::filesystem;

	// We temporary "deconstify" the constant data structure in order to populate from the disk.
	bpt::ptree	* deconstedData = const_cast< bpt::ptree* >( &m_constData );

	// Support for module.xml files.
	// These files should be converted into component.xml.
	const bfs::path	oldFilename = getPath(SharePath) / "module.xml";
	if( bfs::exists(oldFilename) )
	{
		try
		{
			// Reads data in the old fashion.
			bpt::ptree	oldData;
			bpt::read_xml( oldFilename.string(), oldData );

			// Puts old data in to the new fashion.
			deconstedData->put_child( "component", oldData.get_child("module") );
		}
		catch( bpt::xml_parser_error & xpe )
		{
			std::cerr << "Error while loading component meta data file " << oldFilename << ". " << xpe.what() << std::endl;
		}
		catch( bpt::ptree_bad_path & pbp )
		{
			std::cerr << "Error while converting old component meta file " << oldFilename << ". " << pbp.what() << std::endl;
		}

		// Skip further processing.
		return;
	}
	
	// Loads constant meta data.
	{
		const bfs::path	filename = getPath(SharePath) / "component.xml";
		if( bfs::exists(filename) )
		{
			try
			{
				// Loads meta data from an xml file.
				bpt::read_xml( filename.string(), *deconstedData );
			}
			catch( bpt::xml_parser_error & )
			{
				std::cerr << "Error while loading component meta data file " << filename << "." << std::endl;
			}		
		}
	}

	// Loads editable meta data.
	{
		const bfs::path	filename = getPath(VarPath) / "component.xml";
		if( bfs::exists(filename) )
		{
			try
			{
				// Loads meta data from an xml file.
				bpt::read_xml( filename.string(), m_editableData );
			}
			catch( bpt::xml_parser_error & )
			{
				std::cerr << "Error while loading component meta data file " << filename << "." << std::endl;
			}		
		}
	}
}


const std::string Component::getDescription() const
{
	return m_constData.get( "component.description", std::string() );
}


const std::string Component::getLabel() const
{
	return m_constData.get( "component.label", getName() );
}


const Component::TagContainer Component::getTags() const
{
	namespace		bpt = boost::property_tree;
	TagContainer	result;

	try
	{
		const bpt::ptree	& tags = m_constData.get_child( "component.tags" );

		for( bpt::ptree::const_iterator i = tags.begin(); i != tags.end(); ++i )
		{
			result.push_back( i->second.get_value< std::string >() );
		}
	}
	catch( bpt::ptree_bad_path & )
	{}

	return result;
}


const std::string Component::getTagsString() const
{
	namespace	bpt = boost::property_tree;
	std::string	result;

	try
	{
		const bpt::ptree & tags = m_constData.get_child( "component.tags" );

		for( bpt::ptree::const_iterator i = tags.begin(); i != tags.end(); ++i )
		{
			if( !result.empty() ) result += " ";
			result += i->second.get_value< std::string >();
		}
	}
	catch( bpt::ptree_bad_path & )
	{}

	return result;
}


const bool Component::hasTag( const std::string & tag ) const
{
	namespace	bpt = boost::property_tree;

	try
	{
		const bpt::ptree	& tags = m_constData.get_child( "component.tags" );

		for( bpt::ptree::const_iterator i = tags.begin(); i != tags.end(); ++i )
		{
			if( i->second.get_value< std::string >() == tag )
			{
				return true;
			}
		}
	}
	catch( bpt::ptree_bad_path & )
	{
		return false;
	}

	return false;
}


const boost::property_tree::ptree Component::getDataAsTree( const std::string & key ) const
{
	const std::string			path = "component.payload." + key;
	boost::property_tree::ptree	result;

	result = m_editableData.get_child( path, boost::property_tree::ptree() );
	if( !result.empty() )
	{
		return result;
	}

	result = m_constData.get_child( path, boost::property_tree::ptree() );
	return result;
}


const std::string Component::getDataAsString( const std::string & key ) const
{
	const std::string	path = "component.payload." + key;
	std::string			result;

	result =  m_editableData.get( path, std::string() );
	if( !result.empty() )
	{
		return result;
	}

	return m_constData.get( path, std::string() );
}


const std::string Component::getName() const
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


const boost::filesystem::path Component::getPath( const PathType & type ) const
{
	boost::filesystem::path	result;
	
	result  = m_rootPath;
	result /= toString(type);
	result /= m_name;
	result /= m_version;

	return result;
}


const boost::filesystem::path Component::getPathSafe( const PathType & type ) const
{
	const boost::filesystem::path	result = getPath(type);

	if( type == VarPath )
	{
		try
		{
			boost::filesystem::create_directories( result );
		}
		catch( const std::exception & e )
		{
			std::cerr << "Error while creating directories. " << e.what() << std::endl;
		}
	}
	return result;
}


const boost::filesystem::path Component::getRootPath() const
{
	return m_rootPath;
}


const std::string & Component::getVersion() const
{
	return m_version;
}


void Component::saveData() const
{
	const boost::filesystem::path	filename = getPathSafe(VarPath)/"component.xml";
	std::ofstream					os( filename.string().c_str() );

	boost::property_tree::write_xml( os, m_editableData );
}


void Component::setData( const std::string & key, const std::string & data )
{
	m_editableData.put( "component.payload."+key, data );
	saveData();
}

const bool Component::hasMetaData() const
{
	return !m_constData.empty();
}




} // namespace pkg

} // namespace sbf
