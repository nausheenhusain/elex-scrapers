##
## Kendall scraper, election 2020
## This is written in Python3.
##
## Assumptions: 
## - vote total is the first number on a given row
## - race name we want is "COUNTY BOARD MEMBER-DIST.1"
## - race name we want is "COUNTY BOARD MEMBER-DIST.2"
## - precincts_reporting can be turned into an int

from bs4 import BeautifulSoup
from datetime import datetime, timezone
import json
import probablepeople as pp
import re
import requests
from scrapers.utils.scraper_helper import get_name, initialize_race_obj
import urllib.request
import urllib.parse

def get_candidate_info(row):
	cand_info = re.split(r"\s{2,}", row)
	raw = cand_info[0].split('(')
	cand_name = raw[0]
	full_name = pp.parse(cand_name, 'person')
	cand_party = raw[1][:3]

	return cand_info, full_name, cand_party

def parse_name(fullname):
	first, middle, last = "","",""
	return get_name(fullname,first,middle,last)
	print(first,middle,last)

def get_vote_count(candinfo):
	# iterate through candidate info array
	# the first time an element e is a digit
	# return it (this also exits the loop)
	# won't work if vote total is not the first number in the row candinfo
	new_candinfo = candinfo[2:]
	for i,e in enumerate(new_candinfo):
		if e != ".":
			votes = int(e.replace(',', ''))
			return votes

def get_candidates_in_race_obj(first, middle, last, votes, party, index):
	return {
		"first_name": first,
		"middle_name": middle,
		"last_name": last,
		"vote_count": int(votes),
		"party": party,
		"ballot_order": int(index)
	}

def scrape_kendall():
	COUNTY_NAME = "Kendall"
	# sets URLs
	KENDALL_RACE_URL = 'https://results.co.kendall.il.us/'
	
	#gets data
	html = urllib.request.urlopen(KENDALL_RACE_URL).read()
	soup = BeautifulSoup(html, 'html.parser')
	# print(soup)

	# creates empty list for results info
	kendall_county_results = []

	data = soup.find('pre').text
	precincts_total = 87
	rows = data.splitlines()
	# print(rows)

	for index, row in enumerate(rows):
		if row.startswith(" PRECINCTS"):
			precincts_reporting = int(row[-2:])


		if row == "COUNTY BOARD MEMBER-DIST.1":
			dist1_race_name = row

			dist1_race_obj = initialize_race_obj(dist1_race_name,precincts_reporting,precincts_total,COUNTY_NAME)

		if index >= 115 and index <= 119: # will need to double-check this every once in a while, hard-coded
			cand_index = int(str(index)[-1:]) - 2
			cand_info, full_name, party = get_candidate_info(row)
				
			first_name, middle_name, last_name = parse_name(full_name)

			# votes = 99
			votes = get_vote_count(cand_info)
			
			formatted_candidate_info = get_candidates_in_race_obj( 
				first_name, middle_name, last_name, 
				votes, party, cand_index)

			dist1_race_obj["reporting_units"][0]['candidates'].append(formatted_candidate_info)

		if row == "COUNTY BOARD MEMBER-DIST.2":
			dist2_race_name = row

			dist2_race_obj = initialize_race_obj(dist2_race_name,precincts_reporting,precincts_total,COUNTY_NAME)

		if index >= 124 and index <= 129: # will need to double-check this every once in a while, hard-coded
			cand_index = int(str(index)[-1:]) - 1
			cand_info, full_name, party = get_candidate_info(row)
				
			first_name, middle_name, last_name = parse_name(full_name)
			votes = get_vote_count(cand_info)
			
			formatted_candidate_info = get_candidates_in_race_obj( 
				first_name, middle_name, last_name, 
				votes, party, cand_index)

			dist2_race_obj["reporting_units"][0]['candidates'].append(formatted_candidate_info)

	kendall_county_results.append(dist1_race_obj)
	kendall_county_results.append(dist2_race_obj)

	with open('scrapers/kendall_data.json', 'w', encoding='utf-8') as f:
		json.dump(kendall_county_results, f, ensure_ascii=False, indent=4)

	return kendall_county_results

# this should be commented out when running the app
# leave it in if you're just testing the scraper
# scrape_kendall()