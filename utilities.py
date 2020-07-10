import folium
from folium.plugins import FastMarkerCluster
from folium import FeatureGroup
from folium.features import DivIcon
import numpy as np
import pandas as pd
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

def get_program_data(echo_data, program, program_data):
    key=dict() # Create a way to look up Registry IDs in ECHO_EXPORTER later

    # We need to provide a custom list of program ids for some programs.
    if ( program.name == "CAA Inspections" or program.name == "CAA Enforcements"):
        # The REGISTRY_ID field is the index of the echo_data
        registry_ids = echo_data[echo_data['AIR_FLAG'] == 'Y'].index.values
        key = { i : i for i in registry_ids }
        program_data = program.get_data( ee_ids=registry_ids )
    elif ( program.name == "Greenhouse Gas Emissions" or program.name == "Toxic Releases Inventory - Air" ):
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

    # Filter to 2010 and later
    if (program.name == "CWA Violations"): 
        year = program_data[program.date_field].astype("str").str[0:4:1]
        program_data[program.date_field] = year

    program_data[program.date_field] = pd.to_datetime(program_data[program.date_field], format=program.date_format, errors='coerce')
    program_data=program_data.loc[(program_data[program.date_field] >= pd.to_datetime('2010'))] 
    
    # Aggregate data using agg_col and agg_type from DataSet.py
    if ((program.agg_type=="count") & (program.name.find("RCRA") == -1)):
        program_data['State'] = np.where((program_data[program.agg_col]=="S") | (program_data[program.agg_col]=="State"), 1,0) # Count state actions
        program_data['Federal'] = np.where((program_data[program.agg_col]=="E") | (program_data[program.agg_col]=="EPA"), 1,0) # Count EPA actions
        program_data.reset_index(inplace=True) # By default, DataSet.py indexes the results from the query. But we have to reset the indext to group it.
        bars = program_data.groupby(program.date_field)[["State", "Federal"]].sum() #Sum the counted State/EPA actions
        bars = bars.resample("Y").sum()
        bars.index = bars.index.strftime('%Y')
        stacked=True
        program_data = program_data.groupby([program.idx_field])[[program.agg_col]].agg(program.agg_type) # Count of inspections etc. for each facility
    else:
        program_data.reset_index(inplace=True) # By default, DataSet.py indexes the results from the query. But we have to reset the indext to group it.
        bars = program_data.groupby(program.date_field)[[program.agg_col]].agg(program.agg_type) # Sum of total emissions etc. in the district per year
        bars = bars.resample('Y').sum() # Sum again in case it wasn't summed the first time...
        bars.index = bars.index.strftime('%Y') 
        stacked=False
        program_data = program_data.groupby([program.idx_field])[[program.agg_col]].agg(program.agg_type) # Sum of emissions etc. for each facility across years
    
    print("representing "+str(program_data.shape[0])+" facilities.")

    # Find the facility that matches the program data, by REGISTRY_ID.  
    # Add lat and lon, facility name, and an index
    # (Note: not adding REGISTRY_ID right now as it is sometimes interpreted as an int and that messes with the charts...)
    my_prog_data = []
    no_data_ids = []

    # Look through all the facilities in my area and program and get supplemental echo_data info
    if (program_data is None): # Handle no data
        print("Sorry, we don't have data for this program! That could be an error on our part, or ECHO's, or because the data type doesn't apply to this area.")
    else:
        for fac in program_data.itertuples():
            fac_id = fac.Index # Use the Index
            reg_id = key[fac_id] # Look up this facility's Registry ID through its Program ID
            try:
                e=echo_data.loc[echo_data.index==reg_id].copy()[['FAC_NAME', 'FAC_LAT', 'FAC_LONG', 'DFR_URL', 'FAC_PERCENT_MINORITY']].to_dict('index')
                e = e[reg_id] # remove indexer
                p =  fac._asdict() #split id and year?
                e.update(p)
                my_prog_data.append(e)
            except KeyError:
                # The facility wasn't found in the program data.
                no_data_ids.append( fac.Index )
   
    my_prog_data=pd.DataFrame(my_prog_data)
    bars = pd.DataFrame(bars)


    return my_prog_data, bars, stacked

