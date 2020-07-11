import folium
from folium.plugins import FastMarkerCluster
from folium import FeatureGroup
from folium.features import DivIcon
import numpy as np
import pandas as pd
import geopandas
import matplotlib.pyplot as plt

# Set up some default parameters for graphing
from matplotlib import cycler
colour = "#00C2AB" # The default colour for the barcharts
colors = cycler('color',
                ['#4FBBA9', '#E56D13', '#D43A69',
                 '#25539f', '#88BB44', '#FFBBBB'])
plt.rc('axes', facecolor='#E6E6E6', edgecolor='none',
       axisbelow=True, grid=True, prop_cycle=colors)
plt.rc('grid', color='w', linestyle='solid')
plt.rc('xtick', direction='out', color='gray')
plt.rc('ytick', direction='out', color='gray')
plt.rc('patch', edgecolor='#E6E6E6')
plt.rc('lines', linewidth=2)
font = {'family' : 'DejaVu Sans',
        'weight' : 'normal',
        'size'   : 16}
plt.rc('font', **font)
plt.rc('legend', fancybox = True, framealpha=1, shadow=True, borderpad=1)

# Pretty format numbers
def formatter(value):
    return f'{value:,}'

def get_program_data(echo_data, program, program_data, geo_json_data):
    key=dict() # Create a way to look up Registry IDs in ECHO_EXPORTER later

    #### We need to provide a custom list of program ids for some programs.
    if ( program.name == "CAA Inspections"): 
        # The REGISTRY_ID field is the index of the echo_data
        registry_ids = echo_data[echo_data['AIR_FLAG'] == 'Y'].index.values
        key = { i : i for i in registry_ids }
        program_data = program.get_data( ee_ids=registry_ids )
    elif ( program.name == "Greenhouse Gas Emissions"):
        program_flag = program.echo_type + '_FLAG'
        registry_ids = echo_data[echo_data[ program_flag ] == 'Y'].index.values
        program_data = program.get_data( ee_ids=registry_ids )
        key = { i : i for i in registry_ids }
    else:
        ids_string = program.echo_type + '_IDS'
        ids = list()
        registry_ids = list()
        for index, value in echo_data[ ids_string ].items():
            try:
                for this_id in value.split():
                    ids.append( this_id )
                    key[this_id]=index
            except ( KeyError, AttributeError ) as e:
                pass
        program_data = program.get_data( ee_ids=ids )
    
    all_data=program_data

    #### Handle special penalties cases...
    if (program.name == "CWA Penalties"): 
        program_data[program.agg_col] = program_data["FED_PENALTY_ASSESSED_AMT"].fillna(0) + program_data["STATE_LOCAL_PENALTY_AMT"].fillna(0)  
    if (program.name == "RCRA Penalties"): 
        program_data[program.agg_col] =  program_data["PMP_AMOUNT"].fillna(0) + program_data["FMP_AMOUNT"].fillna(0) + program_data["FSC_AMOUNT"].fillna(0) + program_data["SCR_AMOUNT"].fillna(0) # Lots of NaNs here. For now, replace with zero :(

    #### Filter to 2010 and later
    # Handle CWA separately
    if (program.name == "CWA Violations"): 
        year = program_data[program.date_field].astype("str").str[0:4:1]
        program_data[program.date_field] = year
    program_data[program.date_field] = pd.to_datetime(program_data[program.date_field], format=program.date_format, errors='coerce')
    program_data=program_data.loc[(program_data[program.date_field] >= pd.to_datetime('2010'))] 
    
    #### Aggregate data using agg_col and agg_type from DataSet.py
    program_data.reset_index(inplace=True) # By default, DataSet.py indexes the results from the query. But we have to reset the indext to group it.
    
    t = program_data.groupby([program.idx_field,program.date_field])[[program.agg_col]].agg(program.agg_type)
    t=t.groupby([pd.Grouper(level=program.idx_field), 
        pd.Grouper(level=program.date_field, freq='Y')] #Summarize by year to make search faster
    ).sum()

    state_bars = program_data.groupby(program.date_field)[[program.agg_col]].agg(program.agg_type) # Sum of total emissions etc. in the district per year
    state_bars = state_bars.resample('Y').sum() # Sum again in case it wasn't summed the first time...
    state_bars.index = state_bars.index.strftime('%Y')

    #### Find the facility that matches the program data, by REGISTRY_ID.  
    # Add lat and lon, facility name, and an index
    # (Note: not adding REGISTRY_ID right now as it is sometimes interpreted as an int and that messes with the charts...)
    time_data = []
    no_data_ids = []

    # Look through all the facilities in my area and program and get supplemental echo_data info
    if (t is None): # Handle no data
        print("Sorry, we don't have data for this program! That could be an error on our part, or ECHO's, or because the data type doesn't apply to this area.")
    else:
        for fac in t.itertuples():
            fac_id = fac.Index[0] # the id
            date = fac.Index[1] # the date
            data = fac[1] # the data we want... e.g. annual emissions 
            reg_id = key[fac_id] # Look up this facility's Registry ID through its Program ID
            try:
                e=echo_data.loc[echo_data.index==reg_id].copy()[['FAC_NAME', 'FAC_LAT', 'FAC_LONG', 'DFR_URL', 'FAC_PERCENT_MINORITY']].to_dict('index')
                e = e[reg_id] # remove indexer
                e.update({"Index":fac_id, program.date_field : date, program.agg_col : data})
                time_data.append(e)
            except KeyError:
                # The facility wasn't found in the program data.
                no_data_ids.append( fac.Index )
    
    state_bars = pd.DataFrame(state_bars)
    time_data = pd.DataFrame(time_data)

    # Join the facilities and the chosen district
    gdf = geopandas.GeoDataFrame(
        time_data, crs= "EPSG:4326", geometry=geopandas.points_from_xy(time_data["FAC_LONG"], time_data["FAC_LAT"]))
    district_time_data = geopandas.sjoin(gdf, geo_json_data, how="inner", op='intersects')

    # Create district bar charts
    district_bars = district_time_data.groupby(program.date_field)[[program.agg_col]].sum() # Sum of total emissions, violations, etc. in the district for the whole year
    district_bars = district_bars.resample('Y').sum() # Sum again in case it wasn't summed the first time...
    district_bars.index = district_bars.index.strftime('%Y')

    # Aggregate time data for each facility
    district_program_data = time_data.groupby(["DFR_URL","FAC_LAT","FAC_LONG","FAC_NAME","FAC_PERCENT_MINORITY", "Index"])[[program.agg_col]].sum() # sum up years
    district_program_data.reset_index(inplace=True)
    gdf = geopandas.GeoDataFrame(
        district_program_data, crs= "EPSG:4326", geometry=geopandas.points_from_xy(district_program_data["FAC_LONG"], district_program_data["FAC_LAT"]))
    district_program_data = geopandas.sjoin(gdf, geo_json_data, how="inner", op='intersects')

    state_bars.reset_index(inplace=True)
    district_bars.reset_index(inplace=True)
    bars = state_bars.join(district_bars, rsuffix=" in this District")
    bars.set_index('index', inplace=True)

    return district_program_data, bars, all_data



