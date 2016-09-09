"""
todo:
    report data by 
    community area
    for the following:
        - racial majority (acs B03002)
        - median income (acs ? ... and do we need to go by poverty rate)
        - unemployment rate (acs ? see unemployment story)
        - education - hs diploma
        - vacant lots (data portal)
        - crime - property and violent (data portal, per 100K)


I'm still figuring out how to organize research projects.
This is not the way.
"""
import csv, json, requests, subprocess
from chi_census.comm_area_data import init
from geojson import Feature, FeatureCollection, MultiPolygon


### START CONFIG ###
output_dir              = 'source_data/'
vizdata_dir             = 'viz_data/'
vizdata_file_name       = 'data.geojson'
vizdata_file_path       = vizdata_dir + vizdata_file_name
vizdata_file            = open(vizdata_file_path,'w')
comm_area_boundary_ep   = 'https://data.cityofchicago.org/resource/igwz-8jzy.json' 
comm_area_boundary_file = 'source_data/comm_area_boundaries.json'
census_tables           = ['B03002','B15003','B25002','C17002','B23025']
refresh_data            = False # set to False if data already collected
crime_api_endpoint      = 'https://data.cityofchicago.org/resource/6zsd-86xi.json' # broken
crime_filename          = 'source_data/crime.csv'
simplification_level    = ".0005"
### END CONFIG   ### 


def run_raw_reports():
    if not refresh_data:
        return
    get_crime_data()
    for table in census_tables:
        init(table_arg=table,output_dir_arg=output_dir)


def get_comm_areas():
    if refresh_data:
        response = requests.get(comm_area_boundary_ep)
        j = response.json()
        wf = open(comm_area_boundary_file,'w')
        json.dump(j,wf)
        wf.close()
    return json.load(open(comm_area_boundary_file))


def build_geojson():
    js  = get_comm_areas()
    js  = bind_crime_to_json(js)
    js  = bind_race_to_json(js)
    js  = bind_edu_att_to_json(js)
    js  = bind_unemployment_to_json(js)
    js  = bind_vacancy_to_json(js)
    js  = bind_poverty_to_json(js)
    gjs = geojsonify(js)
    json.dump(gjs,vizdata_file)
    vizdata_file.close()
    simplify_json()


def simplify_json():
    subprocess.call(
                    [
                     "ogr2ogr",
                     "-f","GeoJSON",
                     "-simplify",simplification_level,
                     vizdata_file_path, # output file
                     vizdata_file_path, # input file
                    ]
                   )


def get_crime_data():
    # note that I never got the json because it's an associative array 
    if refresh_data:
        response = requests.get(crime_api_endpoint)
        j = response.json()
        wf = open(crime_filename)
        wf.write(j)
        wf.close()


