import requests
import pandas as pd
from bs4 import BeautifulSoup
from tika import parser
import io
import re
import time

base_url = "https://disclosures-clerk.house.gov/PublicDisclosure/FinancialDisclosure/"

def clerk_request(member_lastname=None) -> BeautifulSoup:  
    """
    Makes a request to the Office of the Clerk's website for member financial
    disclosures
    
    Parameters
    ----------
    member_lastname: str or None, default None
        Member to get filings of. If None gets all data.
    
    Returns
    -------
    Response
        BeautifulSoup: Souped HTML response of request to clerk query tool.
    """
    endpoint = base_url + "ViewMemberSearchResult"
    if member_lastname is None:
        clerk_response = requests.post(endpoint)
    else:
         clerk_response = requests.post(endpoint, data ={"LastName": member_lastname})
    clerk_response.raise_for_status()
    souped_response = BeautifulSoup(clerk_response.text, "lxml")
    return souped_response
 
def clerk_filings(member_lastname=None, filing_range: int=2014) -> pd.DataFrame: 
    
    """
    Parses member filing data into a DataFrame. 
    
    Parameters
    ----------
    member_lastname: str or None, default None
        Member to get filings of. If None gets all data.
    
    filing_range: Int, default 2014
        Date range of filings to grab. Defaults to 2014,
        when electronic filing was introduced.
    
    Returns
    -------
    pd.DataFrame
        HTML table from clerk request parsed into a DataFrame
    """
    
    table_collection = []

    souped_response = clerk_request(member_lastname=member_lastname)

    for table_row in souped_response.find_all('tr'):
        row = {}
        for table_cell in table_row.find_all('td'):
            link_field = table_cell.find('a')
            if link_field:
                row.update({'href': link_field.get('href'), table_cell.get('data-label'): table_cell.text})
            else:
                row.update({table_cell.get('data-label'): table_cell.text})
        if row:
            table_collection.append(row)
    
    filings_df =  pd.DataFrame(table_collection)
     
    filings_df["Filing Year"] = filings_df["Filing Year"].apply(lambda x: int(x))
     
    return filings_df[filings_df["Filing Year"] >= filing_range]


def request_pdf_to_string(pdf_endpoint):
    
    """
    Gets member filing pdf data. Used as a lambda on href from clerk_filings.   
    
    Parameters
    ----------
    request_directory: str
        Directory URL of relevant PDF. Gets concatenated onto base URL.    
    filing_rang: Int, default 2014
    
    Returns
    -------
    string
        String content of requested PDF.
    """
    
    request_url = "https://disclosures-clerk.house.gov" + pdf_endpoint
    time.sleep(1)
    pdf_bytes = requests.get(request_url).content
    with io.BytesIO(pdf_bytes) as pdf_stream:
        tika_dict = parser.from_buffer(pdf_stream)
        pdf_string = tika_dict["content"]
    return pdf_string


def get_pdf(member_lastname):
    response_df = clerk_filings(member_lastname=member_lastname).iloc[:5]
    response_df["pdf_string"] = response_df["href"].apply(lambda x: request_pdf_to_string(x))
    return response_df

def parse_pdf(pdf_string: str, pattern: str="\\n(((?!\\n).)*)\s\w{2}\s(\$[0-9\,]+.*?\$[0-9\,]+)"):
    investment_list_extract = re.findall(pattern, pdf_string, flags=re.I | re.S | re.M)
    return investment_list_extract
