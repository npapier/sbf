# SConsBuildFramework - Copyright (C) 2009, 2010, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

import SCons.Script

class IVersionControlSystem :
	"""Interface to version control system"""

	def __init__( self ):
		pass

	def add( self, myProjectPathName, myProject ):
		raise SCons.Errors.UserError("'add' operation is not available in the version control system.")

	def checkout( self, myProjectPathName, myProject ):
		raise SCons.Errors.UserError("'checkout' operation is not available in the version control system.")

	def export( self ):
		raise SCons.Errors.UserError("'export' operation is not available in the version control system.")

	def clean( self, myProjectPathName, myProject ):
		raise SCons.Errors.UserError("'clean' operation is not available in the version control system.")

	def status( self, myProjectPathName, myProject ):
		raise SCons.Errors.UserError("'status' operation is not available in the version control system.")

	def update( self, myProjectPathName, myProject ):
		raise SCons.Errors.UserError("'update' operation is not available in the version control system.")

	def getUrl( self, path ):
		raise SCons.Errors.UserError("'getUrl' method is not available in the version control system.")	

