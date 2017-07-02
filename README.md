# propublica-data
A python script that uses the Propublica API to retrieve data (in csv format) on any list of non-profit US organizations. To run, simply type "python propublica.py" in your terminal. The data will be outputted as "finaldata.csv".



Currently the script is extracting data on final clubs and other student organizations at Harvard. To look up data on other organizations, simply look for their propublica numbers and edit the "listoforgs.csv" file.

Due to speed of propublica's API, each organization will take around 2-5 seconds resulting in a total of a couple of minutes depending on the number of organizations you input.

To find out more, go to Propublica's Nonprofit Explorer API here: https://projects.propublica.org/nonprofits/api
