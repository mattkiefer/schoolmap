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
import csv, json, requests
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
census_tables           = ['B03002','B15003']
refresh_data            = False # set to False if data already collected
### END CONFIG   ### 


def run_raw_reports():
    if not refresh_data:
        return
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
    js  = bind_race_to_json(js)
    js  = bind_edu_att_to_json(js)
    gjs = geojsonify(js)
    json.dump(gjs,vizdata_file,indent=4)

    vizdata_file.close()


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
