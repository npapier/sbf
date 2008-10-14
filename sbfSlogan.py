#! /usr/bin/python

# SConsBuildFramework - Copyright (C) 2008, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Guillaume Brocker

import optparse
import os
import pysvn
import re
import sys


# Files extension classifications.
sourceFileExtensions  = set(['.h', '.hxx', '.hpp', '.c', '.cpp'])
ignoreFileExtensions  = set(['.sys', '.rc', '.pch', '.res', '.jpg', '.png', '.aps', '.txt', '.list', '.dll', '.trian2', '.zip', '.targets', '.inf', '.htm', '.trian', '.scc', '.exe', '.lib', '.vspscc', '.bit', '.avi', '.bmp', '.options', '.vcproj', '.ico', '.wav', '.suo', '.lnk', '.position', '.sln', '.scons1908'])
unknownFileExtensions = set()


# Source code analysis patterns.
anyPattern               = re.compile("^(.*?)$")
blankPattern             = re.compile("^(\\s*)$")
blockCommentStartPattern = re.compile("^\\s*(/\\*.*)$")
blockCommentEndPattern   = re.compile("^(.*?\\*/.*)$")
codePattern              = re.compile("^\\s*(\\S+.*?)$")
lineCommentPattern       = re.compile("^\\s*(//.*)$")


newLinePattern = re.compile("^-[^\\-].*$")
oldLinePattern = re.compile("^\\+[^\\+].*$")



# Counts the file content changes
def getFileChanges( svnClient, svnUrl, svnRevision ) :
	return getFileChanges2( svnClient, svnUrl, svnRevision, pysvn.Revision(pysvn.opt_revision_kind.number, svnRevision.number-1) )
	

def getFileChanges2( svnClient, svnUrl, svnRevision, otherSvnRevision ) :
	linesAdded = 0
	linesModified = 0
	linesDeleted = 0
	
	if isUrlSourceFile( svnUrl ) :
		diffLog = svnClient.diff('.', svnUrl, svnRevision, svnUrl, otherSvnRevision )
		
		inNew = 0
		
		for line in diffLog.splitlines() :
			if newLinePattern.match( line ) :
				inNew += 1
			elif oldLinePattern.match( line ) :
				if inNew > 0 :
					inNew -= 1
					linesModified += 1
				else :
					linesDeleted += 1
			else :
				linesAdded += inNew
				inNew = 0
		
		linesAdded += inNew
			
	return (linesAdded, linesModified, linesDeleted)
	

# Retrieves the number of source code lines for the file at the given url and revision.
# The function returns a tuple in the form (blank, comment, code).
def getFileLocs( svnClient, svnUrl, svnRevision ):
	anyLines			= 0
	blankLines			= 0
	commentLines		= 0
	codeLines			= 0	
	
	if isUrlSourceFile(svnUrl) :
		# Get fone content.
		content = svnClient.cat( svnUrl, svnRevision )
		
		# Walks lines to analyse the content of the file
		inBlockComment = False
		for line in content.splitlines() :
			anyLines += 1
			
			if inBlockComment :
				#print "CM " + line
				commentLines += 1
				if blockCommentEndPattern.match(line) :
					inBlockComment = False
			elif blankPattern.match(line) :
				#print "BL " + line
				blankLines += 1
			elif blockCommentStartPattern.match(line) :
				#print "CM " + line
				inBlockComment = True
				commentLines += 1
			elif codePattern.match(line) :
				#print "CO " + line
				codeLines += 1
			elif lineCommentPattern.match(line) :
				#print "CM " + line
				commentLines += 1
			else :
				print "Encountered unknown line of code"
				
		
	return (anyLines, blankLines, commentLines, codeLines)
	
	
def isUrlExcluded( svnURL ) :
	if not options.excludes :
		return False
		
	for exclude in options.excludes :
		if svnURL.find(exclude) != -1 :
			return True
	
	return False
	
	
	
# Tells if the given url points to a recognized source file
def isUrlSourceFile( svnUrl ) :
	(root, extension)	= os.path.splitext(svnUrl)
	
	if extension in sourceFileExtensions :
		return True
	elif extension in ignoreFileExtensions :
		return False
	elif extension :
		unknownFileExtensions.add( extension )
		return False


# Get command line options and parameters.
optionParser = optparse.OptionParser()

