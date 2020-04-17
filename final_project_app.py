from bs4 import BeautifulSoup
import requests
import json
import time

COVID_BASE_URL = 'https://health-api.com/api/v1/covid-19/$'
CACHE_FILE_NAME = 'cache.json'
COVID_CACHE = {}

headers = {
    'User-Agent': 'UMSI 507 Course Project - Python Scraping',
    'From': 'karbates@umich.edu',
    'Course-Info': 'https://si.umich.edu/programs/courses/507'
}


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


def make_request_using_cache(url, params, cache):
    request_key = construct_unique_key(url, params=params)
    if request_key in cache.keys():
        print("Using cache")
        return cache[request_key]
    else:
        print("Fetching")
        time.sleep(1)
        response = requests.get(url, params=params)
        cache[request_key] = response.text
        save_cache(cache)
        return cache[request_key]

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



def get_covid_data(country):
    '''Obtain API data from COVID19 API.

    Parameters
    ----------
    place: string
        a country or state someone wants to see
        the COVID totals for

    Returns
    -------
    dict
        a converted API return from COVID API
    '''
    params = {'country': country}
    results = make_request_using_cache(COVID_BASE_URL, params, COVID_CACHE)
    json_results = json.loads(results)
    return json_results



print(get_covid_data('United States'))


url = "https://www.kff.org/other/state-indicator/adults-at-higher-risk-of-serious-illness-if-infected-with-coronavirus/?currentTimeframe=0&selectedRows=%7B%22states%22:%7B%22iowa%22:%7B%7D%7D%7D&sortModel=%7B%22colId%22:%22Location%22,%22sort%22:%22asc%22%7D"
# response = requests.get(url, headers=headers)
# soup = BeautifulSoup(response.text, 'html.parser')
# searching_site = soup.find("div", class_="ag-cell-no-focus ag-cell ag-cell-not-inline-editing ag-cell-value")

# print(searching_site)


kff_page_url = url
response = requests.get(kff_page_url, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')
print(soup)