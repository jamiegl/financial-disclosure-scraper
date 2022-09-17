import requests
import pandas as pd
from bs4 import BeautifulSoup
from tika import parser
import io
import re
import time

base_url = "https://disclosures-clerk.house.gov/PublicDisclosure/FinancialDisclosure/"

def _clerk_request(member_lastname=None) -> BeautifulSoup:  
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
        bs4.BeautifulSoup: Souped HTML response of request to clerk query tool.
    """
    endpoint = base_url + "ViewMemberSearchResult"
    if member_lastname is None:
        clerk_response = requests.post(endpoint)
    else:
         clerk_response = requests.post(endpoint, data ={"LastName": member_lastname})
    clerk_response.raise_for_status()
    souped_response = BeautifulSoup(clerk_response.text, "lxml")
    return souped_response
 
def _clerk_filings(member_lastname=None, filing_range=2014): 
    
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
    DataFrame
        Response of request.
    """
    
    clerk_request = _clerk_request(member_lastname)
    
    souped_request = BeautifulSoup(clerk_request, 'lxml')

    table_collection = []

    for table_row in souped_request.find_all('tr'):
        row = {}
        for table_cell in table_row.find_all('td'):
            if table_cell.find('a') is not None:
                row.update({'href': table_cell.find('a').get('href'), table_cell.get('data-label'): table_cell.text})
            else:
                row.update({table_cell.get('data-label'): table_cell.text})
        table_collection.append(row)
    
    filings_df =  pd.DataFrame(table_collection[1:])
     
    filings_df["Filing Year"] = filings_df["Filing Year"].apply(lambda x: int(x))
     
    return filings_df[filings_df["Filing Year"] >= filing_range]
     
def _request_pdf_bytes(request_directory):
    
    """
    Gets member filing pdf data. Used as a lambda on href from clerk_filings.   
    
    Parameters
    ----------
    request_directory: str
        Directory URL of relevant PDF. Gets concatenated onto base URL.    
    filing_rang: Int, default 2014
    
    Returns
    -------
    bytes
        Content of request response.
    """
    
    request_url = "https://disclosures-clerk.house.gov" + request_directory
    time.sleep(1)
    pdf_bytes = requests.get(request_url).content
    return pdf_bytes

def _pdf_bytes_to_string(pdf_bytes):
    
    """
    Turns pdf bytes into a stream which is read by a Tika parser.
    
    Parameters
    ----------
    pdf_bytes: bytes
        Bytes of PDF file.
    
    Returns
    -------
    String
        Text contents of PDF.
    """
    
    with io.BytesIO(pdf_bytes) as pdf_stream:
        tika_dict = parser.from_buffer(pdf_stream)
        pdf_string = tika_dict["content"]
    return pdf_string

def _parse_tickers(investment_name):
    
    ticker_matcher = re.match(r".*?\s\((.*?)\)", investment_name)
    
    if ticker_matcher is None:
        return None
    else:
        return ticker_matcher[1]

def _parse_investment(investment_range):
    
    investment_range = investment_range.replace(",", "").replace("-", "")
    investment_matcher = re.findall(r"\$([0-9]+)", investment_range)
    
    if investment_matcher is None:
        return [None, None, investment_range.replace("$", "")]
    else:
        investment_average = (int(investment_matcher[0]) + int(investment_matcher[1]))/2
        return [investment_matcher[0], investment_matcher[1], investment_average]


def _tabulate_filing_pdf(request_directory, tickers_only=True, pattern="\\n(((?!\\n).)*)\s\w{2}\s(\$[0-9\,]+.*?\$[0-9\,]+)"):
    
    pdf_bytes = _request_pdf_bytes(request_directory)
    
    pdf_string = _pdf_bytes_to_string(pdf_bytes)
    
    investment_list_extract = re.findall(pattern, pdf_string, flags=re.I | re.S | re.M)
    
    investment_df = pd.DataFrame(investment_list_extract, columns=["name", "trash", "investment"]).drop("trash", axis=1)
    
    investment_df = investment_df[investment_df["name"].str.lower().str.find('description') == -1]
    
    investment_df["investment_array"] = investment_df["investment"].apply(lambda x: _parse_investment(x))
    
    investment_df["lower_limit/$"] = investment_df["investment_array"].apply(lambda x: x[0])
    investment_df["upper_limit/$"] = investment_df["investment_array"].apply(lambda x: x[1])
    investment_df["average/$"] = investment_df["investment_array"].apply(lambda x: x[2])
    
    investment_df = investment_df.drop("investment_array", axis=1)

    
    if tickers_only is True:
        investment_df["ticker"] = investment_df["name"].apply(lambda x: _parse_tickers(x))
        investment_df = investment_df[investment_df["ticker"].notnull()]
        return investment_df
    else:
        return investment_df

def collect_filings(member_lastname=None, filing_range=2014):
    filing_df = _clerk_filings(member_lastname, filing_range)
    concat_df = pd.DataFrame()
    data = filing_df["href"].apply(lambda x: [_tabulate_filing_pdf(x), x])

    for tuple in data:
        dfc = pd.DataFrame(tuple[0])
        dfc["href"] = tuple[1]
        concat_df = concat_df.append(dfc)
    
    joined_df = concat_df.set_index('href').join(filing_df.set_index('href'))
    joined_df = joined_df[joined_df["ticker"].str.lower().str.find('formerly') == -1]
    
    return joined_df
            
 
    

