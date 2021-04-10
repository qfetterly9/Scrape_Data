# Scrape_Data
This hold files to both download from both the Sheriff's page and CCAP/DOC

### ccap_mhtml_extract.py
  This will read through a directory tree and find all the .html and .mhtml files scraped from CCAP and extract 3 tab files (csv files with tab separators) 
  into a directory called output. 
  
  The dates on these files are the initiation date for the earliest and latest case processed. 
  * race_sex2019-01-02_to_2019-12-30.csv
    * This has demographic data for each case. If one person has more than one case there will be multiple lines.  The linked cases are all lumped into one field in each record
    
  - court_records2019-01-02_to_2019-12-30.csv
    - This has the court records for each case. There will be one row for each new court event.  Some data like bail are extracted where they are included
    
  - ext_charges2019-01-02_to_2019-12-30.csv
    - This file will have the charges including modifiers.  If the case is closed it also extracts data about the sentence. 

    
### QuinnMHTML.py
- This is the program that searches CCAP for specific types of cases (now battery in Dane County), expands the charges and then downloads them as .mhtml files. 
Using .mhtml files leaves us with files that are both easily readable by both humans and machines. 

### Quinn_mhtml_READ_ME.docx
- Documentation for QuinnMHTML.py

### README.md
- this file

### scrape2_nodb_look.py
  - This scrapes the sherrif's webpage and then extracts data into a sqlite3 two files for the booking information and the charges

      - charges2021-01-01T18-30.csv
      - all_in_jail2021-01-01T18-30.csv


