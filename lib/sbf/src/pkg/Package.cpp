#include "sbf/pkg/Package.hpp"

#include <algorithm>
#include <cassert>
#include <iostream>

#include <boost/filesystem/convenience.hpp>
#include <boost/filesystem/operations.hpp>

#ifdef WIN32
  #include <windows.h>
#endif // WIN32

#include "sbf/pkg/Module.hpp"
#include "sbf/pkg/Pluggable.hpp"


namespace sbf
{

namespace pkg
{

namespace
{

/**
 * @brief	Retrieves the root path of the main package.
 */
const boost::filesystem::path getRoot()
{
#ifdef WIN32
	
	char	filename[1024];

	GetModuleFileName( 0, filename, sizeof(filename) );
	return boost::filesystem::path(filename).parent_path().parent_path();

#else

	return boost::filesystem::initial_path();

#endif
}


/**
 * @brief	Extracts a package name and version from the given path.
 */
const std::pair< std::string, std::string > getPackageNameAndVersion( const boost::filesystem::path & path )
{
	const std::string				filename		= path.filename().string();
	const std::string::size_type	delimiterPos	= filename.find('_');
	std::string						name;
	std::string						version;

	if( delimiterPos != std::string::npos )
	{
		name	= filename.substr( 0, delimiterPos );
		version	= filename.substr( delimiterPos+1 );
	}

	return std::make_pair( name, version );
}


/**
 * @brief	A predicate telling if a module has the given name and version (this one being optional).
 */
struct module_has
{
	module_has( const std::string & name, const std::string & version ) : m_name(name), m_version( version )
	{}

	const bool operator() ( const boost::shared_ptr< Module > module ) const
	{
		return module->getName() == m_name && (m_version.empty() || module->getVersion() == m_version);
	}

