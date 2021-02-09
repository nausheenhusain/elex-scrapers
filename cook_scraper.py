##
## Cook scraper, election 2020
## This is written in Python3.

# 0 race id (4 chars)
# 4 candidate id (3 chars)
# 7 precinct total (4 chars)
# 11 votes (7 chars)
# 18 completed precincts (4 chars)

## Made-up example:
## 0068001006100020400000
## 	0068 001   0061        0,0, 0, 2, 0, 4,0              0,0,0,0
##  0123 456   78910     11,12,13,14,15,16,17           18,19,20,21
##  race can   total            votes                  reported prec


import csv
from datetime import datetime, timezone
from ftplib import FTP_TLS
import json
import probablepeople as pp
import re
from urllib.request import urlopen

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

# gets relevant file from FTP server
def get_txtfile():

	ftps = FTP_TLS("ftps.cookcountyclerk.com")
	ftps.login(user='reporters',passwd='R3p047')
	ftps.prot_p()
	ftps.getwelcome()
	ftps.dir()
	print('getting new txt file')
	with open('scrapers/cook_files/updated_cook.txt', 'wb') as new_results: # this should create a new file called updated_cook.txt
		ftps.retrbinary('RETR ' + 'SummaryExport.txt', new_results.write) # confirm the name of the file that will have updated results
	print('exiting server')
	ftps.quit()

def scrape_cook():
	
	## This scraper loops through the results txt data and matches only with data from cook-IDs.csv. 
	## It only adds in the race_obj if the race name doesn't exist in `added`,
	## which starts as an empty list. Within that for loop exists another for+if loop that loops through the
	## `cook_county_results` list and adds the current race's candidate info.

	get_txtfile()

	cook_county_results = []
	added = []

	with open('scrapers/cook_files/cook-IDs.csv', newline='') as f:
		reader = csv.reader(f)
		cook_info = list(reader)
	with open('scrapers/cook_files/updated_cook.txt','r') as r: # should be name of newly-written file
		results_data = r.readlines()

	# This matches results races to dict races by the first seven characters of the record.
	for results_row in results_data:
		current_ID_match = results_row[0:7] #RESULTS
		for info_line in cook_info:
			full_ID_match = info_line[0][0:7] #CONTEXT
			
			if current_ID_match == full_ID_match:
				
				full_ID = info_line[0]
				race_name = info_line[1].title()
				candidate = info_line[2]
				full_name = pp.parse(candidate, 'person') # uses probablepeople to parse names into a list
				
				first_name, middle_name, last_name = parse_name(full_name)
				
				total_precincts = int(results_row[7:11])
				vote_count = int(results_row[11:18])
				precincts_reporting = int(results_row[18:22])
				if full_ID[22:25] == "DEM" or full_ID[22:25] == "REP" or full_ID[22:25] == "NON":
					cand_party = full_ID[22:25]
					amendment = "False"
				else:
					cand_party = ""
					amendment = "True"
				ballot_order = int(info_line[0][4:7])

				if race_name not in added:
					# creates object in format of race object for use in TribPub's Google Sheet
					race_obj = {
						"name": race_name.title(),
						"description": "",
						"election_date": "2020-11-03",
						"market": "chinews",
						"uncontested": False,
						"amendment": bool(amendment),
						"state_postal": "IL",
						"recount": False,
						"reporting_units": [
						    {
						        "name": "Cook",
						        "level": "county",
						        "district_type": "",
						        "state_postal": "IL",
						        "geo_id": "",
						        "electoral_vote_total": 0,
						        "precincts_reporting": int(precincts_reporting),
						        "total_precincts": int(total_precincts),
						        "data_source_update_time": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S%z'),
						        "candidates": [] # creates empty list for candidates info
						    }
						]
					}

					cook_county_results.append(race_obj)
					added.append(race_name)
				else:
					pass

				for item in cook_county_results:
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
	
	# print(cook_county_results)

	with open('scrapers/cook_files/cook_data.json', 'w', encoding='utf-8') as f:
		json.dump(cook_county_results, f, ensure_ascii=False, indent=4)

	return cook_county_results

