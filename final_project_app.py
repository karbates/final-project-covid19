from bs4 import BeautifulSoup
import requests
import json
import time
import sqlite3
import csv


COVID_BASE_URL = 'https://covidtracking.com/api/states/daily'
CACHE_FILE_NAME = 'cache.json'
COVID_CACHE = {}

STATE_DATA_URL = 'https://www.kff.org/statedata/'
HEALTH_STATUS_URL = 'https://www.kff.org/state-category/health-status/'
COVID_RISK_URL = 'https://www.kff.org/other/state-indicator/adults-at-higher-risk-of-serious-illness-if-infected-with-coronavirus/'


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
URL_CACHE = load_cache()
VAX_CACHE = load_cache()


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



def get_covid_data(state):
    state_covid_cases = {}
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
    params = {'state': state}
    results = make_request_using_cache(COVID_BASE_URL, params, COVID_CACHE)
    json_results = json.loads(results)
    state_covid_cases[state] = {}
    for group in json_results:
        state_covid_cases[state]['date'] = group['date']
        state_covid_cases[state]['positive cases'] = group['positive']
        if 'hospitalizedCurrently' in group.keys():
            state_covid_cases[state]['currently hospitalized'] = group['hospitalizedCurrently']
        else:
            state_covid_cases[state]['currently hospitalized'] = 0
        if 'recovered' in group.keys():
            state_covid_cases[state]['recovered'] = group['recovered']
        else:
            state_covid_cases[state]['recovered'] = 0
        if 'death' in group.keys():
            state_covid_cases[state]['deaths'] = group['death']
        else:
            state_covid_cases[state]['deaths'] = 0
        # for key, val in group.items():
        #     results_date = group['date']
        #     state = group['state']
        #     positive_cases = group['positive']
        #     curr_hospitalized = group['hospitalizedCurrently']
        #     recovered = group['recovered']
        #     deaths = group['death']

    #print(json.dumps(json_results, indent = 2))
    return state_covid_cases

#print(get_covid_data('NY'))


# url = "https://www.kff.org/other/state-indicator/adults-at-higher-risk-of-serious-illness-if-infected-with-coronavirus/?currentTimeframe=0&selectedRows=%7B%22states%22:%7B%22iowa%22:%7B%7D%7D%7D&sortModel=%7B%22colId%22:%22Location%22,%22sort%22:%22asc%22%7D"
# response = requests.get(url, headers=headers)
# soup = BeautifulSoup(response.text, 'html.parser')
# searching_site = soup.find("div", class_="ag-cell-no-focus ag-cell ag-cell-not-inline-editing ag-cell-value")

# print(searching_site)


# kff_page_url = url
# response = requests.get(kff_page_url, headers=headers)
# soup = BeautifulSoup(response.text, 'html.parser')
# print(soup)



def build_state_url_dict():
    ''' Make a dictionary that maps state name to state page url from "https://www.kff.org/statedata"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a state name and value is the url
    '''
    state_url_dict = {}
    response = requests.get(STATE_DATA_URL)
    soup = BeautifulSoup(response.text, 'html.parser')

    state_dropdown_menu = soup.find('select', class_='geo-picker')
    states_in_menu = state_dropdown_menu.find_all('option')
    for state in states_in_menu[1:]:
        state_name = state.string.lower()
        state_abbrv = state['value']
        full_url = f'{STATE_DATA_URL}?state={state_abbrv}'
        state_health_status_url = f'{HEALTH_STATUS_URL}?state={state_abbrv}'
        state_covid_risk_url = f'{COVID_RISK_URL}?state={state_abbrv}'
        state_url_dict[state_name] = {}
        state_url_dict[state_name]['state data'] = full_url
        state_url_dict[state_name]['state health status'] = state_health_status_url
        state_url_dict[state_name]['state COVID risk pop'] = state_covid_risk_url
    return state_url_dict



def make_url_request_using_cache(url, cache):
    if (url in cache.keys()): # the url is our unique key
        print("Using cache")
        return cache[url]
    else:
        print("Fetching")
        time.sleep(1)
        response = requests.get(url, headers=headers)
        cache[url] = response.text
        save_cache(cache)
        return cache[url]




