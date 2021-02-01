# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.9.1
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %%
import pandas as pd
import requests
import openpyxl
import geopandas as gpd

# %%
dtm = pd.read_excel("Mozambique - Site Assessment - Cyclone IDAI and Floods - Round 18.xlsx")
dtm_short = dtm[['SSID','Latitude','Longitude']]

# %%
r = requests.get('https://healthsites.io/api/v2/facilities/?api-key=8d978f6bfa9d7914751307b4ebcc500f711771d0&page=1&country=Mozambique')
data = r.json()
hsio =  pd.json_normalize(data)
r = requests.get('https://healthsites.io/api/v2/facilities/count?country=Mozambique&format=json')
data = r.json()
pagecount = int(data/100)
pagecount
for page in range(2,pagecount+2):
    rtemp = requests.get(f'https://healthsites.io/api/v2/facilities/?api-key=8d978f6bfa9d7914751307b4ebcc500f711771d0&page={page}&country=Mozambique')
    datatemp = rtemp.json()
    hsiotemp =  pd.json_normalize(datatemp)
    hsio = hsio.append(hsiotemp, ignore_index=True)

# %%
hsio_short = hsio[['osm_id','attributes.name','centroid.coordinates']]
hsio_short['centroid.coordinates']
t = pd.DataFrame(hsio_short['centroid.coordinates'].to_list(), columns=['lat', 'long'])
hsio_short.join(t, how='outer').drop(['centroid.coordinates'], axis=1)

# %%
len(dtm_short)
