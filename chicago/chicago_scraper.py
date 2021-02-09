##
## City Of Chicago scraper, election 2020
## This is written in Python 3
##
# 1-4 contest code (4 chars)
# 5- 7 candidate number (3 chars)
# 8- 11 eligible precincts (4 chars)
# 12-18 - votes (7 chars)
# 19-22 completed precincts (4 chars)
## Made-up example:
## 0068001006100020400000
## 	0068 001   0061        0,0, 0, 2, 0, 4,0              0,0,0,0
##  0123 456   78910     11,12,13,14,15,16,17         18,19,20,21
##  race can  prectotal         votes                  reported prec
## Python slicing works:
## [start:end] -- this goes from start to end -1


import csv
from datetime import datetime, timezone
import json
import probablepeople as pp
import re
import requests

def initialize_race_obj(name,reporting,total):
	race_obj = {
		"name": name.title(),
		"description": "",
		"election_date": "2020-11-03",
		"market": "chinews",
		"uncontested": False,
		"amendment": bool(False),
		"state_postal": "IL",
		"recount": False,
		"reporting_units": [
			{
				"name": "Chicago",
				"level": "city",
				"district_type": "",
				"state_postal": "IL",
				"geo_id": "",
				"electoral_vote_total": 0,
				"precincts_reporting": int(reporting),
				"total_precincts": int(total),
				"data_source_update_time": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S%z'),
				"candidates": []
			}
		]
	}
	return race_obj	

def parse_name(fullname):
	first, middle, last = "","",""
	return get_name(fullname,first,middle,last)

def get_name(full_name, first, middle, last):
	if len(full_name) == 1:
		first = ""
		middle = ""
		last = full_name[0][0]
	elif len(full_name) == 2:
		first = full_name[0][0]
		middle = ""
		last = full_name[1][0]
	elif len(full_name) == 3:
		first = full_name[0][0]
		middle = full_name[1][0]
		last = full_name[2][0]
	elif len(full_name) == 4:
		first = full_name[0][0]
		middle = full_name[1][0]
		last = full_name[2][0]+" "+full_name[3][0]
	return first, middle, last
	
def scrape_chicago():
	
	## This scraper loops through the results txt data and matches only with data from chicago-IDs.csv. 
	## It only adds in the race_obj if the race name doesn't exist in `added`,
	## which starts as an empty list. Within that for loop exists another for+if loop that loops through the
	## `chicago_results` list and adds the current race's candidate info.

	# TODO: REPLACE THIS WITH THE REAL URL ON ELECTION NIGHT
	txt_download =  'https://chicagoelections.gov/ap/summary.txt'
	r = requests.get(txt_download)
	with open('scrapers/chicago_files/chicago-results.txt', 'wb') as f:
		f.write(r.content)

	chicago_results = []
	added = []

	# CONTEXT SHEET - this info not provided during election night
	with open('scrapers/chicago_files/chicago-IDs.csv', newline='') as f:
		reader = csv.reader(f)
		chicago_info = list(reader)

	with open('scrapers/chicago_files/chicago-results.txt','r') as r: # created from chicago-zeroes-full.txt
		results_data = r.readlines()
	
	# This matches results races to dict races by the first seven characters of the record.
	for results_row in results_data:
		current_ID_match = results_row[0:7] #RESULTS

		for info_line in chicago_info:
			context_ID_match = info_line[0][0:7] #CONTEXT
			
			if current_ID_match == context_ID_match:
	
				context_ID = info_line[0]
				race_name = info_line[1].title()
				
				candidate = info_line[2]
				full_name = pp.parse(candidate, 'person') # uses probablepeople to parse names into a list
				first_name, middle_name, last_name = parse_name(full_name)
				
				total_precincts = int(results_row[7:11])

				vote_count = int(results_row[11:18])

				precincts_reporting = int(results_row[18:22])

				if context_ID[22:25] == "DEM" or context_ID[22:25] == "REP" or context_ID[22:25] == "NON":
					cand_party = context_ID[22:25]
					amendment = "False"
				else:
					cand_party = ""
					amendment = "True"
		
				ballot_order = int(info_line[0][4:7])
				
				if race_name not in added:
					race_obj = initialize_race_obj(race_name,precincts_reporting,total_precincts)

					chicago_results.append(race_obj)
					added.append(race_name)
				else:
					pass

				for item in chicago_results:
					if item['name'] == race_name.title():
						item['reporting_units'][0]['candidates'].append({
						"first_name": first_name,
						"middle_name": middle_name,
						"last_name": last_name,
						"vote_count": int(vote_count),
						"party": cand_party,
						"ballot_order": int(ballot_order)
					})
					else:
						pass
			else:
				pass
	
	with open('scrapers/chicago_files/chicago_data.json', 'w', encoding='utf-8') as f:
		json.dump(chicago_results, f, ensure_ascii=False, indent=4)

	return chicago_results

# this should be commented out when running the app
# leave it in if you're just testing the scraper
# scrape_chicago()