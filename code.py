import json
from math import ceil
import pandas as pd
from requests import get

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 \
    (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
}
page, PER_PAGE = 1, 999
WEBSITE = f'''https://www.sreality.cz/api/cs/v2/estates?category_main_cb=4&category_sub_cb=38&category_type_cb=1&locality_region_id=10%7C2%7C8%7C14%7C6&page={page}&per_page={PER_PAGE}&tms=1635964216059'''
WEB_JSON = json.loads(get(WEBSITE, headers=HEADERS).text)
COUNT_OF_PAGE = ceil(WEB_JSON['result_size'] / PER_PAGE)
XHR_PATTERN = "https://www.sreality.cz/api"

# add a repeating piece of the offer link here
LINK_PATTERN = "https://www.sreality.cz/detail/prodej/komercni/cinzovni-dum/"
data = {}


def get_page(number_of_actual_elem):
    website = f'''https://www.sreality.cz/api/cs/v2/estates?category_main_cb=4&category_sub_cb=38&category_type_cb=1&locality_region_id=10%7C2%7C8%7C14%7C6&page={page}&per_page={PER_PAGE}&tms=1635964216059'''
    page_json = json.loads(get(website, headers=HEADERS).text)

    # the first element is advertising, so I trimmed it
    for offer in page_json['_embedded']['estates'][1:]:
        actual_offer = json.loads(get(XHR_PATTERN + offer['_links']['self']['href'], headers=HEADERS).text)

        # link
        data.setdefault(actual_offer['_links']['self']['title'], [])
        data[actual_offer['_links']['self']['title']].append(XHR_PATTERN + actual_offer['_links']['self']['href'])

        # I didn't find another way, but I really wanted to add a normal link to the offer :(
        data.setdefault('Odkaz', [])
        data['Odkaz'].append(LINK_PATTERN + actual_offer['seo']['locality'] + "/" +
                             actual_offer['_links']['self']['href'].split('estates/')[1])

        # name
        data.setdefault(actual_offer['name']['name'], [])
        data[actual_offer['name']['name']].append(actual_offer['name']['value'])

        # description
        data.setdefault(actual_offer['text']['name'], [])
        data[actual_offer['text']['name']].append(actual_offer['text']['value'])

        # locality
        data.setdefault(actual_offer['locality']['name'], [])
        data[actual_offer['locality']['name']].append(actual_offer['locality']['value'])

        # coordinates
        data.setdefault('lat', [])
        data['lat'].append(actual_offer['map']['lat'])
        data.setdefault('lon', [])
        data['lon'].append(actual_offer['map']['lon'])

        # parameters
        for k in actual_offer['items']:
            # for example, if this is the fifth house and the parameter has just appeared,
            # then you need to add an empty parameter to the four previous houses
            if k['name'] not in data:
                new_parameter(k['name'], number_of_actual_elem)
            # sometimes parameter is array of parameters
            if type(k['value']) != list:
                data[k['name']].append(k['value'])
            else:
                data[k['name']].append("".join([j['value'] for j in k['value']]))

        # near objects
        for k in actual_offer['poi']:
            if k['name'] not in data:
                new_parameter(k['name'], number_of_actual_elem)
            data[k['name']].append(k['distance'])

        # if the house has no parameters that exist in the dictionary, add an empty one
        for k in data.keys():
            if len(data[k]) != number_of_actual_elem + 1:
                data[k].append("")

        number_of_actual_elem += 1


def new_parameter(key, count):
    data.setdefault(key, [])
    for i in range(count):
        data[key].append("")


for _ in range(COUNT_OF_PAGE):
    get_page((page - 1) * PER_PAGE)
    page += 1

pd.DataFrame(data).to_excel('./result.xlsx')
