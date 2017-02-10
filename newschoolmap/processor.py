import csv, json, locale, re
from geojson import Feature, FeatureCollection, Point 
from typify import parse_str_date

### START CONFIG ###
infile_path = 'closed_schools_data.csv'
outfile_path = 'geo_schools.geojson'
s3_prefix = 'https://s3.amazonaws.com/projects.chicagoreporter.com/graphics/newschoolmap/'
img_prefix = s3_prefix + 'images/'
pdf_prefix = s3_prefix + 'pdfs/'
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
                      'img' : imgify(school['img']),
                      'address': school['address'],
                      'name': school['closed_school'],
                      'link': linkify(school['closed_school']),
                      'comm_area': school['community_area'],
                      'status': school['status'],
                      'usage': school['usage'],
                      'status_doc': pdfify(school['status_doc']),
                      'repurpose_doc': pdfify(school['repurpose_doc']),
                      'alderman': alderify(school['alderman']),
                      'board_approval_date': datify(school['board_approval_date']),
                      'buyer': buyerify(school['buyer']),
                      'price': dollarify(school['price']),
                      'narrative': build_narrative(school),
                     }
        features.append(Feature(geometry=point,properties=properties))
    return FeatureCollection(features)


def datify(date_str):
    if date_str: 
        date_obj = parse_str_date(date_str)
        month = date_obj.strftime('%b') + ' '
        day = str(int(date_obj.strftime('%d'))) + ', '
        year = date_obj.strftime('%Y')
        return month + day + year


def buyerify(buyer):
    if buyer: return buyer


def dollarify(price_str):
    #if price_str: return '$' + locale.format("%d", int(price_str), grouping=True)
    return price_str + '. '


def build_narrative(school):
    narrative = ''
    # start with sale info, if any
    if school['board_approval_date']:
        sale_narr = 'The Board of Education approved a sale to '
        sale_narr += buyerify(school['buyer'])
        sale_narr += ' on '
        sale_narr += datify(school['board_approval_date'])
        sale_narr += ' for '
        sale_narr += dollarify(school['price'])
        narrative += sale_narr
    narrative += school['usage']
    narrative += school['notes']
    return narrative



def slugify(school_name):
    return re.sub("[^a-zA-Z]+","",school_name).lower()


def linkify(school_name):
    return "<a href='#" + slugify(school_name) + "' class='anchorLink'>" + school_name + "</a>" 


def imgify(file_name):
    if file_name: return img_prefix + file_name.replace(' ','+') + '.jpg'  


def pdfify(file_name):
    return pdf_prefix + file_name  


def alderify(ald_name):
    return "Alderman " + ald_name

outfile = open(outfile_path,'w')
outfile.write('callback(')
json.dump(geojsonify(incsv),outfile)
outfile.write(')')
outfile.close()
