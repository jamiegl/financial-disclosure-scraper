import requests
import pandas as pd
import lxml
from bs4 import BeautifulSoup
from tika import parser
import io
import re

data = requests \
    .post("https://disclosures-clerk.house.gov/PublicDisclosure/FinancialDisclosure/ViewMemberSearchResult", data ={"LastName": "Pelosi"}).text

#%%

soup = BeautifulSoup(data, 'lxml')

lista = []

for link in soup.find_all('tr'):
    row = {}
    for foo in link.find_all('td'):
        if foo.find('a') is not None:
            row.update({'href': foo.find('a').get('href'), foo.get('data-label'): foo.text})
        else:
            row.update({foo.get('data-label'): foo.text})
    print(row, '\n')
    lista.append(row)
    
df = pd.DataFrame(lista[1:])   

#%%

rel_pdf = requests.get('https://disclosures-clerk.house.gov/public_disc/financial-pdfs/2016/10015814.pdf')

#%%

with io.BytesIO(rel_pdf.content) as open_file:
    raw = parser.from_buffer(open_file)

#%%


vx = re.findall("\\n(((?!\\n).)*)\s\w{2}\s(\$[0-9\,]+.*?\$[0-9\,]+)", raw["content"], flags=re.I | re.S | re.M)

df2 = pd.DataFrame(vx, columns=["Name", "Trash", "Investment"]).drop("Trash", axis=1)

df2 = df2[df2["Name"] != ""]

df2 = df2[df2["Name"].str.lower().str.find('description') == -1]









