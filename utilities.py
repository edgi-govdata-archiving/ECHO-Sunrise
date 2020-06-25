import folium
from folium.plugins import FastMarkerCluster

def get_program_data(echo_data, program, program_data):
    key=dict() # Create a way to look up Registry IDs in ECHO_EXPORTER later

    # We need to provide a custom list of program ids for some programs.
    if ( program.name == "Air Inspections" or program.name == "Air Enforcements" ):
        # The REGISTRY_ID field is the index of the echo_data
        registry_ids = echo_data[echo_data['AIR_FLAG'] == 'Y'].index.values
        key = { i : i for i in registry_ids }
        program_data = program.get_data( ee_ids=registry_ids )
    elif ( program.name == "Combined Air Emissions" ):
        ghg_registry_ids = echo_data[echo_data['GHG_FLAG'] == 'Y'].index.values
        tri_registry_ids = echo_data[echo_data['TRI_FLAG'] == 'Y'].index.values
        id_set = np.union1d( ghg_registry_ids, tri_registry_ids )
        registry_ids = list(id_set)
        program_data = program.get_data( ee_ids=registry_ids )
        key = { i : i for i in registry_ids }
    elif ( program.name == "Greenhouse Gases" or program.name == "Toxic Releases" ):
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

    # Find the facility that matches the program data, by REGISTRY_ID.  
    # Add lat and lon, facility name and REGISTRY_ID as fac_registry_id. 
    # (Note: not adding REGISTRY_ID right now as it is sometimes interpreted as an int and that messes with the charts...)

    my_prog_data = []
    no_data_ids = []

    # Look through all the facilities in my area and program and get supplemental echo_data info
    if (program_data is None): # Handle no data
        print("Sorry, we don't have data for this program! That could be an error on our part, or ECHO's, or because the data type doesn't apply to this area.")
    else:
        for fac in program_data.itertuples():
            fac_id = fac.Index
            reg_id = key[fac_id] # Look up this facility's Registry ID through its Program ID
            try:
                e=echo_data.loc[echo_data.index==reg_id].copy()[['FAC_NAME', 'FAC_LAT', 'FAC_LONG', 'DFR_URL']].to_dict('index')
                e = e[reg_id] # remove indexer
                p =  fac._asdict()
                e.update(p)
                my_prog_data.append(e)
            except KeyError:
                # The facility wasn't found in the program data.
                no_data_ids.append( fac.Index )

    return my_prog_data

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

def mapper_circle(df, a):
    # Initialize the map
    m = folium.Map()

    # Scale
    scale = {0:8, 1:12, 2:16, 3:24}
    
    # Add a clickable marker for each facility
    for index, row in df.iterrows():
        folium.CircleMarker(
            location = [row["FAC_LAT"], row["FAC_LONG"]],
            popup = row["FAC_NAME"] +": " + str(int(row[a])), # + "<p><a href='"+row["DFR_URL"]+"' target='_blank'>Link to ECHO detailed report</a></p>",
            radius = scale[row["quantile"]],
            color = "black",
            weight = 1,
            fill_color = "orange",
            fill_opacity= .4
        ).add_to(m)
        
    bounds = m.get_bounds()
    m.fit_bounds(bounds)

    # Show the map
    return m

def mapper_area(geo_json_data, att_data, g):
    q = att_data['value'].quantile([0, 0.25,0.5,0.75, 1]) # Create a quantile scale. This should put an equal number of geographies in each bin/color.
    m = folium.Map()
    c = folium.Choropleth(
        geo_data = geo_json_data,
        data = att_data,
        columns=['geo', 'value'], key_on='feature.properties.'+g, # Join the geo data and the attribute data on a key id
        fill_color='OrRd',fill_opacity=0.75,line_weight=.5,nan_fill_opacity=.5, nan_fill_color="grey", highlight=True, 
        bins=[q[0.00],q[0.25], q[0.5], q[0.75], q[1.00]],
        legend_name="Value"
    ).add_to(m)

    c.geojson.add_child(
                folium.features.GeoJsonTooltip([g])
            )

    bounds = m.get_bounds()
    m.fit_bounds(bounds)

    return m