	const std::string	m_name;
	const std::string	m_version;
};

}


Package::PackageContainer	Package::m_packages;


Package::Package( const std::string & name, const std::string & version, const boost::filesystem::path & path, const boost::weak_ptr< Package > parent )
:	m_name( name ),
	m_version( version ),
	m_path( path ),
	m_parent( parent )
{}


Package::const_iterator Package::begin()
{
	return m_packages.begin();
}


boost::shared_ptr< Package > Package::current()
{
	init();
	
	assert( m_packages.size() >= 1 );

	return m_packages.front();
}


Package::const_iterator Package::end()
{
	return m_packages.end();
}


const boost::shared_ptr< Module > Package::findModule( const std::string & name, const std::string & version ) const
{
	namespace bfs = boost::filesystem;

	// First, we search for a module already registered.
	// If none of the registered module matches the query, 
	// we search in the var sub-directory for a module that created ressource after startup,
	// and if all this fails, we cannot return a valid module.
	const_module_iterator		found = std::find_if( m_modules.begin(), m_modules.end(), module_has(name, version) );
	
	if( found != m_modules.end() )
	{
		return *found;
	}
	else
	{
		return const_cast< Package* >(this)->initModule( VarPath, name, version );
	}	
}


const boost::shared_ptr< Pluggable > Package::findPluggable( const std::string & name, const std::string & version ) const
{
	// We look for a registered pluggable module and returns it if found, or a null pointer otherwise.
	const_pluggable_iterator found = std::find_if( m_pluggables.begin(), m_pluggables.end(), module_has(name, version) );

	return found != m_pluggables.end() ? *found : boost::shared_ptr< Pluggable >();
}


const std::string & Package::getName() const
{
	return m_name;
}


const boost::shared_ptr< Package > Package::getParent() const
{
	return m_parent.lock();
}


const std::vector< std::string > Package::getPlugablesByTag( const std::string & tag ) const
{
	std::vector< std::string > result;

	for( ModuleContainer::const_iterator i = m_modules.begin(); i != m_modules.end(); ++i )
	{
		boost::shared_ptr< Module >		module		= *i;
		boost::shared_ptr< Pluggable >	plugable	= boost::dynamic_pointer_cast< Pluggable >( module );

		if( plugable && plugable->hasTag(tag) )
		{
			const std::string uniqueModuleName = module->getName() + "_" + module->getVersion();

			result.push_back( uniqueModuleName );
		}
	}
	return result;
}


const boost::filesystem::path & Package::getPath() const
{
	return m_path;
}


const boost::filesystem::path Package::getPath( const PathType & type ) const
{
	return m_path / toString(type);
}


const boost::filesystem::path Package::getPathSafe( const PathType & type ) const
{
	boost::filesystem::path	result = getPath(type);

	boost::filesystem::create_directories( result );
	return result;
}	


const std::string & Package::getVersion() const
{
	return m_version;
}


void Package::init()
{
	namespace bfs = boost::filesystem;

	// If the root package has been created,
	// then package collection contains at least one entry,
	// then skip processing further.
	if( m_packages.size() >= 1 )
	{
		return;
	}


	// Builds the root path used to initialize the system.
	const bfs::path	rootPath = getRoot();


	// Creates the root package representing the running application.
	// The root package is the first package in the collection.
	const boost::shared_ptr< Package >	rootPackage( new Package(std::string(), std::string(), rootPath) );
	m_packages.push_back( rootPackage );
	rootPackage->initModules(SharePath);
	rootPackage->initModules(VarPath);


	// Get's the path of the package repository
	// and walks the sub-directories to populate the package collection.
	const bfs::path	 repositoryPath = rootPath / "packages";

	if( bfs::is_directory(repositoryPath) )
	{
		bfs::directory_iterator	end;

		for( bfs::directory_iterator entry(repositoryPath); entry != end; ++entry )
		{
			// Skips the current entry if it is not a directory
			if( entry->status().type() != bfs::directory_file ) continue;

			// Collects various informations, 
			// creates a new package and adds it the collection.
			const bfs::path								path			= entry->path();
			const std::pair< std::string, std::string >	nameAndVersion	= getPackageNameAndVersion( path );
			const boost::shared_ptr< Package >			package( new Package(nameAndVersion.first, nameAndVersion.second, path, rootPackage) );
			
			m_packages.push_back( package );
			package->initModules( SharePath );
			package->initModules( VarPath );
		}
	}
}


void Package::initModules( const PathType & pathType )
{
	namespace bfs = boost::filesystem;

	const bfs::path			basePath = getPathSafe( pathType );

	std::string	moduleName;
	std::string	moduleVersion;
	
	for( bfs::recursive_directory_iterator i(basePath); i != bfs::recursive_directory_iterator(); ++i )
	{
		const bfs::directory_entry	entry( *i );
		const bfs::file_status		fileStatus( entry.status() );
		

		// At level 0, a directory corresponds to a module name,
		// so we simply stores the module name.
		if( fileStatus.type() == bfs::directory_file && i.level() == 0 )
		{
			moduleName = entry.path().filename().string();
		}
		// At level 1, a directory corresponds to a module version,
		// so we store the module version, stop recursing to avoid module's data
		// and we create the module instance.
		else if( fileStatus.type() == bfs::directory_file && i.level() == 1 )
		{
			moduleVersion = entry.path().filename().string();
			i.no_push();
			initModule( pathType, moduleName, moduleVersion );
			moduleName.clear();
			moduleVersion.clear();
		}
	}
}


const boost::shared_ptr< Module > Package::initModule( const PathType & pathType, const std::string & name, const std::string & version )
{
	namespace bfs = boost::filesystem;

	const_module_iterator		found		= std::find_if( m_modules.begin(), m_modules.end(), module_has(name, version) );
	const bfs::path				modulePath	= getPathSafe(pathType) / name / version;
	
	// If the module exists, then we return that instance.
	// Else if the module path is valid, we create an instance of module or pluggable.
	// Else if the module version has properly been specified, we create a module instance.
	if( found != m_modules.end() )
	{
		return *found;
	}
	else if( bfs::is_directory(modulePath) )
	{
		const bool	isPluggable = bfs::is_regular(modulePath/"module.xml");

		if( isPluggable )
		{
			const boost::shared_ptr< Pluggable>	pluggable( new Pluggable(shared_from_this(), name, version) );

			m_modules.push_back( pluggable );
			m_pluggables.push_back( pluggable );
			return pluggable;
		}
		else
		{
			boost::shared_ptr< Module >	module( new Module(shared_from_this(), name, version) );

			m_modules.push_back( module );
			return module;
		}
	}
	else if( !version.empty() )
	{
		boost::shared_ptr< Module >	module( new Module(shared_from_this(), name, version) );

		m_modules.push_back( module );
		return module;
	}
	else
	{
		return boost::shared_ptr< Module >();
	}
}


void Package::loadPlugablesByTag( const std::string & tag )
{
	for( ModuleContainer::iterator i = m_modules.begin(); i != m_modules.end(); ++i )
	{
		boost::shared_ptr< Module >		module = *i;
		boost::shared_ptr< Pluggable >	plugable = boost::dynamic_pointer_cast< Pluggable >( module );

		if( plugable && plugable->hasTag(tag) )
		{
			plugable->load();
			std::cout << "Loaded module " << plugable->getName() << " " << plugable->getVersion() << std::endl;

			// load by tag as of now is mandatorily loaded at application startup
			// hence the loaded module shouldn't be unloadable
			plugable->blockUnloading();
		}
	}
}


Package::module_iterator Package::moduleBegin()
{
	return m_modules.begin();
}


Package::const_module_iterator Package::moduleBegin() const
{
	return m_modules.begin();
}


const unsigned int Package::moduleCount() const
{
	return m_modules.size();
}


Package::module_iterator Package::moduleEnd()
{
	return m_modules.end();
}


Package::const_module_iterator Package::moduleEnd() const
{
	return m_modules.end();
}


Package::pluggable_iterator Package::pluggableBegin()
{
	return m_pluggables.begin();
}


Package::const_pluggable_iterator Package::pluggableBegin() const
{
	return m_pluggables.begin();
}


const unsigned int Package::pluggableCount() const
{
	return m_pluggables.size();
}


Package::pluggable_iterator Package::pluggableEnd()
{
	return m_pluggables.end();
}


Package::const_pluggable_iterator Package::pluggableEnd() const
{
	return m_pluggables.end();
}


} // namespace pkg

} // namespace sbf