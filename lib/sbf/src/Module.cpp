// SConsBuildFramework - Copyright (C) 2009, Guillaume Brocker.
// Distributed under the terms of the GNU General Public License (GPL)
// as published by the Free Software Foundation.
// Author Guillaume Brocker

#include "sbf/Module.hpp"



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



const std::string Module::toString( const PathType type )
{
	switch( type )
	{
	case Share:	return "share";
	case Var:	return "var";
	default:	return "";
	}
}



} // namespace sbf
