import folium
from folium import FeatureGroup
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

def get_program_data(echo_data, program, program_data, district):
    key=dict() # Create a way to look up Registry IDs in ECHO_EXPORTER later

    # We need to provide a custom list of program ids for some programs.
    if ( program.name == "Greenhouse Gas Emissions"):
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

    # Handle special penalties cases...
    if (program.name == "CWA Penalties"): 
        program_data[program.agg_col] = program_data["FED_PENALTY_ASSESSED_AMT"].fillna(0) + program_data["STATE_LOCAL_PENALTY_AMT"].fillna(0)  
    if (program.name == "RCRA Penalties"): 
        program_data[program.agg_col] =  program_data["FMP_AMOUNT"].fillna(0) # Lots of NaNs here. For now, replace with zero :(

    # Filter to 2010 and later
    # Handle CWA separately
    if (program.name == "CWA Violations"): 
        year = program_data[program.date_field].astype("str").str[0:4:1]
        program_data[program.date_field] = year
    program_data[program.date_field] = pd.to_datetime(program_data[program.date_field], format=program.date_format, errors='coerce')
    program_data=program_data.loc[(program_data[program.date_field] >= pd.to_datetime('2010'))] 
    
    # Aggregate data using agg_col and agg_type from DataSet.py
    program_data.reset_index(inplace=True) # By default, DataSet.py indexes the results from the query. But we have to reset the indext to group it.
    
    t = program_data.groupby([program.idx_field,program.date_field])[[program.agg_col]].agg(program.agg_type) # Count inspections and violations, sum emissions and penalties
    t=t.groupby([pd.Grouper(level=program.idx_field), 
        pd.Grouper(level=program.date_field, freq='Y')] # Summarize everything by year to make search faster
    ).sum()

    state_bars = program_data.groupby(program.date_field)[[program.agg_col]].agg(program.agg_type) # Sum of total emissions or penalties, or count of inspections or violations, in the district
    state_bars = state_bars.resample('Y').sum() # Summarize by year
    state_bars.index = state_bars.index.strftime('%Y') # Make the year look pretty e.g. 2018 instead of 2018-12-31.

    # Find the facility that matches the program data, by REGISTRY_ID.  
    # Add additional information, like congressional district #, lat and lon, facility name, and the program-specific id (index)
    time_data = []
    no_data_ids = []

    # Look through all the facilities in my area and program and get supplemental echo_data info
    if (t is None): # Handle no data
        print("Sorry, we don't have data for this program! That could be an error on our part, or ECHO's, or because the data type doesn't apply to this area.")
    else:
        for fac in t.itertuples():
            fac_id = fac.Index[0] # the facility id
            date = fac.Index[1] # the year
            data = fac[1] # the data we want... e.g. annual emissions 
            reg_id = key[fac_id] # Look up this facility's main Registry ID through its Program ID
            try:
                e=echo_data.loc[echo_data.index==reg_id].copy()[['FAC_NAME', 'FAC_DERIVED_CD113', 'FAC_LAT', 'FAC_LONG', 'DFR_URL', 'FAC_PERCENT_MINORITY']].to_dict('index')
                e = e[reg_id] # remove indexer
                e.update({"Index":fac_id, program.date_field : date, program.agg_col : data})
                time_data.append(e)
            except KeyError:
                # The facility wasn't found in the program data.
                no_data_ids.append( fac.Index )
    
    state_bars = pd.DataFrame(state_bars)
    time_data = pd.DataFrame(time_data)

    # Filter the facilities to the chosen congressional district
    district_time_data = time_data.loc[(time_data["FAC_DERIVED_CD113"]==district)]

    # Create district bar charts
    district_bars = district_time_data.groupby(program.date_field)[[program.agg_col]].sum() # Sum of total emissions, violations, etc. _in this district_ for the whole year
    district_bars = district_bars.resample('Y').sum() # Resample by year
    district_bars.index = district_bars.index.strftime('%Y')

    # Aggregate time data for each facility
    district_program_data = time_data.groupby(["DFR_URL","FAC_DERIVED_CD113", "FAC_LAT","FAC_LONG","FAC_NAME","FAC_PERCENT_MINORITY", "Index"])[[program.agg_col]].sum() # Sum up years
    district_program_data.reset_index(inplace=True)
    district_program_data = district_program_data.loc[(district_program_data["FAC_DERIVED_CD113"]==district)]

    state_bars.reset_index(inplace=True)
    district_bars.reset_index(inplace=True)
    bars = state_bars.join(district_bars, rsuffix=" in this District")
    bars.set_index(program.date_field, inplace=True)

    return district_program_data, bars, all_data



def mapper_area(df, geo_json_data, a, units, program, title):  
    # Initialize the map
    m = folium.Map()

    pg_colors = {"RCRA": "orange", "GHG": "green", "NPDES": "blue", "AIR": "red"}
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
            fill_color = pg_colors[program] if (int(row[a]) > 0) else "grey",
            fill_opacity = .4,
            tooltip = row["FAC_NAME"]+": " + formatter(int(row[a])) + " " + units + ""
        ).add_to(cm_map)
    #folium.GeoJsonTooltip(fields=["District"]).add_to(gj)
    cm_map.add_to(m)
    
    gj = folium.GeoJson(
        geo_json_data,
        name = "Congressional District",
    )
    gj.add_to(m)

    title_html = '<h3 align="center" style="font-size:20px"><b>'+title+'</b></h3>'

    m.get_root().html.add_child(folium.Element(title_html))
    m.keep_in_front(cm_map)
    bounds = m.get_bounds()
    m.fit_bounds(bounds)

    folium.LayerControl().add_to(m)

    return m