optionParser.add_option( "-d", "--delta", action="store_true", dest="delta", help="Show some delta information between the first and last revision, instead of parsing the log." )
optionParser.add_option( "-e", "--exclude", action="append", type="string", dest="excludes", help="Exclude an URL from analysis." )
optionParser.add_option( "-r", "--start-rev", action="store", type="int", dest="startRev", help="Tells the revision number that marks the starts of the statistics." )
optionParser.add_option( "-o", "--output", action="store", type="string", dest="output", default="stats.csv", help="Gives the path of the output CVS file (stats.cvs by default)." )
(options, args) = optionParser.parse_args()


# Retrieves the repository url.
if len(args) >= 1 :
	url = args[0]
else :
	url = None


# Creates the pysvn client.
client = pysvn.Client()


# Ensures that a valid svn url has been given
if not url :
	print 'Required svn repository URL missing!'
	sys.exit(-1)
elif not client.is_url(url) :
	print '%s: invalid svn repository url.' % url
	sys.exit(-1)

	
# Gathers the svn log, from head to the given revision.
if options.startRev :
	startRevision = pysvn.Revision(pysvn.opt_revision_kind.number, options.startRev)
else :
	startRevision = pysvn.Revision(pysvn.opt_revision_kind.number, 1)
print("Gathering log.")
log = client.log(url, revision_end=startRevision, discover_changed_paths=True, strict_node_history=False)


# Performs the delta between the first and the last release
if options.delta :
	revisionOne = startRevision
	revisionTwo = pysvn.Revision(pysvn.opt_revision_kind.head)
	
	# Retrieves the node infos for the first and the last revision.
	nodeInfosOne = client.info2( url, revision=revisionOne, depth=pysvn.depth.infinity )
	nodeInfosTwo = client.info2( url, revision=revisionTwo, depth=pysvn.depth.infinity )
	
	# Collects initial URLs
	locsCacheOne	= dict()
	filesOne		= 0
	locsOne			= 0
	for (path, info) in nodeInfosOne :
		if info.kind != pysvn.node_kind.file :
			continue
			
		if not isUrlSourceFile(info.URL) :
			continue
			
		if isUrlExcluded(info.URL) :
			continue
			
		(anyLines, blankLines, commentLines, codeLines) = getFileLocs( client, info.URL, revisionOne )
		
		filesOne += 1
		locsOne  += commentLines + codeLines
		locsCacheOne[info.URL] = commentLines + codeLines
		
		
	# Walks the last node infos to make the delta.
	files = 0
	filesAdded = 0
	filesModified = 0
	filesDeleted = 0
	filesUntouched = 0
	locs = 0
	locsAdded = 0
	locsModified = 0
	locsDeleted = 0
	for (path, info) in nodeInfosTwo :
		if info.kind != pysvn.node_kind.file :
			continue
			
		if not isUrlSourceFile(info.URL) :
			continue
			
		if isUrlExcluded(info.URL) :
			continue
		
		files += 1
		(anyLines, blankLines, commentLines, codeLines) = getFileLocs( client, info.URL, revisionTwo )
		locs += commentLines + codeLines
		
		if info.URL in locsCacheOne.keys() :
			del( locsCacheOne[info.URL] )
			(fileLocsAdded, fileLocsModified, fileLocsDeleted) = getFileChanges2( client, info.URL, revisionTwo, revisionOne )
			if fileLocsAdded == 0 and fileLocsModified == 0 and fileLocsDeleted == 0:
				filesUntouched += 1
			else :
				filesModified += 1
				locsAdded += fileLocsAdded
				locsModified += fileLocsModified
				locsDeleted += fileLocsDeleted
		else :
			filesAdded += 1
			locsAdded += commentLines + codeLines

	for deleteUrl in locsCacheOne.keys() :
		filesDeleted += 1
		locsDeleted += locsCacheOne[deleteUrl]
	

	print "Initial Revision:"
	print "Files           %i" % filesOne
	print "Locs            %i" % locsOne
	print
	print "Final Revision:"
	print "Files           %i" % files
	print "Files Added     %i" % filesAdded
	print "Files Modified  %i" % filesModified
	print "Files Deleted   %i" % filesDeleted
	print "Files Untouched %i" % filesUntouched
	print "Locs            %i" % locs
	print "Locs Added      %i" % locsAdded
	print "Locs Modified   %i" % locsModified
	print "Locs Deleted    %i" % locsDeleted
	sys.exit(0)