# this should be commented out when running the app
# leave it in if you're just testing the scraper
# scrape_cook()


	## This also works if we have issues with the dict for some reason and want to only use SummaryExport.txt.

	# with open('SummaryExport.txt','r') as f:
	# 	data = f.readlines()[6:]
	# 	for row in data:
	# 		# splits row by an instance of two or more characters of white space
	# 		# https://stackoverflow.com/questions/48917121/split-on-more-than-one-space
	# 		row = re.split(r"\s{2,}", row)
	# 		if "&" in row[2]:
	# 			pass
	# 		else:
	# 			row_race_name = row[1]
	# 			row_geography = row[3]
	# 			cand_id = row[0]
	# 			total_precincts = int(cand_id[7:11])
	# 			vote_count = int(cand_id[11:18])
	# 			precincts_reporting = int(cand_id[18:22])
	# 			cand_party = cand_id[22:]
	# 			if cand_party == "":
	# 				amendment = True
	# 			else:
	# 				amendment = False
	# 			ballot_order = int(cand_id[5:7])
				
	# 			# handles splitting names up
	# 			row_cand_name = row[2]
	# 			print(row_cand_name)
	# 			full_name = pp.parse(row_cand_name, 'person') # uses probablepeople to parse names into a list
	# 			if len(full_name) == 1:
	# 				first_name = ""
	# 				middle_name = ""
	# 				last_name = full_name[0][0]
	# 			elif len(full_name) == 2:
	# 				first_name = full_name[0][0]
	# 				middle_name = ""
	# 				last_name = full_name[1][0]
	# 			elif len(full_name) == 3:
	# 				first_name = full_name[0][0]
	# 				middle_name = full_name[1][0]
	# 				last_name = full_name[2][0]
	# 			elif len(full_name) == 4:
	# 				first_name = full_name[0][0]
	# 				middle_name = full_name[1][0]
	# 				last_name = full_name[2][0]+" "+full_name[3][0]	
				
	# 			if row_race_name not in added:

	# 				# creates object in format of race object for use in TribPub's Google Sheet
	# 				race_obj = {
	# 					"name": row_race_name,
	# 					"description": "",
	# 					"election_date": "2020-11-03",
	# 					"market": "chitrib",
	# 					"uncontested": False,
	# 					"amendment": amendment, # default, can be changed later
	# 					"state_postal": "IL",
	# 					"recount": False,
	# 					"reporting_units": [
	# 					    {
	# 					        "name": "Cook County",
	# 					        "level": "county",
	# 					        "district_type": "",
	# 					        "state_postal": "IL",
	# 					        "geo_id": "",
	# 					        "electoral_vote_total": 0,
	# 					        "precincts_reporting": precincts_reporting,
	# 					        "total_precincts": total_precincts,
	# 					        "data_source_update_time": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S%z'),
	# 					        "candidates": [] # creates empty list for candidates info
	# 					    }
	# 					]
	# 				}

	# 				cook_county_results.append(race_obj)
	# 				added.append(row_race_name)
	# 			else:
	# 				pass

	# 			for item in cook_county_results:
	# 				if item['name'] == row_race_name:
	# 					item['reporting_units'][0]['candidates'].append({
	# 						"first_name": first_name,
	# 						"middle_name": middle_name,
	# 						"last_name": last_name,
	# 						"vote_count": vote_count,
	# 						"party": cand_party,
	# 						"ballot_order": ballot_order
	# 					})
	# 	# print(cook_county_results)
	# 	with open('cook_data.json', 'w', encoding='utf-8') as f:
	# 		json.dump(cook_county_results, f, ensure_ascii=False, indent=4)
	# 	return cook_county_results