def parse_crime_data():
    all_crime_types = ['ARSON', 'ASSAULT', 'BATTERY', 'BURGLARY', 'CONCEALED CARRY LICENSE VIOLATION', 'CRIM SEXUAL ASSAULT', 'CRIMINAL DAMAGE', 'CRIMINAL TRESPASS', 'DECEPTIVE PRACTICE', 'GAMBLING', 'HOMICIDE', 'HUMAN TRAFFICKING', 'INTERFERENCE WITH PUBLIC OFFICER', 'INTIMIDATION', 'KIDNAPPING', 'LIQUOR LAW VIOLATION', 'MOTOR VEHICLE THEFT', 'NARCOTICS', 'NON - CRIMINAL', 'NON-CRIMINAL', 'NON-CRIMINAL (SUBJECT SPECIFIED)', 'OBSCENITY', 'OFFENSE INVOLVING CHILDREN', 'OTHER NARCOTIC VIOLATION', 'OTHER OFFENSE', 'PROSTITUTION', 'PUBLIC INDECENCY', 'PUBLIC PEACE VIOLATION', 'ROBBERY', 'SEX OFFENSE', 'STALKING', 'THEFT', 'WEAPONS VIOLATION']
    violent_crime_types = ['ASSAULT', 'BATTERY', 'CRIM SEXUAL ASSAULT', 'HOMICIDE', 'HUMAN TRAFFICKING', 'INTIMIDATION', 'KIDNAPPING', 'ROBBERY', 'SEX OFFENSE', 'STALKING']
    property_crime_types = ['ARSON', 'BURGLARY', 'CRIMINAL DAMAGE', 'CRIMINAL TRESPASS', 'DECEPTIVE PRACTICE', 'MOTOR VEHICLE THEFT', 'THEFT']
    get_crime_data()
    # data = json.load(open(crime_filename,'r'))
    # import ipdb; ipdb.set_trace()
    # note that i'm using csv but should use json because apis
    crime_data = dict()
    """
    ### sample data ###
    {'community area':
                      {
                       'violent'    : 0,
                       'property'   : 0,
                       'pop'        : 0,
                      }  
    """
    for row in csv.DictReader(open(crime_filename)):
        # add community area to crime_data if necessary
        ca = row['Community Area']
        if ca == "0":
            continue
        try:
            if ca not in crime_data:
                crime_data[ca] = {'violent':0,'property':0}
        except Exception, e:
            import ipdb; ipdb.set_trace()
        pt = row['Primary Type']
        if pt in violent_crime_types:
            crime_data[ca]['violent'] += 1
        elif pt in property_crime_types:
            crime_data[ca]['property'] += 1
        else:
            pass
    if refresh_data: 
        init(table_arg='B01003',output_dir_arg=output_dir) 
    for row in csv.DictReader(open(output_dir + '/B01003_moe.csv')):
        crime_data[row['Community Area ID']]['pop'] = row['B01003_001E: Total']
    for caid in crime_data:
        crime_data[caid]['property_rate'] = int(crime_data[caid]['property'] / float(crime_data[caid]['pop']) * 100000)
        crime_data[caid]['violent_rate'] = int(crime_data[caid]['violent'] / float(crime_data[caid]['pop']) * 100000)
    return crime_data


def bind_crime_to_json(js):
    try:
        crime_data = parse_crime_data()
        for comm_area_id in crime_data:
            # find the json element corresponding with this comm area
            j_comm_area = [x for x in js['features'] if x['properties']['area_numbe'] == comm_area_id][0]
            j_comm_area['property_crime_rate'] = crime_data[comm_area_id]['property_rate']
            j_comm_area['violent_crime_rate'] = crime_data[comm_area_id]['violent_rate']
        return js
    except Exception,e:
        import ipdb; ipdb.set_trace()


def bind_race_to_json(js):
    """
    ugh i hate myself for this
    """
    file_path = 'source_data/B03002_moe.csv'
    c = [x for x in csv.DictReader(open(file_path))]
    for row in c:
        # find the json element corresponding with this comm area
        j_comm_area = [x for x in js['features'] if x['properties']['area_numbe'] == row['Community Area ID']][0]
        j_comm_area['racial_majority'] = define_racial_majority(row)
    return js


def define_racial_majority(row):
    total = row['B03002_001E: Total:']
    white = row['B03002_003E: Not Hispanic or Latino:!!White alone']
    black = row['B03002_004E: Not Hispanic or Latino:!!Black or African American alone']
    hisp  = row['B03002_012E: Hispanic or Latino:']

    if get_pct_of_total(white,total) > 0.5:
        return 'White'
    elif get_pct_of_total(black,total) > 0.5:
        return 'Black'
    elif get_pct_of_total(hisp,total) > 0.5:
        return 'Hispanic'
    else:
        return 'Mixed'


def get_pct_of_total(string,total):
    try:
        return round(int(string)/float(int(total)),2)
    except:
        return 0


def bind_edu_att_to_json(js):
    for row in csv.DictReader(open(output_dir + 'B15003_moe.csv')):
        j_comm_area = [x for x in js['features'] if x['properties']['area_numbe'] == row['Community Area ID']][0]
        j_comm_area['hs_diploma_or_less'] = calc_hs_only(row)
    return js


