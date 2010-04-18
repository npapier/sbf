# SConsBuildFramework - Copyright (C) 2010, Nicolas Papier.
# Distributed under the terms of the GNU General Public License (GPL)
# as published by the Free Software Foundation.
# Author Nicolas Papier

def askQuestion( question, choicesList ):
	"""The given question is written to standard output followed by a textual description of the available choices.
	The first choise in choicesList would be the default choice. The answer is returned as a string."""

	choicesText = ''
	selectors = []
	for choice in choicesList:
		selector = choice[0]
		selectors.append( selector )

		choiceText = '({0}){1}'.format( selector, choice[1:] )
		if len(choicesText) == 0:
			choicesText = choiceText.upper()
		else:
			choicesText += ', ' + choiceText

	defaultSelector = selectors[0]

	# Asks question
	while( True ):
		answer = raw_input('{0} ? {1} '.format( question, choicesText ))

		if len(answer)==0:
			answer = defaultSelector

		answer = answer.lower()

		if answer in selectors:
			break
	return answer