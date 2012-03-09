#include "sbf/pkg/Pluggable.hpp"

#ifdef WIN32
#include <windows.h>
#endif

#include <iostream>
#include <boost/property_tree/xml_parser.hpp>

#include "sbf/operations.hpp"


namespace sbf
{

namespace pkg
{


struct Pluggable::DynLib
{
	DynLib( const std::string & name, const std::string & version ) : m_name(name), m_version(version)
	{}

	virtual ~DynLib()
	{}

	virtual operator const bool() const = 0; ///< Tells if the library has been loaded.
	virtual void * getSymbol( const std::string & name ) const = 0; ///< Retrieves a pointer to a symbol of the library for the given name.

protected:	
	const std::string	m_name;
	const std::string	m_version;
};

#ifdef WIN32

struct Win32Lib : public Pluggable::DynLib
{
	Win32Lib( const std::string & name, const std::string & version )
	:	DynLib(name, version),
		m_libraryName( name + "_" + version + getPlatformCCPostfix() + getConfigurationPostfix() + ".dll" ),
		m_handle( LoadLibrary(m_libraryName.c_str()) )
	{}

	~Win32Lib()
	{
		if( m_handle )
		{
			FreeLibrary(m_handle);
		}
	}

	operator const bool() const
	{
		return m_handle != 0;
	}
	
	void * getSymbol( const std::string & name ) const
	{
		return m_handle != 0 ? GetProcAddress(m_handle, name.c_str()) : 0;
	}

private:

	const std::string	m_libraryName;
	const HMODULE		m_handle;
};

#endif WIN32



	
Pluggable::Pluggable( boost::weak_ptr< Package > package, const std::string & name, const std::string & version )
:	Module(package, name, version),
	m_canBeUnloaded(true)
{
	namespace bpt = boost::property_tree;
	namespace bfs = boost::filesystem;

	const bfs::path	filename = getPathSafe(SharePath) / "module.xml";
	
	try
	{
		// Loads meta data from an xml file.
		bpt::read_xml( filename.string(), m_data );
	}
	catch( bpt::xml_parser_error & )
	{
		std::cerr << "Error while loading module meta data file " << filename << "." << std::endl;
	}
}


const std::string Pluggable::getDescription() const
{
	return m_data.get( "module.description", std::string() );
}


const std::string Pluggable::getLabel() const
{
	return m_data.get( "module.label", getName() );
}


const boost::property_tree::ptree Pluggable::getPayload( const std::string & name ) const
{
	namespace bpt = boost::property_tree;

	try
	{
		return m_data.get_child( "module.payload." + name );
	}
	catch( const bpt::ptree_bad_path & )
	{
		return bpt::ptree();
	}
}


const Pluggable::TagContainer Pluggable::getTags() const
{
	namespace		bpt = boost::property_tree;
	TagContainer	result;

	try
	{
		const bpt::ptree	& tags = m_data.get_child( "module.tags" );

		for( bpt::ptree::const_iterator i = tags.begin(); i != tags.end(); ++i )
		{
			result.push_back( i->second.get_value< std::string >() );
		}
	}
	catch( bpt::ptree_bad_path & )
	{}

	return result;
}


const std::string Pluggable::getTagsString() const
{
	namespace	bpt = boost::property_tree;
	std::string	result;

	try
	{
		const bpt::ptree	& tags = m_data.get_child( "module.tags" );

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




const bool Pluggable::hasTag( const std::string & tag ) const
{
	namespace	bpt = boost::property_tree;

	try
	{
		const bpt::ptree	& tags = m_data.get_child( "module.tags" );

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


const bool Pluggable::isLoaded() const
{
	return m_library;
}


bool Pluggable::hasUnloadingFunction()
{
	return m_library ? m_library->getSymbol("unload") != 0 : false;
}


void Pluggable::load()
{
	namespace bfs = boost::filesystem;
	
	// Skips loading if already done.
	if( m_library )
	{
		return;
	}

	// Builds the library name and do the effective module loading.
	boost::shared_ptr< DynLib >	library;

#ifdef WIN32
	library.reset( new Win32Lib(m_name, m_version) );
#endif
	
	// If the library exists and has been loaded
	if( library && (*library) )
	{
		// Registers the library.
		m_library.swap(library);

		// Starts the pluggable module initialization.
		void * loadFunAddr = m_library->getSymbol("load");

		if( loadFunAddr )
		{
			void (*loadFunPtr)(void) = reinterpret_cast< void (*)(void) >( loadFunAddr );

			loadFunPtr();
		}
	}
	else
	{
		std::cerr << "Error while loading dynamic library of the pluggable " << m_name << "_" << m_version << "." << std::endl;
	}
}


void Pluggable::unload()
{
	// If the library was loaded
	if( m_library )
	{
		void * unloadFunAddr = m_library->getSymbol("unload");

		if( unloadFunAddr )
		{
			void (*loadFunPtr)(void) = reinterpret_cast< void (*)(void) >( unloadFunAddr );

			loadFunPtr();

			// unregisters the library.
			m_library.reset();
		}		
	}
}


bool Pluggable::canBeUnloaded()
{
	return m_canBeUnloaded;
}


void Pluggable::blockUnloading()
{
	m_canBeUnloaded = false;
}


} // namespace pkg

} // namespace sbf
