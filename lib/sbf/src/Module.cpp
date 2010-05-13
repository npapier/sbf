// SConsBuildFramework - Copyright (C) 2009, 2010, Guillaume Brocker.
// Distributed under the terms of the GNU General Public License (GPL)
// as published by the Free Software Foundation.
// Author Guillaume Brocker

#include "sbf/Module.hpp"

#include <fstream>
#include <iostream>
#include <boost/filesystem.hpp>

#include "sbf/path.hpp"



namespace sbf
{


	
Module::Container	Module::m_registry;



Module::ConstIterator Module::begin()
{
	return m_registry.begin();
}



Module::ConstIterator Module::end()
{
	return m_registry.end();
}



const bool Module::hasInfoFile() const
{
	const boost::filesystem::path	infoPath = sbf::path::get(sbf::path::Share, *this) / "info.sbf";

	return boost::filesystem::exists( infoPath );
}



const std::string Module::getInfoFromFile() const
{
	const boost::filesystem::path	infoPath = sbf::path::get(sbf::path::Share, *this) / "info.sbf";
	std::string						buffer;

	if( boost::filesystem::exists( infoPath ) )
	{
		std::ifstream	in( infoPath.file_string().c_str() );

		while( in )
		{
			std::string	line;

			std::getline( in, line );
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


	
const Module & Module::get( const std::string & name )
{
	// Searchs for a registered module.
	for( ConstIterator i = m_registry.begin(); i != m_registry.end(); ++i )
	{
		if( (*i)->m_name == name )
		{
			return *(*i);
		}
	}
	
	
	// Or returns the invalid module.
	static Module	invalid("","");
	
	return invalid;
}



Module::Module( const std::string & name, const std::string & version )
:	m_name( name ),
	m_version( version )
{
	const Module & found = get(m_name);

	if( ! found )
	{
		m_registry.push_back(this);
	}
}



Module::~Module()
{
	Container::iterator	found = std::find(m_registry.begin(), m_registry.end(), this);

	if( found != m_registry.end() )
	{
		m_registry.erase( found );
	}
}



const std::string Module::getName() const
{
	return m_name;
}



const std::string Module::getVersion() const
{
	return m_version;
}



Module::operator const bool () const
{
	return m_name.empty() == false && m_version.empty() == false;
}



} // namespace sbf
