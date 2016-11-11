# HTML parser for sending/receiving noun associations
# for figuring out how to use items.

import subprocess

# Queries a word to the website. Returns a list of verbs associated with
# that noun.
def query_word(noun):

	# First, curl the website for the noun
	subprocess.call(["curl", 
		"https://wordassociations.net/en/words-associated-with/" + noun + "?start=0", "-o",
			"curl-output.txt"])

	# Open up the file
	with open("curl-output.txt", 'r') as f: 

		# Splice this thing up. First, cut out everything prior to the verb section.
		# then, cut everything after the end of the verb section. We do this by looking
		# for a social media token that always appear after all of the word outputs.
		# Verbs are last, so this makes our job relatively simple.
		html = f.read()
		ind1 = html.find("VERB-SECTION")
		ind2 = html.find("b-social-share__icon")
		verb_html = html[ind1:ind2]

		# Now, we split on href and filter out some more crap by dropping the first 
		# and last elements.
		splice1 = verb_html.split("href")
		verb_splice = splice1[1: len(splice1)-1] 

		# We now are very close to what we want. We splice each element again,
		# producing the final list based on the length of href and the location
		# of the token </a>.
		i = 0
		verbs = []
		for v in verb_splice:
			ind1 = verb_splice[i].find("-with/") + 6
			ind2 = verb_splice[i].find(">")
			verbs.append((verb_splice[i])[ind1:ind2].strip('"'))
			i+=1
			
	return verbs

		


