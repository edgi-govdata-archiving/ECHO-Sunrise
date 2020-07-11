# COUNT BY STATE/FEDERAL ACTIONS
    if ((program.agg_type=="count") & (program.name.find("RCRA") == -1)):
        program_data['State Actions'] = np.where((program_data[program.agg_col]=="S") | (program_data[program.agg_col]=="State"), 1,0) # Count state actions
        program_data['Federal Actions'] = np.where((program_data[program.agg_col]=="E") | (program_data[program.agg_col]=="EPA"), 1,0) # Count EPA actions
        program_data.reset_index(inplace=True) # By default, DataSet.py indexes the results from the query. But we have to reset the indext to group it.
       
        t = program_data.groupby([program.idx_field,program.date_field])[["State Actions", "Federal Actions"]].sum()
        t=t.groupby([pd.Grouper(level=program.idx_field), 
            pd.Grouper(level=program.date_field, freq='Y')] #Summarize by year to make search faster
        ).sum()

        state_bars = program_data.groupby(program.date_field)[["State Actions", "Federal Actions"]].sum() #Sum the counted State/EPA actions
        state_bars = state_bars.resample("Y").sum()
        state_bars.index = state_bars.index.strftime('%Y')
        #program_data = program_data.groupby([program.idx_field])[[program.agg_col]].agg(program.agg_type) # Count of inspections etc. for each facility
        stacked=True

# in the joining function
if program.agg_type == "sum":
    data = fac[1] # the data we want... e.g. annual emissions # HOW TO HANDLE COUNT SITUATIONS WITH STATE/FEDERAL
else:
    state = fac[1]
    federal = fac[2]
if sum:
    e.update({})
else:
    e.update({"State Actions": state, "Federal Actions": federal})

# in the bar chart cell:    
else (if count):
    local_bars = district_time_data.groupby(program.date_field)[["State Actions", "Federal Actions"]].sum() # Sum of total emissions, violations, etc. in the district for the whole year
    local_bars = local_bars.resample('Y').sum() # Sum again in case it wasn't summed the first time...
    local_bars.index = local_bars.index.strftime('%Y')
    
    time_data[program.agg_col] = time_data['State Actions'] + time_data['Federal Actions']
    district_program_data=time_data.groupby(["DFR_URL","FAC_LAT","FAC_LONG","FAC_NAME","FAC_PERCENT_MINORITY", "Index"])[[program.agg_col]].sum()
    district_program_data.reset_index(inplace=True)
    tgdf = geopandas.GeoDataFrame(
        district_program_data, crs= "EPSG:4326", geometry=geopandas.points_from_xy(district_program_data["FAC_LONG"], district_program_data["FAC_LAT"]))
    district_program_data = geopandas.sjoin(tgdf, geo_json_data, how="inner", op='intersects')


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


     # # Look through all the facilities in my area and program and get supplemental echo_data info
    # if (program_data is None): # Handle no data
    #     print("Sorry, we don't have data for this program! That could be an error on our part, or ECHO's, or because the data type doesn't apply to this area.")
    # else:
    #     for fac in program_data.itertuples():
    #         fac_id = fac.Index # Use the Index
    #         reg_id = key[fac_id] # Look up this facility's Registry ID through its Program ID
    #         try:
    #             e=echo_data.loc[echo_data.index==reg_id].copy()[['FAC_NAME', 'FAC_LAT', 'FAC_LONG', 'DFR_URL', 'FAC_PERCENT_MINORITY']].to_dict('index')
    #             e = e[reg_id] # remove indexer
    #             p =  fac._asdict() #split id and year?
    #             e.update(p)
    #             my_prog_data.append(e)
    #         except KeyError:
    #             # The facility wasn't found in the program data.
    #             no_data_ids.append( fac.Index )



# Create a DataSet object for each of the programs we track.  
# Initialize each one with the information it needs to do its query
# of the database.
# Store the DataSet objects in a dictionary with keys being the
# friendly names of the program, which will be used in selection
# widgets.

# In the following line, 'from DataSet' refers to the file DataSet.py
# while 'import DataSet' refers to the DataSet class within DataSet.py.

from ECHO_modules.DataSet import DataSet

