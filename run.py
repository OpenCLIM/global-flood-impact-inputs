import os
import glob
from glob import glob
import geopandas as gpd
import pandas as pd
import shutil
import math
from geojson import Polygon
from os.path import join, isdir, isfile
from datetime import datetime

def metadata_json(output_path, output_title, output_description, bbox, file_name):
    """
    Generate a metadata json file used to catalogue the outputs of the UDM model on DAFNI
    """

    # Create metadata file
    metadata = f"""{{
      "@context": ["metadata-v1"],
      "@type": "dcat:Dataset",
      "dct:language": "en",
      "dct:title": "{output_title}",
      "dct:description": "{output_description}",
      "dcat:keyword": [
        "UDM"
      ],
      "dct:subject": "Environment",
      "dct:license": {{
        "@type": "LicenseDocument",
        "@id": "https://creativecommons.org/licences/by/4.0/",
        "rdfs:label": null
      }},
      "dct:creator": [{{"@type": "foaf:Organization"}}],
      "dcat:contactPoint": {{
        "@type": "vcard:Organization",
        "vcard:fn": "DAFNI",
        "vcard:hasEmail": "support@dafni.ac.uk"
      }},
      "dct:created": "{datetime.now().isoformat()}Z",
      "dct:PeriodOfTime": {{
        "type": "dct:PeriodOfTime",
        "time:hasBeginning": null,
        "time:hasEnd": null
      }},
      "dafni_version_note": "created",
      "dct:spatial": {{
        "@type": "dct:Location",
        "rdfs:label": null
      }},
      "geojson": {bbox}
    }}
    """

    # write to file
    with open(join(output_path, '%s.json' % file_name), 'w') as f:
        f.write(metadata)
    return

def round_down(val, round_val):
    """Round a value down to the nearst value as set by the round val parameter"""
    return math.floor(val / round_val) * round_val

def round_up(val, round_val):
    """Round a value up to the nearst value as set by the round val parameter"""
    return math.ceil(val / round_val) * round_val

# Set data paths
data_path = os.getenv('DATA','/data')
inputs_path = os.path.join(data_path, 'inputs')
boundary_path = os.path.join(inputs_path, 'boundary')
utm_zone_path = os.path.join(inputs_path, 'utm_zones')
utm_code_path = os.path.join(inputs_path,'utm_codes')
outputs_path = os.path.join(data_path, 'outputs')
if not os.path.exists(outputs_path):
    os.mkdir(outputs_path)
boundary_outputs_path = os.path.join(outputs_path, 'boundary')
if not os.path.exists(boundary_outputs_path):
    os.mkdir(boundary_outputs_path)
parameter_outputs_path = os.path.join(outputs_path, 'parameters')
if not os.path.exists(parameter_outputs_path):
    os.mkdir(parameter_outputs_path)
meta_outputs_path = os.path.join(outputs_path, 'metadata')
if not os.path.exists(meta_outputs_path):
    os.mkdir(meta_outputs_path)

# Read environment variables
year = os.getenv('YEAR')
country = os.getenv('COUNTRY')
projection = os.getenv('PROJECTION')
location = os.getenv('LOCATION')
rainfall_mode = os.getenv('RAINFALL_MODE')
rainfall_total = int(os.getenv('TOTAL_DEPTH'))
duration = int(os.getenv('DURATION'))
open_boundaries = (os.getenv('OPEN_BOUNDARIES'))
permeable_areas = os.getenv('PERMEABLE_AREAS')
roof_storage = float(os.getenv('ROOF_STORAGE'))
post_event_duration = int(os.getenv('POST_EVENT_DURATION'))
output_interval = int(os.getenv('OUTPUT_INTERVAL'))
size = os.getenv('SIZE')  # convert from km to m
x = os.getenv('X')
y = os.getenv('Y')


if size != None:
  size = float(size)*1000

if x != None:
  x = int(x)

if y != None:
  y = int(y)

print(size)

# Unused Parameters for this version of citycat - for further studies these can be incorporated
# baseline = (os.getenv('BASELINE'))
# time_horizon = os.getenv('TIME_HORIZON')
# discharge_parameter = float(os.getenv('DISCHARGE'))
# return_period = int(os.getenv('RETURN_PERIOD'))

# Locate the boundary file and move into the correct output folder
# Rename based on the location of the city of interest
boundary = glob(boundary_path + "/*.*", recursive = True)
src=boundary[0]
print('src:',src)
dst=os.path.join(boundary_outputs_path, location + '.gpkg')
print('dst:',dst)
shutil.copy(src,dst)

