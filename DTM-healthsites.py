# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.11.4
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# ## Todo:
# - [x] Get DTM data .xslx for Mozambique
# - [x] Get Healthsites.io facilities for Mozambique
# - [x] Map locations together
# - [x] Get the nearest hospital to each displacement site (as the crow flies, for now)
# - [x] Map the straight-line distance from each site to the nearest hospital
# - [x] Use OSRM to calculate travel time (by fooot) for every site to their nearest hospital
# - [ ] Make a histogram of travel times

# %%
import pandas as pd
import requests
import openpyxl
import geopandas as gpd
import folium 
import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib
from shapely.ops import nearest_points
from shapely.geometry import LineString
from IPython.display import Markdown
matplotlib.rcParams.update({'font.size': 14})
# %matplotlib inline

# %%
# get DTM data
dtm = pd.read_excel("Mozambique - Site Assessment - Cyclone IDAI and Floods - Round 18.xlsx")
dtm.rename(columns={'Latitude':'lat', 'Longitude':'lon','How long does it take to reach the nearest health facility from the site?':'health_facility_distance'}, inplace=True)
dtm_short = dtm[['SSID','lat','lon','health_facility_distance']]

# get health facilities data
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

hsio_short = hsio[['osm_id','attributes.name','centroid.coordinates']]
hsio_short['centroid.coordinates']
t = pd.DataFrame(hsio_short['centroid.coordinates'].to_list(), columns=['lon', 'lat'])
hsio_short = hsio_short.join(t, how='outer').drop(['centroid.coordinates'], axis=1)


# %%
# make geodf and map sites and facilities
def create_gdf(df, x="lon", y="lat"):
    return gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df[x], df[y]), crs="epsg:4326")

hsio_short_gdf = create_gdf(hsio_short)
dtm_short_gdf = create_gdf(dtm_short)

m = folium.Map([-20.0760232,34.3582913909869],
               zoom_start=10,
               tiles="CartoDb dark_matter")
locs_dtm_short = zip(dtm_short_gdf.lat, dtm_short_gdf.lon)
locs_hsio_short = zip(hsio_short_gdf.lat, hsio_short_gdf.lon)
for location in locs_dtm_short:
    folium.CircleMarker(location=location, color="red", radius=4).add_to(m)
for location in locs_hsio_short:
    folium.CircleMarker(location=location, color="white", radius=2).add_to(m)
#m.save("map1.html")
m

# %%
Markdown(f" There are {len(dtm_short)} DTM tracked displacement sites in Mozambique and {len(hsio_short)} health facilities")


# %%
# calculate the nearest health facility from each site
def calculate_nearest(row, destination, val, col="geometry"):
    dest_unary = destination["geometry"].unary_union
    nearest_geom = nearest_points(row[col], dest_unary)
    match_geom = destination.loc[destination.geometry == nearest_geom[1]]
    match_value = match_geom[val].to_numpy()[0]
    return match_value

dtm_short_gdf["nearest_geom"] = dtm_short_gdf.apply(calculate_nearest, destination=hsio_short_gdf, val="geometry", axis=1)
dtm_short_gdf["nearest_hospital"] = dtm_short_gdf.apply(calculate_nearest, destination=hsio_short_gdf, val="attributes.name", axis=1)

# %%
# Create LineString Geometry and map
dtm_short_gdf['line'] = dtm_short_gdf.apply(lambda row: LineString([row['geometry'], row['nearest_geom']]), axis=1)
line_gdf = dtm_short_gdf[["SSID", "nearest_hospital", "line"]].set_geometry('line')
line_gdf.crs = crs="epsg:4326"

m = folium.Map([-20.0760232,34.3582913909869],zoom_start = 10,  
    tiles='CartoDb dark_matter')
locs_hsio_short = zip(hsio_short_gdf.lat, hsio_short_gdf.lon)
locs_dtm_short = zip(dtm_short_gdf.lat, dtm_short_gdf.lon)

folium.GeoJson(line_gdf).add_to(m)
for location in locs_hsio_short:
    folium.CircleMarker(location=location, color="white", radius=2).add_to(m)
