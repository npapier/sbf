# SConsBuildFramework - Copyright (C) 2009, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

# Interface to version control system
class IVersionControlSystem :
	def __init__( self ):
		raise StandardError("IVersionControlSystem::__init__() not implemented")

	def add( self ):
		raise StandardError("IVersionControlSystem::add() not implemented")

	def checkout( self ):
		raise StandardError("IVersionControlSystem::checkout() not implemented")

	def clean( self ):
		raise StandardError("IVersionControlSystem::clean() not implemented")

	def status( self ):
		raise StandardError("IVersionControlSystem::status() not implemented")

	def update( self ):
		raise StandardError("IVersionControlSystem::update() not implemented")