# Helps us make the map! PUT IN UTILITIES....
# Based on https://medium.com/@bobhaffner/folium-markerclusters-and-fastmarkerclusters-1e03b01cb7b1
def mapper_marker(df):
    # Initialize the map
    m = folium.Map()

    # Create the Marker Cluster array
    #kwargs={"disableClusteringAtZoom": 10, "showCoverageOnHover": False}
    
    # Adjust Leaflet-specific properties
    #callback = ('function (row) {' 
                #'var marker = L.circleMarker(new L.LatLng(row[0], row[1]), {radius: 5, fill: "orange"});'
                #"var popup = L.popup({maxWidth: '300'});"
                #"const display_text = {text: row[2]};"
                #"var mytext = $(`<div id='mytext' class='display_text' style='width: 100.0%; height: 100.0%;'> ${display_text.text}</div>`)[0];"
                #"popup.setContent(mytext);"
                #"marker.bindPopup(popup);"
                #'return marker};')
    mc = FastMarkerCluster("")
 
    # Add a clickable marker for each facility
    for index, row in df.iterrows():
        mc.add_child(folium.CircleMarker(
            location = [row["FAC_LAT"], row["FAC_LONG"]],
            popup = row["FAC_NAME"] + "<p><a href='"+row["DFR_URL"]+"' target='_blank'>Link to ECHO detailed report</a></p>",
            radius = 8,
            color = "black",
            weight = 1,
            fill_color = "orange",
            fill_opacity= .4
        ))
    
    m.add_child(mc)
    #m.add_child(FastMarkerCluster(df[["FAC_LAT", "FAC_LONG", "FAC_NAME"]].values.tolist(), callback=callback))
    bounds = m.get_bounds()
    m.fit_bounds(bounds)

    # Show the map
    return m

def mapper_area(df, geo_json_data, g, a): #att_data, 
    # Initialize the map
    m = folium.Map()

    # Scale the size of the circles
    scale = {0:4, 1:10, 2:16, 3:24, 4:32}
    # Add a clickable marker for each facility
    cm_map = FeatureGroup(name="Facilities")
    for index, row in df.iterrows():
        folium.CircleMarker(
            location = [row["FAC_LAT"], row["FAC_LONG"]],
            popup = row["FAC_NAME"] +": " + formatter(int(row[a])) + "<p><a href='"+row["DFR_URL"]+"' target='_blank'>Link to ECHO detailed report</a></p>", # + "<p><a href='"+row["DFR_URL"]+"' target='_blank'>Link to ECHO detailed report</a></p>",
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
    folium.GeoJsonTooltip(fields=["ids"]).add_to(gj)
    gj.add_to(m)

    # q = pd.cut(np.array(att_data['value']), bins=5) # Creates an Equal Interval scale with 5 bins. #quantile([0, 0.25,0.5,0.75, 1]) # Create a quantile scale. This should put an equal number of geographies in each bin/color.
    # c = folium.Choropleth(
    #     geo_data = geo_json_data,
    #     data = att_data,
    #     columns =['geo', 'value'], key_on='feature.properties.'+g, # Join the geo data and the attribute data on a key id
    #     fill_color ='OrRd',fill_opacity=0.75,line_weight=.5,nan_fill_opacity=.5, nan_fill_color="grey", highlight=True, 
    #     bins =[min(att_data['value']), q.categories[1].left, q.categories[2].left, q.categories[3].left, q.categories[4].left, max(att_data['value'])],
    #     legend_name = a,
    #     name = g,
    # ).add_to(m)
    # c.geojson.add_child(
    #             folium.features.GeoJsonTooltip([g])
    #         )
    
    m.keep_in_front(cm_map)
    bounds = m.get_bounds()
    m.fit_bounds(bounds)

    folium.LayerControl().add_to(m)

    return m