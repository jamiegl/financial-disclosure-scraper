import requests
import pandas as pd
from bs4 import BeautifulSoup
import pdf2image
from typing import Tuple

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

def image_from_endpoint(endpoint: str) -> Tuple:
    """
    Gets PIL image objects from the PDF at the given endpoint.
    
    Parameters
    ----------
    endpoint: str
        Endpoint PDF is located at.

    Returns
    -------
    Tuple
        First elem is image metadata, second elem is array of PIL images for
        each page in PDF.
    """
    base_url = "https://disclosures-clerk.house.gov"
    pdf_response_obj = requests.get(base_url + endpoint)
    pdf_response_obj.raise_for_status()
    pdf_info = pdf2image.pdfinfo_from_bytes(pdf_response_obj.content)
    pdf_pages = pdf2image.convert_from_bytes(pdf_response_obj.content)
    return (pdf_info, pdf_pages)