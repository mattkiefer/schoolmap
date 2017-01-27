import csv, json, locale, re
from geojson import Feature, FeatureCollection, Point 


### START CONFIG ###
infile_path = 'closed_schools_data.csv'
outfile_path = 'geo_schools.geojson'
### END CONFIG ###


infile = open(infile_path)
incsv = [x for x in csv.DictReader(infile)]

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')


def geojsonify(schools_list):
    """
    takes list of dicts
    and returns geojson
    """
    features = []
    for school in schools_list:
        point = Point(coordinates=(float(school['lon']),float(school['lat'])))
        properties = {
                      'slug': slugify(school['closed_school']),
                      'address': school['address'],
                      'name': school['closed_school'],
                      'link': linkify(school['closed_school']),
                      'comm_area': school['community_area'],
                      'status': school['status'],
                      'usage': school['usage'],
                      'sale_doc': doc_url(school['sale_doc']),
                      'repurpose_doc': doc_url(school['repurpose_doc']),
                      'alderman': school['alderman'],
                      'sale_date': datify(school['sale_date']),
                      'buyer': buyerify(school['buyer']),
                      'price': dollarify(school['price']),
                      'narrative': build_narrative(school),
                     }
        features.append(Feature(geometry=point,properties=properties))
    return FeatureCollection(features)


def doc_url(filename):
    return filename


def datify(date_str):
    if date_str: return 'Sold ' + date_str


def buyerify(buyer):
    if buyer: return 'to ' + buyer


def dollarify(price_str):
    if price_str: return '$' + locale.format("%d", int(price_str), grouping=True)


def build_narrative(school):
    pass


def slugify(school_name):
    return re.sub("[^a-zA-Z]+","",school_name).lower()


def linkify(school_name):
    return "<a href='#" + slugify(school_name) + "' class='anchorLink'>" + school_name + "</a>" 


outfile = open(outfile_path,'w')
outfile.write('callback(')
json.dump(geojsonify(incsv),outfile)
outfile.write(')')
outfile.close()