def mapper_area(df, geo_json_data, a, units):  
    # Initialize the map
    m = folium.Map()

    # Scale the size of the circles
    scale = {0:4, 1:10, 2:16, 3:24, 4:32}
    # Add a clickable marker for each facility
    cm_map = FeatureGroup(name="Facilities")
    for index, row in df.iterrows():
        folium.CircleMarker(
            location = [row["FAC_LAT"], row["FAC_LONG"]],
            popup = row["FAC_NAME"] +": " + formatter(int(row[a])) + " " + units + "<p><a href='"+row["DFR_URL"]+"' target='_blank'>Link to ECHO detailed report</a></p>", # + "<p><a href='"+row["DFR_URL"]+"' target='_blank'>Link to ECHO detailed report</a></p>",
            radius = scale[row["quantile"]],
            color = "black",
            weight = 1,
            fill_color = "orange",
            fill_opacity = .4
        ).add_to(cm_map)
    cm_map.add_to(m)
    
    gj = folium.GeoJson(
        geo_json_data,
        name = "Congressional District",
    )
    folium.GeoJsonTooltip(fields=["District"]).add_to(gj)
    gj.add_to(m)

    
    m.keep_in_front(cm_map)
    bounds = m.get_bounds()
    m.fit_bounds(bounds)

    folium.LayerControl().add_to(m)

    return m