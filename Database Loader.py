import arcpy
import os
import shutil
import pandas as pd
import dateutil.parser

changed_files = []
files_for_db = []

no_final_copy = []
filename_error = []

def delete_csv_and_csv_layers():
    ## delete all csv tables in mxd
    for t in arcpy.mapping.ListTableViews(arcpy.mapping.MapDocument("CURRENT")):
        arcpy.Delete_management(t)
        
    ## delete all csv layers in mxd
    for l in arcpy.mapping.ListLayers(arcpy.mapping.MapDocument("CURRENT")):
        if l.name[-4:] == '.csv':
            arcpy.Delete_management(l)
            
            
def print_errors():
    ''' prints out folders without a database copy and files with names that don't meet convention '''
    error = False
    
    if len(no_final_copy) > 0:
        print("Folders without Database Copy:")
        for item in no_final_copy:
            print(item)
        print('\n')
        error = True
    
    if len(filename_error) > 0:
        print("Database Copy files with improper filename:")
        for item in filename_error:
            print(item)
        error = True
        
    if not error:
        print('All Good - No empty database folders or filename errors')
            
            
def add_columns(csv, filename):
    ''' adds Geography and Date fields to CSVs that do not already have them '''
    geo = filename.split('_', 2)[1]
    date = filename.split('_', 2)[2].split('.')[0].replace('_', '/').replace('-', '/')
    
    csv_input = pd.read_csv(csv, engine='python')
    
    changed = False
    
    if 'Date' not in list(csv_input):   
        csv_input['Date'] = date
        changed = True
        
    if 'Geography' not in list(csv_input):   
        csv_input['Geography'] = geo
        changed = True
        
    try:
        dateutil.parser.parse(date)
        
        if changed: 
            changed_files.append(filename)
            csv_input.to_csv(csv, index=False)
    except:
        filename_error.append(filename)


# gather all csvs in folders called "For Database"
for root, dirs, files in os.walk(r"Z:\(G) Geographic Information Systems\GIS SUPPORT\000 - Store Locations", topdown=False):
    for subdir in dirs:
        for root, dirs, files in os.walk(root + '\\' + subdir):
            if root.rsplit('\\')[-1] == 'For Database':
                if len(files) == 1:
                    files_for_db.append(root + '\\' + files[0])
                    if files[0].count('_') not in [2, 4]:
                        filename_error.append(files[0])
                    else:
                        add_columns(r"{}".format(root + '\\' + files[0]), files[0])
                else: 
                    if root.rsplit('\\', 2)[1].split()[0] != '000':
                        no_final_copy.append(root.rsplit('\\', 2)[1])


print_errors()

# put these csvs in "For Store Database" folder
for file in files_for_db:
    shutil.copy(file, r"Z:\(G) Geographic Information Systems\GIS SUPPORT\000 - Store Locations\For Store Database")

# truncate database feature class
arcpy.TruncateTable_management("Retail Store Location Data")

# delete any existing csvs and event layers in map
delete_csv_and_csv_layers()
    
## Add csv event layers for files in "For Store Database" folder
for file in files_for_db:
    file_name = file.rsplit('\\', 1)[-1]
    arcpy.MakeXYEventLayer_management(file, "Longitude", "Latitude", file_name)
      
## put all csv layer files into list    
files_in = [x for x in arcpy.mapping.ListLayers(arcpy.mapping.MapDocument("CURRENT")) if x.name[-4:] == '.csv']

## append csv layer files
arcpy.Append_management(files_in, "Retail Store Location Data", "NO_TEST")

# delete any existing csvs and event layers in map
delete_csv_and_csv_layers()