# Creates the output file
print "Creating output file '%s'." % options.output
output = open(options.output, 'w+')
output.write("revision, dirs, files, files - added, files - modified, files - deleted, loc, loc - added, loc - modified, loc - deleted, loc - blank, loc - comment, loc - code\n")


# Creates the file loc cache, index by url.
class FileLocs :
	def __init__(self, lastChangedDate, locs, blankLocs, commentLocs, codeLocs) :
		self.lastChangedDate	= lastChangedDate
		self.locs				= locs
		self.blankLocs			= blankLocs
		self.commentLocs		= commentLocs
		self.codeLocs			= codeLocs

fileLocCache = dict()


# Walks this log in reverse oder (from oldest to the newest).
logItemSeen = 0.0
for logItem in reversed(log) :
	# Builds a message
	logItemSeen += 1.0
	sys.stdout.write( 'Processing revision %i - %i%% (%i/%i)' % (logItem.revision.number, logItemSeen/len(log)*100, logItemSeen, len(log)) )
	sys.stdout.flush()
		
	# Gathers all nodes information for the current revision
	nodeInfos = client.info2( url, revision=logItem.revision, depth=pysvn.depth.infinity )
	
	# Process nodes.
	files		= 0
	dirs		= 0
	locs		= 0
	locBlanks	= 0
	locComments	= 0
	locCodes	= 0
	for (path,info) in nodeInfos :
		# Ensures the current item's URL is not be excluded
		if isUrlExcluded(info.URL) :
			continue
		
		# The node is a file
		if info.kind == pysvn.node_kind.file and isUrlSourceFile(info.URL):
			files += 1
			if info.URL not in fileLocCache.keys() or (fileLocCache[info.URL].lastChangedDate < info.last_changed_date) :
				fileLocs = getFileLocs(client, info.URL, logItem.revision)
				fileLocCache[info.URL] = FileLocs(info.last_changed_date, fileLocs[0], fileLocs[1], fileLocs[2], fileLocs[3])
			locs		+= fileLocCache[info.URL].locs
			locBlanks	+= fileLocCache[info.URL].blankLocs
			locComments	+= fileLocCache[info.URL].commentLocs
			locCodes	+= fileLocCache[info.URL].codeLocs
		# The node is a directory
		elif info.kind == pysvn.node_kind.dir :
			dirs  += 1
		
		# Prints an output message
		sys.stdout.write('.')
		sys.stdout.flush()
	
	# Process changed paths for the current log item.
	filesAdded		= 0
	filesModified	= 0
	filesDeleted	= 0
	locAdded		= 0
	locModified		= 0
	locDeleted		= 0
	rootUrl			= client.root_url_from_path(url)
	for changedPath in logItem.changed_paths :
		changedUrl = rootUrl + changedPath.path
		if changedUrl in fileLocCache.keys() and not changedPath.copyfrom_path :
			if changedPath.action == 'A' :
				filesAdded += 1
				locAdded += fileLocCache[ changedUrl ].locs
			elif changedPath.action == 'M' :
				filesModified += 1
				(fileLocAdded, fileLocModified, fileLocDeleted) = getFileChanges(client, changedUrl, logItem.revision)
				locAdded += fileLocAdded
				locModified += fileLocModified
				locDeleted += fileLocDeleted			
			elif changedPath.action == 'D' :
				locDeleted += fileLocCache[ changedUrl ].locs
				filesDeleted += 1
				
		# Prints an output message
		sys.stdout.write('.')
		sys.stdout.flush()
	
	# Writes the node number for the current revision.
	output.write( "%i, %i, %i, %i, %i, %i, %i, %i, %i, %i, %i, %i, %i\n" % (logItem.revision.number, dirs, files, filesAdded, filesModified, filesDeleted, locs, locAdded, locModified, locDeleted, locBlanks, locComments, locCodes) )
	output.flush()
	
	# Print an output message.
	sys.stdout.write('\n')
	sys.stdout.flush()
	

# Closes the output file.
print "Saving statistics."
output.close();


# Prints unknown file extensions.
if len(unknownFileExtensions) > 0 :
	print
	print "Unknown file extensions:%s" % ' '.join(unknownFileExtensions)