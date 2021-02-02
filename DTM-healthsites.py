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

# %% [markdown]
# ## Todo:
# - [x] Get DTM data .xslx for Mozambique
# - [x] Get Healthsites.io facilities for Mozambique
# - [x] Map locations together
# - [x] Get the nearest hospital to each displacement site (as the crow flies, for now)
# - [x] Map the straight-line distance from each site to the nearest hospital
# - [ ] Use OSRM to calculate travel time (by fooot) for every site to their nearest hospital
# - [ ] Make a histogram of travel times

# %%
import pandas as pd
import requests
import openpyxl
import geopandas as gpd
import folium 
from shapely.ops import nearest_points
from shapely.geometry import LineString
from IPython.display import Markdown

# %%
dtm = pd.read_excel("Mozambique - Site Assessment - Cyclone IDAI and Floods - Round 18.xlsx")
dtm.rename(columns={'Latitude':'lat', 'Longitude':'lon'}, inplace=True)
dtm_short = dtm[['SSID','lat','lon']]

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
t = pd.DataFrame(hsio_short['centroid.coordinates'].to_list(), columns=['lon', 'lat'])
hsio_short = hsio_short.join(t, how='outer').drop(['centroid.coordinates'], axis=1)


# %%
def create_gdf(df, x="lon", y="lat"):
    return gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df[x], df[y]), crs="epsg:4326")

hsio_short_gdf = create_gdf(hsio_short)
dtm_short_gdf = create_gdf(dtm_short)

# %%
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
def calculate_nearest(row, destination, val, col="geometry"):
    dest_unary = destination["geometry"].unary_union
    nearest_geom = nearest_points(row[col], dest_unary)
    match_geom = destination.loc[destination.geometry == nearest_geom[1]]
    match_value = match_geom[val].to_numpy()[0]
    return match_value

dtm_short_gdf["nearest_geom"] = dtm_short_gdf.apply(calculate_nearest, destination=hsio_short_gdf, val="geometry", axis=1)
dtm_short_gdf["nearest_hospital"] = dtm_short_gdf.apply(calculate_nearest, destination=hsio_short_gdf, val="attributes.name", axis=1)

# %%
dtm_short_gdf

# %%
# Create LineString Geometry
dtm_short_gdf['line'] = dtm_short_gdf.apply(lambda row: LineString([row['geometry'], row['nearest_geom']]), axis=1)
# Create Line Geodataframe
line_gdf = dtm_short_gdf[["SSID", "nearest_hospital", "line"]].set_geometry('line')
# Set the Coordinate reference
line_gdf.crs = crs="epsg:4326"

# %%
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



# %%
dtm_short_gdf

# %%
dtm_short_gdf.geometry.x
