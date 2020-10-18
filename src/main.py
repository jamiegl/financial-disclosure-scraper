import scraper.helpers as sch
import pandas as pd

# Generates image from readme
# There is a slice on the collect_filings function - remove it if 
# you want more rows

data = sch.collect_filings('Pelosi')