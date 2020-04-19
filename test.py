from bs4 import BeautifulSoup
import requests
import json
import time


CACHE_FILE_NAME = 'cache.json'
COVID_CACHE = {}


def load_cache():
    try:
        cache_file = open(CACHE_FILE_NAME, 'r')
        cache_file_contents = cache_file.read()
        cache = json.loads(cache_file_contents)
        cache_file.close()
    except:
        cache = {}
    return cache


def save_cache(cache):
    cache_file = open(CACHE_FILE_NAME, 'w')
    contents_to_write = json.dumps(cache)
    cache_file.write(contents_to_write)
    cache_file.close()

COVID_CACHE = load_cache()

def construct_unique_key(baseurl, params):
    ''' constructs a key that is guaranteed to uniquely and
    repeatably identify an API request by its baseurl and params

    Parameters
    ----------
    baseurl: string
        The URL for the API endpoint
    params: dict
        A dictionary of param:value pairs

    Returns
    -------
    string
        the unique key as a string
    '''
    param_strings = []
    connector = '_'
    for k in params.keys():
        param_strings.append(f'{k}_{params[k]}')
    unique_key = baseurl + connector + connector.join(param_strings)
    return unique_key



# def make_covid_request_using_cache(url, params):
#     request_key = construct_unique_key(url, params=params)
#     if request_key in cache.keys():
#         print("Using cache")
#         return cache[request_key]
#     else:
#         print("Fetching")
#         time.sleep(1)
#         response = requests.get(url, params=params)
#         cache[request_key] = response.text
#         save_cache(cache)
#         return cache[request_key]



def get_covid_data(country):
    '''Obtain API data from MapQuest API.

    Parameters
    ----------
    site_object: object
        an instance of a national site

    Returns
    -------
    dict
        a converted API return from MapQuest API
    '''
    params = none
    base_url = "https://health-api.com/api/v1/covid-19/$"
    response = requests.get(base_url, params=params)
    results = response.text
    json_results = json.loads(results)
    return json_results


#print(get_covid_data('US'))


# base_url = "https://health-api.com/api/v1/covid-19/total"
# response = requests.get(base_url)
# results = response.text
# json_results = json.loads(results)
# print(json_results)



headers = {
    'User-Agent': 'UMSI 507 Course Project - Python Scraping',
    'From': 'karbates@umich.edu',
    'Course-Info': 'https://si.umich.edu/programs/courses/507'
}
url = "https://www.kff.org/other/state-indicator/adults-at-higher-risk-of-serious-illness-if-infected-with-coronavirus/?currentTimeframe=0&selectedRows=%7B%22states%22:%7B%22iowa%22:%7B%7D%7D%7D&sortModel=%7B%22colId%22:%22Location%22,%22sort%22:%22asc%22%7D"
# response = requests.get(url, headers=headers)
# soup = BeautifulSoup(response.text, 'html.parser')
# searching_site = soup.find("div", class_="ag-cell-no-focus ag-cell ag-cell-not-inline-editing ag-cell-value")

# print(searching_site)


kff_page_url = url
response = requests.get(kff_page_url, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')
print(soup)




### Trial and error for finding the pct at risk pop

    # state_url_key = str(state_url)
    # url_text = make_url_request_using_cache(state_url_key, STATE_URL_CACHE)
    # soup = BeautifulSoup(url_text, 'html.parser')
    # park_instance_list = []
    # searching_state = soup.find('ul', id='list_parks')
    # parks_lis = searching_state.find_all('li', recursive=False)
    # for li in parks_lis:
    #     park_tag = li.find('a')
    #     park_details_path = park_tag['href']
    #     park_url = BASE_URL + park_details_path
    #     park_instance_list.append(get_site_instance(park_url))
    # return park_instance_list




# column = soup.find(class_="ag-cell-no-focus ag-cell ag-cell-not-inline-editing ag-cell-value")
# a = column.find(colid="Total, adults ages 18 and older__At-risk adults, as a share of all adults ages 18 and older")


# def extract_at_risk_pop(url):
#     state_stats = {}
#     states_names = []
#     site_url_key = str(url)
#     url_text = make_url_request_using_cache(site_url_key, URL_CACHE)
#     soup = BeautifulSoup(url_text, 'html.parser')
#     #column = soup.find('tr')
#     #info = soup.find_all('td', recursive=True)
#     info_names = soup.find_all('td', style='width: 87px')
#     for i in info_names[2:-1]:
#         state_stats['state name'] = i.string
#         states_names = i.string
#     #perc_at_risk = a.string
#     return states_names