def extract_at_risk_pop():
    state_names = []
    state_stats = []
    at_risk_pop = {}
    site_url_key = 'https://www.kff.org/global-health-policy/issue-brief/how-many-adults-are-at-risk-of-serious-illness-if-infected-with-coronavirus/'
    url_text = make_url_request_using_cache(site_url_key, URL_CACHE)
    soup = BeautifulSoup(url_text, 'html.parser')
    name = soup.find_all('td', style='width: 87px')
    stats = soup.find_all('td', style='width: 62px;text-align: center')
    for n in name[2:]:
        state_names.append(n.string)
    for stat in stats[1:]:
        state_stats.append(stat.string)
    for state in state_names:
        for stat in state_stats:
            at_risk_pop[state] = stat
            state_stats.remove(stat)
            break
    return at_risk_pop


def write_at_risk_csv():
    at_risk_pop_dict = extract_at_risk_pop()
    with open('at_risk_pop.csv', mode='w') as risk_file:
        writer = csv.writer(risk_file)
        for key, value in at_risk_pop_dict.items():
            writer.writerow([key, value])



# def vaccinated_pop(url):
#     info_table = []
#     url_key = str(url)
#     url_text = make_url_request_using_cache(url_key, VAX_CACHE)
#     soup = BeautifulSoup(url_text, 'html.parser')
#     table = soup.find_all('script', type='text/javascript')
#     info_needed = table[6]
#     info_two = info_needed.strip('\n\tvar appJs = appJs || {};\n\tappJs = jQuery.extend(appJs, ')
#     return info_two

# print(vaccinated_pop('https://www.kff.org/other/state-indicator/adult-overweightobesity-rate-by-gender/'))



# def vaccinated_pop_two(url):
#     table_text = []
#     url_key = str(url)
#     url_text = make_url_request_using_cache(url_key, VAX_CACHE)
#     soup = BeautifulSoup(url_text, 'html.parser')
#     table = soup.find_all('script', type="text/javascript")
#     for t in table[7:]:
#         table_text.append(t.text)
#     return table_text


'''
CREATING THE DATABASES
'''

DB_NAME = "covid_state_info.sqlite"

def create_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    drop_risk_sql = '''
        DROP TABLE IF EXISTS AtRiskPopulation;
    '''

    create_risk_sql = '''
        CREATE TABLE IF NOT EXISTS AtRiskPopulation (
            "Id"        INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
            "STATE" TEXT NOT NULL,
            "PCT AT RISK POPULATION"  TEXT NOT NULL
        );
    '''

    drop_state_sql = '''
        DROP TABLE IF EXISTS StateInfo;
    '''

    create_state_sql = '''
        CREATE TABLE IF NOT EXISTS StateInfo (
            "Id" INTEGER PRIMARY KEY AUTOINCREMENT,
            "FIPS" INTEGER NOT NULL,
            "STATE" TEXT NOT NULL,
            "STATE ABBRV" TEXT NOT NULL,
            "NUMERIC INFO SITE" TEXT,
            "INFORMATIONAL SITE"  TEXT,
            "TWITTER"  TEXT
        );
    '''

    cur.execute(drop_risk_sql)
    cur.execute(drop_state_sql)

    cur.execute(create_risk_sql)
    cur.execute(create_state_sql)

    conn.commit()
    conn.close()



def load_risk():

    file_contents = open('at_risk_pop.csv', 'r')
    csv_reader = csv.reader(file_contents)

    insert_risk_sql = '''
        INSERT INTO AtRiskPopulation
        VALUES (NULL, ?, ?)
    '''

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()


    for r in csv_reader:
        cur.execute(insert_risk_sql,
            [
                r[0], #state
                r[1] #pct at risk
            ]
        )
    conn.commit()
    conn.close()


def load_state():

    file_contents = open('info.csv', 'r')
    csv_reader = csv.reader(file_contents)

    insert_state_sql = '''
        INSERT INTO StateInfo
        VALUES (NULL, ?, ?, ?, ?, ?, ?)
    '''

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    for r in csv_reader:
        cur.execute(insert_state_sql,
            [
                r[8], #FIPS
                r[9], #STATE
                r[0], #STATE ABBRV
                r[2], #NUM INFO SITE
                r[3], #INFO SITE
                r[4] #TWITTER
            ]
        )
    conn.commit()
    conn.close()

