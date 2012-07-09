# SConsBuildFramework - Copyright (C) 2010, 2012, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

import re

def askQuestion( question, choicesList, queryUser = True ):
	"""The given question is written to standard output followed by a textual description of the available choices.
	The first choise in choicesList would be the default choice. Shortcut for a choice is given by letter(s) between opening and closing brackets in the choice string.
	The answer is returned as a string containing the choice string without brackets.
	If queryUser parameter is False, then question is not asked and the default choice is returned
	@remark returned string is always in lower case"""

	def normalizeAnswer( answer ):
		return choicesListWithoutBrackets[ selectors.index(answer) ].lower()

	selectors = [] # selectors contains the shortcut of each element of the choicesList
	choicesListWithoutBrackets = []
	choicesText = ''

	reSelector = re.compile(r"^\w*[(]([a-zA-Z0-9]+)[)]\w*")
	for choice in choicesList:

		# Extract selector
		selectorMatch = reSelector.match(choice)
		if selectorMatch:
			selector = selectorMatch.group(1)
		else:
			selector = choice

		# Append new choice informations
		selectors.append( selector )
		choicesListWithoutBrackets.append( choice.replace('(','').replace(')','') )

		if len(choicesText) == 0:
			choicesText = choice
		else:
			choicesText += ', ' + choice

	# Default selector
	defaultSelector = selectors[0]

	# Don't ask question
	if not queryUser:
		return normalizeAnswer(defaultSelector)

	# Asks question
	while( True ):
		answer = raw_input('{0} ?\n {1} ?'.format( question, choicesText ))

		if len(answer)==0:
			answer = defaultSelector
		elif answer in choicesListWithoutBrackets:
			answer = selectors[choicesListWithoutBrackets.index(answer)]

		if answer in selectors:
			break

	return normalizeAnswer(answer)


def ask( question, defaultValue, queryUser = True ):
	"""The given question is written to standard output followed by the default value (must be defined).
	The answer is returned as a string.
	If queryUser parameter is False, then question is not asked and the default choice is returned."""

	# Checks precondition
	if len(defaultValue)==0:
		raise AssertionError('Empty default value is not allowed.')

	# Don't ask question
	if not queryUser:
		return defaultValue

	# Asks question
	while( True ):
		answer = raw_input( '{0} (default={1}) ? '.format(question, defaultValue) )

		if len(answer)==0:
			answer = defaultValue

		if len(answer)!=0:
			break

	return answer

