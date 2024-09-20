import os
import glob
from glob import glob
import geopandas as gpd
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
country = os.getenv('COUNTRY')
projection = os.getenv('PROJECTION')
location = os.getenv('LOCATION')

# Locate the boundary file and identify the bounding box limits
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


# Ensure all of the polygons are defined by the same crs
boundary.to_crs(epsg=projection, inplace=True)
print('new boundary crs:',boundary.crs)

print(boundary.head())
if 'fid' in boundary.columns:
  boundary['fid'] = boundary['fid'].astype('int64')

# Print to a gpkg file
boundary.to_file(os.path.join(boundary_outputs_path, location + '.gpkg'),driver='GPKG')#,index=False)

# Print all of the input parameters to an excel sheet to be read in later
with open(os.path.join(parameter_outputs_path,country + '-' + location +'-parameters.csv'), 'w') as f:
    f.write('PARAMETER,VALUE\n')
    f.write('COUNTRY,%s\n' %country)
    f.write('LOCATION,%s\n' %location)
    f.write('PROJECTION,%s\n' %projection)

# Creating the title for each model output
title_for_output_inputs = location + ' input_model'
title_for_output_ufg = location + ' urban fabric results'
title_for_output_green_areas = location + ' existing greenspaces'
title_for_output_buildings = location + ' existing buildings'
title_for_output_dtm = location + ' digital terrain data'
title_for_output_udm_citycat = location + ' new urban form'
title_for_output_citycat = location + ' CityCAT results'
title_for_output_impact = location + ' flood impact results'
title_for_output_visualisation = location + ' maps'

# Defining the description for each model output
description_for_output_inputs = 'This csv includes all the parameters used to run the Urban Flooding Impact Assessment Workflow for ' + location + '.'
description_for_output_ufg = 'Spatial footprints of the new urban form for ' + location +'. This data includes housing footprints, gardens and new roads.'
description_for_output_green_areas = 'Greenspace data for ' + location + ' based on the current (2017) urban form.'  
description_for_output_buildings = 'Building data for ' + location  +' based on the current (2017) urban form.'
description_for_output_dtm = 'The digital terrain data for ' + location + '.'
description_for_output_udm_citycat = 'This data presents the new urban form for ' + location + '. New urban developments, houses, gardens and roads are merged with the current urban form.'  
description_for_output_citycat = 'Outputs from the CityCAT model for ' + location +'.'
description_for_output_impact = 'This data shows the flood impact data generated by the CityCat flooding model for ' + location +'.'
description_for_output_visualisation = 'These maps and graphics show flood impact metrics for ' + location +'.'  
   
# write a metadata file so outputs properly recorded on DAFNI
metadata_json(output_path=meta_outputs_path, output_title=title_for_output_inputs, output_description=description_for_output_inputs, bbox=geojson, file_name='metadata_inputs')
metadata_json(output_path=meta_outputs_path, output_title=title_for_output_ufg, output_description=description_for_output_ufg, bbox=geojson, file_name='metadata_ufg')
metadata_json(output_path=meta_outputs_path, output_title=title_for_output_green_areas, output_description=description_for_output_green_areas, bbox=geojson, file_name='metadata_green_areas')
metadata_json(output_path=meta_outputs_path, output_title=title_for_output_buildings, output_description=description_for_output_buildings, bbox=geojson, file_name='metadata_buildings')
metadata_json(output_path=meta_outputs_path, output_title=title_for_output_dtm, output_description=description_for_output_dtm, bbox=geojson, file_name='metadata_dtm')
metadata_json(output_path=meta_outputs_path, output_title=title_for_output_udm_citycat, output_description=description_for_output_udm_citycat, bbox=geojson, file_name='metadata_udm_citycat')
metadata_json(output_path=meta_outputs_path, output_title=title_for_output_citycat, output_description=description_for_output_citycat, bbox=geojson, file_name='metadata_citycat')
metadata_json(output_path=meta_outputs_path, output_title=title_for_output_impact, output_description=description_for_output_impact, bbox=geojson, file_name='metadata_impact')
metadata_json(output_path=meta_outputs_path, output_title=title_for_output_visualisation, output_description=description_for_output_visualisation, bbox=geojson, file_name='metadata_visualisation')
