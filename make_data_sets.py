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
    
    ds = DataSet( name='Air Violations',  echo_type="AIR",
                    table_name='ICIS-AIR_VIOLATION_HISTORY', idx_field='PGM_SYS_ID', 
                    date_field='HPV_DAYZERO_DATE', date_format='%m-%d-%Y' )
    data_sets[ ds.name ] = ds
    ds = DataSet( name='Air Compliance', echo_type="AIR",
                    table_name='ICIS-AIR_FCES_PCES', idx_field='PGM_SYS_ID',
                    date_field='ACTUAL_END_DATE', date_format='%m-%d-%Y' )
    data_sets[ ds.name ] = ds
    ds = DataSet( name='Combined Air Emissions', echo_type=["GHG","TRI"],
                    table_name='POLL_RPT_COMBINED_EMISSIONS', idx_field='REGISTRY_ID',
                    date_field='REPORTING_YEAR', date_format='%Y' )
    data_sets[ ds.name ] = ds
    my_sql = "select * from `POLL_RPT_COMBINED_EMISSIONS` " + \
                " where PGM_SYS_ACRNM = 'E-GGRT' and REGISTRY_ID in "
    ds = DataSet( name='Greenhouse Gases', echo_type="GHG",
                    table_name='POLL_RPT_COMBINED_EMISSIONS', idx_field='REGISTRY_ID',
                    date_field='REPORTING_YEAR', date_format='%Y', sql = my_sql )
    data_sets[ ds.name ] = ds
    my_sql = "select * from `POLL_RPT_COMBINED_EMISSIONS` " + \
                " where PGM_SYS_ACRNM = 'TRIS' and REGISTRY_ID in "
    ds = DataSet( name='Toxic Releases', echo_type="TRI",
                    table_name='POLL_RPT_COMBINED_EMISSIONS', idx_field='REGISTRY_ID',
                    date_field='REPORTING_YEAR', date_format='%Y', sql = my_sql )
    data_sets[ ds.name ] = ds

    return data_sets