boundary_1 = glob(boundary_path + "/*.*", recursive = True)
boundary = gpd.read_file(boundary_1[0])
bbox = boundary.bounds
extents = 1000
left = round_down(bbox.minx,extents)
bottom = round_down(bbox.miny,extents)
right = round_down(bbox.maxx,extents)
top = round_down(bbox.maxy,extents)
geojson = Polygon([[(left,top), (right,top), (right,bottom), (left,bottom)]])

print('projection:',projection)

if projection == '0' :
  print('yes')

  # Read in the UTM shapefile which contains all the geographical zones
  utms_1 = glob(utm_zone_path + "/*.gpkg", recursive = True)
  print('utms:',utms_1)
  utms = gpd.read_file(utms_1[0])

  print('boundary:', boundary.crs)
  print('zones:',utms.crs)

  boundary_crs = boundary.crs
  zones_crs = utms.crs

  # Ensure all of the polygons are defined by the same crs
  boundary.to_crs(epsg=3857, inplace=True)
  utms.to_crs(epsg=3857, inplace=True)

  print('boundary:', boundary.crs)
  print('zones:',utms.crs)

  utm_area = gpd.overlay(boundary, utms, how='intersection')
  utm_area['area'] = utm_area.geometry.area
  utm_area.sort_values(by='area',inplace=True)
  utm_area.drop_duplicates(subset='ZONE',keep='last',inplace=True)
  utm_area.drop(columns=['area'],inplace=True)
  print(utm_area)

  zone = str(int(utm_area.ZONE[0]))
  print('zone:',zone)
  row = utm_area.ROW_[0]
  print('row:',row)  

  number = ord(row)-64
  if number >= 14 :
     projection = '326' + zone
  else:
     projection = '327' + zone

  print('projection:',projection)
  

# Print all of the input parameters to an excel sheet to be read in later
with open(os.path.join(parameter_outputs_path,country + '-' + location + '-' + year +'-parameters.csv'), 'w') as f:
    f.write('PARAMETER,VALUE\n')
    f.write('LOCATION,%s\n' %location)
    f.write('PROJECTION,%s\n' %projection)
    f.write('YEAR,%s\n' %year)
    f.write('RAINFALL_MODE,%s\n' %rainfall_mode)  
    f.write('TOTAL_DEPTH,%s\n' %rainfall_total)
    f.write('DURATION,%s\n' %duration) 
    f.write('OPEN_BOUNDARIES,%s\n' %open_boundaries)
    f.write('PERMEABLE_AREAS,%s\n' %permeable_areas)
    f.write('ROOF_STORAGE,%s\n' %roof_storage)
    f.write('POST_EVENT_DURATION,%s\n' %post_event_duration)
    f.write('OUTPUT_INTERVAL,%s\n' %output_interval)
    f.write('SIZE,%s\n' %size)
    f.write('X,%s\n' %x)
    f.write('Y,%s\n' %y)
    #f.write('BASELINE, %s\n' %baseline)
    #f.write('TIME_HORIZON,%s\n' %time_horizon)
    #f.write('DISCHARGE,%s\n' %discharge_parameter)
    #f.write('RETURN_PERIOD,%s\n' %return_period)


title_for_output = country + ' - ' + location + ' - ' + ' - ' + year

description_for_output_inputs = 'This data shows all of the input data generated to run the CityCat flooding model for the chosen city of ' + location + ' for the year ' + year +'.'
description_for_output_FIM = 'This data shows the flood impact data generated by the CityCat flooding model for the chosen city of ' + location + ' for the year ' + year + '.'
description_for_output_Vis = 'These maps and graphics show flood impact metrics for the chosen city of ' + location + ' for the year ' + year + '.'  
   
# write a metadata file so outputs properly recorded on DAFNI
metadata_json(output_path=meta_outputs_path, output_title=title_for_output+'-inputs', output_description=description_for_output_inputs, bbox=geojson, file_name='metadata_citycat_inputs')

# write a metadata file so inputs properly recorded on DAFNI - for ease of use adds onto info provided for outputs
metadata_json(output_path=meta_outputs_path, output_title=title_for_output+'-output data', output_description=description_for_output_FIM, bbox=geojson, file_name='metadata_FIM_data')

# write a metadata file so outputs properly recorded on DAFNI - for UDM AND CityCat outputs
metadata_json(output_path=meta_outputs_path, output_title=title_for_output+'-output graphics', output_description=description_for_output_Vis, bbox=geojson, file_name='metadata_FIM_graphics')
