 [![Code of Conduct](https://img.shields.io/badge/%E2%9D%A4-code%20of%20conduct-blue.svg?style=flat)](https://github.com/edgi-govdata-archiving/overview/blob/master/CONDUCT.md)

# ECHO-Sunrise
Partnership between EDGI's Environmental Enforcement Watch and Sunrise Boston hubs exploring environmental violations, penalties, and injustices in Massachusetts, using EDGI's mirror of the EPA's ECHO database and a customized, Jupyter Notebook-based analysis.

## Goals and requirements of notebook
* The issues we want to cover: air pollution, water discharges, waste disposal, and greenhouse gas (GHG) emissions
* **Geographies**: For Mass., look at Congressional Districts, State House districts, and municipalities
* **Timeframe**: This was not explicitly discussed in our meeting, but the easiest and potentially most salient thing to do is look at the past three years - 12 quarters - worth of data. That timeframe has direct relevance to Congressional races - we could even look at just the past year and a half. It is also a good place to start because then we only need to pull from the ECHO_EXPORTER table.
* **Metrics**: 
  * What are the three "worst offenders" per geography?
  * Try to come up with other metrics and ultimately a sort of "model" or "algorithm" that identifies specific census districts or other geographies of concern. This might include population density, percent minority in surrounding neighborhoods, proximity to prisons/jails/detention centers (note gaps here), relevant Congressional or State House races, etc.
* **Goal**: 
 * Point out areas for further research and enable Sunrise to raise awareness around individual local facilities, (non) enforcement and compliance trends.

## Outline of the notebook
* Load helper code
  * `ECHO-modules/data_sets.py` for creating data classes
  * `ECHO-Geo/` ... GeoJSONs reprsenting different MA geographies. This is a repo that will need to be created.
  * Other standard code, especially folium
* Load map of MA showing different possible geographies (Note: also maybe load all 38000+ ECHO_EXPORTER facilities in MA using folium's FastClusterMarker. See: https://github.com/edgi-govdata-archiving/ECHO-Cross-Program/issues/42)
  * Congressional Districts (See: https://github.com/edgi-govdata-archiving/ECHO-Cross-Program/issues/43)
  * County
  * Watershed?
  * Zip
  * Census Tract
  * Municipality
  * State House Districts
* Selections
  * Users select the geography they want to explore - that is, how they want to aggregate facility information
  * Users select the data they want to explore
    * **Cross-Program**
     - Past 3 years: Overall compliance? Or, for each facility, # of violations / # of regulated programs?
     - Past 5 years: Total number of enforcement actions against facilities
     - Past 5 years: Total $ in penalties
    * **Air**
     - Past 3 years: Compliance (# of quarters in significant non-compliance or in violation)
     - 2018: Emissions. Use `REGISTRY_ID` to look up 2018 reported emissions of criteria pollutants from `POLL_RPT_COMBINED_EMISSIONS` table
    * **GHG**
     - 2018: Tonnes of CO2 equivalent reported released
     - This ^^^ translated into the social cost of carbon ($)
    * **Water**
     - Past 3 years: Compliance (# of quarters in significant non-compliance or in violation)
     - 2018: Use `WATER_IDS` to look up 2018 reported discharges for key pollutants. Would need to get the FY 2018 version of NPDES_DMR table, which would be a huge file.
    * **Drinking water**
     - ?
    * **Waste**
     - Past 3 years: Compliance
* Reports
   * **1: Where are the worst offenders?**
     - Aggregate data selected above, create new map, and shade selected geography by the selected variable e.g. % of facilities in non-compliance.
     - Report the **three** geographies (Congressional Districts, zip codes, etc.) that are worst for the selected variable.
   * **2: What does this mean for EJ?**
     - Foucsing on the three geographies that are worst, create a new map that shows all facilities in these geographies, shaded by `FAC_PERCENT_MINORITY` or percent in poverty or `Over80Count` or some combination of the two (see here for sequential x sequential bivariate colour schemes: https://www.axismaps.com/guide/multivariate/bivariate-choropleth/#:~:text=There%20are%20two%20kinds%20of,or%20with%20rankable%20categorical%20data) and sized by the variable of interest (# of non-compliance quarters, penalties, emissions, etc.) See here for an example map: https://github.com/edgi-govdata-archiving/Environmental-Enforcement-Watch/issues/29
     - Create and show a scatter plot where, for these geographies, the x-axis is `FAC_PERCENT_MINORITY` and the y-axis is percent in poverty or `Over80Count` and facilities are plotted accordingly. Average/median also plotted. 
     - A challenge is getting percent in poverty information - this is not available directly in ECHO_EXPORTER. `Over80Count` (or `Over80CountUs`) is a field from EJScreen that ECHO pulls in. It is a summary of the number of EJ indices that the census block group the facility is in registers in the 80th percentile nationally. So, if a facility was in a census block group that was among the top 20% block groups nationally when it came to air toxics cancer risk, it would get a 1. If it was also in the top 20% for PM, then its value would be 2. See the complete list of indices here: https://echo.epa.gov/tools/web-services/detailed-facility-report#/Detailed%20Facility%20Report/get_dfr_rest_services_get_ejscreen_indexes As far as I can tell, this is only available through the ECHO API. However, we could add it to the SBU database from here: ftp://newftp.epa.gov/EJSCREEN/2019/
   * **3: Prisons**
     - TBD in consultation with Nick Shapiro's Carceral Ecologies project. Use NACIS codes to show prisons, jails, and detention centers in the three worst geographies, and the facilities within a certain distance (e.g. 3 miles) of them. See here: https://geopandas.org/geometric_manipulations.html
* Export
  * Users can export:
    - All ECHO_EXPORTER data for MA (include lat/lon columns so data can be mapped)
    - Summarized table from Report 1
    - Chart from Report 2
    - Info on specific prison-proximate facilities from Report 3
  
Other considerations
* Report as much as possible when there are data gaps! For instance, for 50 facilities, EPA has entered the county name as "Metropolitan Boston." There is no such county!!! That means those 50 facilities aren't going to get picked up in our analysis by county.
* If we decide to work with EJScreen, we should understand how the indices were calculated.

## How to start contributing to this repo
* Contact @ericnost, @crgreenleaf, or other contributors listed below!
* Slack channel - #eew_coordination
* Check out our [good-first-issue](https://github.com/edgi-govdata-archiving/ECHO-Sunrise/labels/good%20first%20issue)s label

## Using Github Issues
* An issue is something specific and resolvable, like a task or a question
* Github Issues can be accessed from the Issues tab
* Usually, the first message in the Issue says what needs resolving and provides any supporting information. Anyone can then comment on the issue to add to the conversation
* Github issues are typically public but not formal—somewhere between an email and a chat message. It is ok to jump in to a conversation in a Github issue if you have something to add
* If you are working on an issue, it is good form to assign yourself to the issue, to comment and say so, and to provide updates (as comments), especially if you are blocked, have a question, or don't have time to work on it anymore
* By default, anyone who has contributed to or been tagged with their Github handle in that issue will receive notifications about updates to that issue. You can see your notifications by clicking on the bell icon in the top right of any Github page (if you're signed in), so this is a good way to stay engaged with a conversation

## Contributors
| Name | Github | Org | 
| ------|--------|--|
| Sara Wylie | @saraannwylie | EEW |
| Lourdes Vera | @lourdesvera | EEW |
| Casey Greenleaf | @crgreenleaf | EEW |
| Steve Hansen | @shansen5 | EEW |
| Eric Nost | @ericnost  | EEW |
| Kelsey Breseman | @Frijol | EEW |
| Dietmar Offenhuber | @dietoff | EEW |
| Gaby Trudo| @gabrielletrudo | EEW |

---

## License & Copyright

Copyright (C) <year> Environmental Data and Governance Initiative (EDGI)
This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 3.0.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

See the [`LICENSE`](/LICENSE) file for details.
