// VGSDK - Copyright (C) 2004, 2008, 2011, Nicolas Papier.
// Distributed under the terms of the GNU Library General Public License (LGPL)
// as published by the Free Software Foundation.
// Author Nicolas Papier
// Author Guillaume Brocker

#include "sbf/GlobalLogger.hpp"

#include "sbf/Logging.hpp"



namespace sbf
{



ILogging& GlobalLogger::get()
{
	return ( *m_globalLogger );
}


void GlobalLogger::set( boost::shared_ptr< ILogging > logger )
{
	assert( logger );

	m_globalLogger = logger;
}


const bool GlobalLogger::isAssertEnabled()
{
	return m_assertEnabled;
}


void GlobalLogger::setAssertEnabled( const bool enabled )
{
	m_assertEnabled = enabled;
}


boost::shared_ptr< ILogging >	GlobalLogger::m_globalLogger( new Logging() );

bool							GlobalLogger::m_assertEnabled( true );


ILogging& get()
{
	return ( sbf::GlobalLogger::get() );
}


void set( boost::shared_ptr< ILogging > logger )
{
	sbf::GlobalLogger::set( logger );
}


const bool isAssertEnabled()
{
	return sbf::GlobalLogger::isAssertEnabled();
}


void setAssertEnabled( const bool enabled )
{
	sbf::GlobalLogger::setAssertEnabled( enabled );
}


} // namespace sbf