def calc_hs_only(row):
    total = row['B15003_001E: Total:']
    hs_or_less_fields = [
                         'B15003_002E: No schooling completed',
                         'B15003_003E: Nursery school',
                         'B15003_004E: Kindergarten',
                         'B15003_005E: 1st grade',
                         'B15003_006E: 2nd grade',
                         'B15003_007E: 3rd grade',
                         'B15003_008E: 4th grade',
                         'B15003_009E: 5th grade',
                         'B15003_010E: 6th grade',
                         'B15003_011E: 7th grade',
                         'B15003_012E: 8th grade',
                         'B15003_013E: 9th grade',
                         'B15003_014E: 10th grade',
                         'B15003_015E: 11th grade',
                         'B15003_016E: 12th grade, no diploma',
                         'B15003_017E: Regular high school diploma',
                         'B15003_018E: GED or alternative credential',
                        ]
    try:
        countables = [row[x] for x in hs_or_less_fields if row[x] != 'NA']
        return round(sum([int(x) for x in countables])/float(total),2)
    except Exception, e:
        import ipdb; ipdb.set_trace()


def bind_unemployment_to_json(js):
    for row in csv.DictReader(open(output_dir + 'B23025_moe.csv')):
        j_comm_area = [x for x in js['features'] if x['properties']['area_numbe'] == row['Community Area ID']][0]
        j_comm_area['unemployment'] = calc_unemployment(row)
    return js


def calc_unemployment(row):
    try:
        total      = row['B23025_003E: In labor force:!!Civilian labor force:']
        unemployed = row['B23025_005E: In labor force:!!Civilian labor force:!!Unemployed']
        rate = float(unemployed)/float(total)
        return rate
    except Exception, e:
        import ipdb; ipdb.set_trace()


def bind_vacancy_to_json(js):
    for row in csv.DictReader(open(output_dir + 'B25002_moe.csv')):
        j_comm_area = [x for x in js['features'] if x['properties']['area_numbe'] == row['Community Area ID']][0]
        j_comm_area['vacancy'] = calc_vacancy(row)
    return js


def calc_vacancy(row):
    try:
        total      = row['B25002_001E: Total:']
        vacant     = row['B25002_003E: Vacant']
        rate       = round(int(vacant)/float(total),2)
        return rate
    except Exception, e:
        import ipdb; ipdb.set_trace()


def bind_poverty_to_json(js):
    for row in csv.DictReader(open(output_dir + 'C17002_moe.csv')):
        j_comm_area = [x for x in js['features'] if x['properties']['area_numbe'] == row['Community Area ID']][0]
        j_comm_area['poverty'] = calc_poverty(row)
    return js


def calc_poverty(row):
    try:
        total      = row['C17002_001E: Total:']
        under_pov  = sum(int(x) for x in [row['C17002_002E: Under .50'],row['C17002_003E: .50 to .99']] if x != 'NA')
        rate       = round(int(under_pov)/float(total),2)
        return rate
    except Exception, e:
        import ipdb; ipdb.set_trace()


def init_research():
    run_raw_reports()
    build_geojson()


def geojsonify(js):
    features = []
    for ca in js['features']:
        geometry   = MultiPolygon(coordinates = ca['geometry']['coordinates'])
        cap        = ca['properties']
        try:
            properties = {
                      "community"         : cap["community"],
                      "area_numbe"        : cap["area_numbe"],
                      "hs_diploma_or_less": ca["hs_diploma_or_less"],
                      "racial_majority"   : ca["racial_majority"],
                      "unemployment"      : ca["unemployment"],
                      "vacancy"           : ca["vacancy"],
                      "poverty"           : ca["poverty"],
                      "property"          : ca["property_crime_rate"],
                      "violent"           : ca["violent_crime_rate"],
                     }
        except Exception, e:
            import ipdb; ipdb.set_trace()
        feature    = Feature(
                             geometry   = geometry,
                             properties = properties
                            )
        features.append(feature)
    return FeatureCollection(features)
    


# init the census calls
# read the files in
# compile them in json
# add shapes?
# write as d3-compliant json


if __name__ == '__main__':
    init_research()
