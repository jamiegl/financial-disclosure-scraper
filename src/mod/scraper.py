import requests

def clerk_request(member_lastname=None) -> requests.Response:  
    """
    Makes a request to the House of Clerks website for member financial
    disclosures
    
    Parameters
    ----------
    member_lastname: str or None, default None
        Member to get filings of. If None gets all data.
    
    Returns
    -------
    Response
        Response of request.
    """
    
    if member_lastname is None:
        clerk_response = requests \
        .post("https://disclosures-clerk.house.gov/PublicDisclosure/FinancialDisclosure/ViewMemberSearchResult")
    else:
         clerk_response = requests \
        .post("https://disclosures-clerk.house.gov/PublicDisclosure/FinancialDisclosure/ViewMemberSearchResult", data ={"LastName": member_lastname})
    return clerk_response