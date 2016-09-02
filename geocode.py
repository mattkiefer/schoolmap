import requests, csv, json

### START CONFIG ###
input_file_name  = 'source_data/schools.csv'
output_file_name = 'viz_data/geo_schools.csv' 
tamu_api_key     = '058b7ce62ad64541b21d08264187bf72'
response_format  = 'json'
census           = 'false'
not_store        = 'false'
version          = '4.01'
### END CONFIG ###

tamu_base_url       = 'https://geoservices.tamu.edu/Services/Geocode/WebService/GeocoderWebServiceHttpNonParsed_V04_01.aspx?'

input_file          = open(input_file_name)
input_csv           = csv.DictReader(input_file)

output_file         = open(output_file_name,'w')
output_file_headers = input_csv.fieldnames + ['lat','lon']
output_csv          = csv.DictWriter(output_file, output_file_headers)

output_csv.writeheader()

for row in input_csv:
    # set up query
    address           = 'streetAddress=' + row['Address'].replace(' ','%20')
    city              = '&city=Chicago'
    state             = '&state=il'
    api               = '&apikey=' + tamu_api_key
    response_format_q = '&format=' + response_format
    census_q          = '&census=' + census
    not_store_q       = '&notStore=' + not_store
    version_q         = '&version=' + version
    query_string      = tamu_base_url + address + city + state + api + response_format_q + census_q + not_store_q + version_q
    
    # get and parse response
    response      = requests.get(query_string)
    try:
        j_response    = json.loads(response.content)
    except Exception, e:
        print e, query_string
        continue
        import ipdb; ipdb.set_trace()
    output        = j_response['OutputGeocodes']
    if len(output) > 1:
        print 'ambiguous:' + address
        continue
    else:
        output    = output[0]
    geocodes      = output['OutputGeocode']
    latitude      = geocodes['Latitude']
    longitude     = geocodes['Longitude']
    outrow        = row
    outrow['lat'] = latitude
    outrow['lon'] = longitude
    print outrow
    output_csv.writerow(outrow)

