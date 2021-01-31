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
#for cols in dtm.columns:
#    print(cols)
dtm_short = dtm[['SSID','Latitude','Longitude']]
dtm_short

# %%
