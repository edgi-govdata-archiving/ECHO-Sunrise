import folium
from folium.plugins import FastMarkerCluster

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