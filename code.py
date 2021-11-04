import json
import math
import pandas as pd
from requests import get
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 \
    (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
}
page, per_page = 1, 999
WEBSITE = f'''https://www.sreality.cz/api/cs/v2/estates?category_main_cb=4&category_sub_cb=38&category_type_cb=1&locality_region_id=10%7C2%7C8%7C14%7C6&page={page}&per_page={per_page}&tms=1635964216059'''
WEBJSON = json.loads(get(WEBSITE, headers=headers).text)
count_of_page = math.ceil(WEBJSON['result_size'] / per_page)
offer = "https://www.sreality.cz/api"
# add a repeating piece of the offer link here
link_pattern = "https://www.sreality.cz/detail/prodej/komercni/cinzovni-dum/"
info = {}


def get_page(number_of_actual_elem):
    website = f'''https://www.sreality.cz/api/cs/v2/estates?category_main_cb=4&category_sub_cb=38&category_type_cb=1&locality_region_id=10%7C2%7C8%7C14%7C6&page={page}&per_page={per_page}&tms=1635964216059'''
    page_json = json.loads(get(website, headers=headers).text)

    # the first element is advertising, so I trimmed it
    for i in page_json['_embedded']['estates'][1:]:
        x = json.loads(get(offer + i['_links']['self']['href'], headers=headers).text)

        # link
        info.setdefault(x['_links']['self']['title'], [])
        info[x['_links']['self']['title']].append(offer + x['_links']['self']['href'])

        # I didn't find another way :(
        info.setdefault('Odkaz', [])
        info['Odkaz'].append(link_pattern + x['seo']['locality'] + "/" +
                             re.sub("\D", '', x['_links']['self']['href'])[1:])

        # name
        info.setdefault(x['name']['name'], [])
        info[x['name']['name']].append(x['name']['value'])

        # description
        info.setdefault(x['text']['name'], [])
        info[x['text']['name']].append(x['text']['value'])

        # locality
        info.setdefault(x['locality']['name'], [])
        info[x['locality']['name']].append(x['locality']['value'])

        # coordinates
        info.setdefault('lat', [])
        info['lat'].append(x['map']['lat'])
        info.setdefault('lon', [])
        info['lon'].append(x['map']['lon'])

        # parameters
        for k in x['items']:
            # for example, if this is the fifth house and the parameter has just appeared,
            # then you need to add an empty parameter to the four previous houses
            if k['name'] not in list(info.keys()):
                new_parameter(k['name'], number_of_actual_elem)
            # sometimes parameter is array of parameters
            if type(k['value']) != list:
                info[k['name']].append(k['value'])
            else:
                info[k['name']].append("".join([j['value'] for j in k['value']]))

        # near objects
        for k in x['poi']:
            if k['name'] not in list(info.keys()):
                new_parameter(k['name'], number_of_actual_elem)
            info[k['name']].append(k['distance'])

        # if the house has no parameters that exist in the dictionary, add an empty one
        for k in info.keys():
            if len(info[k]) != number_of_actual_elem + 1:
                info[k].append("")

        number_of_actual_elem += 1


def new_parameter(key, count):
    info.setdefault(key, [])
    for i in range(count):
        info[key].append("")


for _ in range(count_of_page):
    get_page((page - 1) * per_page)
    page += 1

pd.DataFrame(info).to_excel('./result.xlsx')