for location in locs_dtm_short:
    folium.CircleMarker(location=location, color="red", radius=4).add_to(m)
#m.save('map2.html')
m



# %% [markdown]
# ## OSM Routing

# %%
test=dtm_short_gdf.copy()
test['site_lon_lat']= test['lon'].astype(str)+','+test['lat'].astype(str)
test = test.set_geometry('nearest_geom')
test['clinic_lon_lat'] = test.geometry.x.astype(str)+','+test.geometry.y.astype(str)

def distance(start, end):
    api_key ='5b3ce3597851110001cf6248a141c1919e684c33a2bec1ab18ea3f4c'
    url ='https://api.openrouteservice.org/v2/directions/foot-walking?'
    try:
        r = requests.get(url + 'api_key=' + api_key + '&start=' + start + '&end=' + end)
        x = r.json()
        distance = x['features'][0]['properties']['summary']['distance']/1000
    except KeyError:
        distance = 'error'
    return distance

def duration(start, end):
    api_key ='5b3ce3597851110001cf6248a141c1919e684c33a2bec1ab18ea3f4c'
    url ='https://api.openrouteservice.org/v2/directions/foot-walking?'
    try:
        r = requests.get(url + 'api_key=' + api_key + '&start=' + start + '&end=' + end)
        x = r.json()
        duration = x['features'][0]['properties']['summary']['duration']/60
    except KeyError:
        duration = 'error'
        #print(url + 'api_key=' + api_key + '&start=' + start + '&end=' + end)
    return duration

#test['distance'] = test.apply(lambda x: distance(x['site_lon_lat'],x['clinic_lon_lat']),axis=1)
test['duration'] = test.apply(lambda x: duration(x['site_lon_lat'],x['clinic_lon_lat']),axis=1)

# %%
## histogram of computed travel times
from matplotlib.ticker import (MultipleLocator, AutoMinorLocator)
matplotlib.rcParams.update({'font.size': 11})

x = (test[test['duration'] !='error']['duration']).astype(int)

fig,ax = plt.subplots(1, 1, figsize=(12,5))
#ax.hist(x, density=False, bins=np.arange(min(x), max(x) + 50, 50))  # density=False would make counts
ax.hist(x, density=False, bins=20) 
ax.set_ylabel('Number of sites')
ax.set_xlabel('Travel time (minutes)')
ax.xaxis.set_major_locator(MultipleLocator(20))
ax.yaxis.set_major_formatter('{x:.0f}')
ax.set_title('Calculated travel time (by foot) between IDP sites and health facilities - Mozambique')

fig.savefig(f"distance.svg", format="svg", transparent=True, bbox_inches='tight', pad_inches=0) 
fig.savefig(f"distance.png", format="png", transparent=True, bbox_inches='tight', pad_inches=0) 

# %%
fig,ax = plt.subplots(1, 1, figsize=(12,5))
ax.hist(test['health_facility_distance'], density=False, bins=20) 


# %%
test =test[test['duration']!='error'].copy()
test['ki_duration_code'] = test['health_facility_distance'].replace(['Less than 15 minutes','16 - 30 minutes','31 - 60 minutes','More than 60 minutes'],[1,2,3,4])
test['computed_duration_code'] = pd.cut(test['duration'], bins=[0,15,30,60,500], labels=[1,2,3,4])

# %%
fig,[ax1,ax2] = plt.subplots(2, 1, figsize=(12,5))
ax1.hist(test['ki_duration_code'], density=False, bins=4) 
ax2.hist(test['computed_duration_code'], density=False, bins=4) 

#test[['ki_distance_code','computed_distance_code']]

# %%
#test[['ki_duration_code','computed_duration_code']]
test['duration_gap'] = test['ki_duration_code'].astype(int)-test['computed_duration_code'].astype(int)
fig,ax = plt.subplots(1, 1, figsize=(12,5))
ax.hist(test['duration_gap'], density=True, bins=4) 

# %%
test.to_excel('temp.xlsx')

# %%
