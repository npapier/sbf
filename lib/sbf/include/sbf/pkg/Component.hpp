#ifndef _SBF_PKG_COMPONENT_HPP_
#define _SBF_PKG_COMPONENT_HPP_

#include <string>

#include <boost/filesystem/path.hpp>
#include <boost/property_tree/ptree.hpp>
#include <boost/shared_ptr.hpp>
#include <boost/weak_ptr.hpp>

#include "sbf/sbf.hpp"
#include "sbf/pkg/types.hpp"


namespace sbf
{

namespace pkg
{


struct Package;


/**
 * @brief	Base class for components of the system of packages and modules.
 */
struct Component
{
	typedef std::vector< std::string >	TagContainer;

	/**
	 * @name Properties
	 */
	//@{
	SBF_API const std::string getDescription() const;		///< Retrieves the module description text.
	SBF_API const std::string getLabel() const;				///< Retrieves the module label.
	SBF_API const std::string getName() const;			///< Retrieves the name of the package.
	SBF_API const std::string getNameAndVersion() const;	///< Retrieves the name and version string of the package.
	SBF_API const TagContainer getTags() const;				///< Retrieves the module tags.
	SBF_API const std::string getTagsString() const;		///< Retrieves the module tags in a string.
	SBF_API const boost::shared_ptr< Package > getParent() const;						///< Retrieves the parent package (returns null if none).
	SBF_API const boost::filesystem::path getPath( const PathType & type ) const;		///< Retrieves the path owned by the component for the given type.
	SBF_API const boost::filesystem::path getPathSafe( const PathType & type ) const;	///< Retrieves the path owned by the component for the given type and ensures that the path exists.
	SBF_API const boost::filesystem::path getRootPath() const;	///< Retrieves the root path for the component.
	SBF_API const std::string & getVersion() const;				///< Retrieves the version of the package.
	SBF_API const bool hasTag( const std::string & tag ) const;	///< Tells if the module has the given tag.
	//@}

	/**
	 * @name Data access
	 */
	//@{
	SBF_API const boost::property_tree::ptree getDataAsTree( const std::string & key ) const;	///< Retrieves a data tree for the given key.
	SBF_API const std::string getDataAsString( const std::string & key ) const;					///< Retrieves a data string for the given key.
	SBF_API void setData( const std::string & key, const std::string & value );					///< Set a string in the data for the given key.
	SBF_API const bool hasMetaData() const;														///< Tells if the component has loaded a meta data file.
	//@}

protected:

	const std::string					m_name;			///< The component's name.
	const std::string					m_version;		///< The component's version.
	const boost::filesystem::path		m_rootPath;		///< The component root's path.
	const boost::weak_ptr< Package >	m_parent;		///< The component's parent.
	const boost::property_tree::ptree	m_constData;	///< Holds the component's constant meta data.
	boost::property_tree::ptree			m_editableData;	///< Holds the component's editable meta data.

	/**
	 * @brief	Constructor
	 */
	Component(
		const std::string & name,
		const std::string & version,
		const boost::filesystem::path & rootPath,
		const boost::weak_ptr< Package > parent = boost::weak_ptr< Package >() );

	/**
	 * @name Helpers
	 */
	//@{
	void loadData();		///< Loads constant and editable data.
	void saveData() const;	///< Saves editable data.
	//@}
};


} // namespace pkg

} // namespace sbf


#endif // _SBF_PKG_COMPONENT_HPP_
