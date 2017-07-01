#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Creates a csv file with the financial data of Harvard orgs.

The output file will include official names.
Here is a list below just for reference.

Spee, Lampoon, Gilbert & Sullivan, Hasty Pudding, Crimson, Crimson Trust, Owl,
Owl Capital Management Krokodiloes, Glee, Model Congress Dubai, Band, Yearbook,
Debate, Collegium Musicum, US-China Reltions In order to use this script on
specific organizations, find their propublica numbers from the website
"""

import json
import urllib2
import csv

PRONUMS = ["43078945", "42631286", "42645068", "41425590", "42426396", "222780253",
           "41696700", "204744523", "43573739", "42628384", "460697343", "43009105",
           "42456752", "202775261", "46042150", "42597463", "42587675", "204741249"]

def main():
    """Compiles data into csv file"""
    with open("data.csv", "wb") as csv_file:
        writer = csv.writer(csv_file, delimiter=",")
        toprow = ["Club Name", "Propublica Number", "Tax Year",
                  "Total Revenue", "Total Functional Expenses", "Net Income",
                  "Total Assets", "Total Liabilities", "Net Assets"]
        writer.writerow(toprow)
        for pronum in PRONUMS:
            url = "https://projects.propublica.org/nonprofits/api/v2/organizations/"+pronum+".json"
            clubjson = json.loads(urllib2.urlopen(url).read())
            officialname = clubjson["organization"]["name"]
            for filing in clubjson["filings_with_data"]:
                year = filing["tax_prd_yr"]
                totrev = filing["totrevenue"]
                totexp = filing["totfuncexpns"]
                netinc = int(totrev) - int(totexp)
                totass = filing["totassetsend"]
                totlia = filing["totliabend"]
                netass = int(totass) - int(totlia)
                writer.writerow([officialname, pronum, year, totrev, totexp,
                                 netinc, totass, totlia, netass])

if __name__ == "__main__":
    main()