def make_data_sets():
    data_sets = {}
    
    ds = DataSet( name='RCRA Violations', idx_field='ID_NUMBER', 
                    table_name='RCRA_VIOLATIONS', echo_type="RCRA",
                    date_field='DATE_VIOLATION_DETERMINED', date_format='%m/%d/%Y', agg_type = "count", agg_col="VIOL_DETERMINED_BY_AGENCY", unit="violations") # For possible later use in assessing state v federal 
    data_sets[ ds.name ] = ds
    ds = DataSet( name='RCRA Inspections', idx_field='ID_NUMBER', 
                    table_name='RCRA_EVALUATIONS', echo_type="RCRA",
                    date_field='EVALUATION_START_DATE', date_format='%m/%d/%Y', agg_type = "count", agg_col="EVALUATION_AGENCY", unit="inspections") # For possible later use in assessing state v federal 
    data_sets[ ds.name ] = ds
    ds = DataSet( name='RCRA Enforcements',  echo_type="RCRA",
                    table_name='RCRA_ENFORCEMENTS', idx_field='ID_NUMBER', 
                    date_field='ENFORCEMENT_ACTION_DATE', date_format='%m/%d/%Y', agg_type = "count", agg_col="ENFORCEMENT_AGENCY", unit="enforcement actions") # For possible later use in assessing state v federal 
    data_sets[ ds.name ] = ds
    ds = DataSet( name='CAA Violations',  echo_type="AIR",
                    table_name='ICIS-AIR_VIOLATION_HISTORY', idx_field='pgm_sys_id', 
                    date_field='HPV_DAYZERO_DATE', date_format='%m-%d-%Y', agg_type = "count", agg_col="AGENCY_TYPE_DESC", unit="violations") # For possible later use in assessing state v federal 
    data_sets[ ds.name ] = ds
    ds = DataSet( name='CAA Penalties', echo_type="AIR",
                    table_name='ICIS-AIR_FORMAL_ACTIONS', idx_field='pgm_sys_id',
                    date_field='SETTLEMENT_ENTERED_DATE', date_format='%m/%d/%Y' , agg_type = "sum", agg_col="PENALTY_AMOUNT", unit="dollars")
    data_sets[ ds.name ] = ds
    ds = DataSet( name='CAA Insepections', echo_type="AIR",
                    table_name='ICIS-AIR_FCES_PCES', idx_field='PGM_SYS_ID',
                    date_field='ACTUAL_END_DATE', date_format='%m-%d-%Y' , agg_type = "count", agg_col="STATE_EPA_FLAG", unit="inspections") # For possible later use in assessing state v federal 
    data_sets[ ds.name ] = ds
    my_sql = "select * from `POLL_RPT_COMBINED_EMISSIONS` " + \
                " where PGM_SYS_ACRNM = 'E-GGRT' and REGISTRY_ID in "
    ds = DataSet( name='Greenhouse Gas Emissions', echo_type="GHG",
                    table_name='POLL_RPT_COMBINED_EMISSIONS', idx_field='REGISTRY_ID',
                    date_field='REPORTING_YEAR', date_format='%Y', sql = my_sql, agg_type = "sum", agg_col="ANNUAL_EMISSION", unit="metric tons of CO2 equivalent")
    data_sets[ ds.name ] = ds
    my_sql = "select * from `POLL_RPT_COMBINED_EMISSIONS` " + \
                 " where PGM_SYS_ID = 'TRIS' and REGISTRY_ID in "
    ds = DataSet( name='Toxic Releases Inventory - Air', echo_type="TRI",
                    table_name='POLL_RPT_COMBINED_EMISSIONS', idx_field='REGISTRY_ID',
                    date_field='REPORTING_YEAR', date_format='%Y', sql = my_sql, agg_type = "sum", agg_col="ANNUAL_EMISSION", unit="pounds")
    data_sets[ ds.name ] = ds
    ds = DataSet( name='CWA Violations', echo_type="NPDES",
                    table_name='NPDES_QNCR_HISTORY', idx_field='NPDES_ID',
                    date_field='YEARQTR', date_format='%Y' , agg_type = "sum", agg_col="NUME90Q", unit="effluent violations")
    data_sets[ ds.name ] = ds
    ds = DataSet( name='CWA Inspections', echo_type="NPDES",
                    table_name='NPDES_INSPECTIONS', idx_field='NPDES_ID',
                    date_field='ACTUAL_END_DATE', date_format='%m/%d/%Y', agg_type = "count", agg_col="STATE_EPA_FLAG", unit="inspections") # For possible later use in assessing state v federal 
    data_sets[ ds.name ] = ds
    ds = DataSet( name='CWA Enforcements', echo_type="NPDES",
                    table_name='NPDES_FORMAL_ENFORCEMENT_ACTIONS', idx_field='NPDES_ID',
                    date_field='SETTLEMENT_ENTERED_DATE', date_format='%m/%d/%Y', agg_type = "count", agg_col="AGENCY", unit="enforcement actions") # For possible later use in assessing state v federal 
    data_sets[ ds.name ] = ds

    return data_sets