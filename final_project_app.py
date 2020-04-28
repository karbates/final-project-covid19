from bs4 import BeautifulSoup
from requests_oauthlib import OAuth1
import requests
import json
import time
import sqlite3
import csv
import secrets
from collections import defaultdict
from datetime import datetime
from datetime import date
from flask import Flask, render_template, request
import plotly.graph_objects as go
app = Flask(__name__)

'''
CITATIONS/ACKNOWLEDGMENTS:

Used the StackOverflow post for formatting the date from COVID API:
https://stackoverflow.com/questions/9750330/how-to-convert-integer-into-date-object-python

The caching functions and majority of the Twitter related functions come from SI 507 Course
examples and assignments.


'''

COVID_BASE_URL = 'https://covidtracking.com/api/states/'
CACHE_FILE_NAME = 'cov_cache.json'
COVID_CACHE = {}

STATE_COV_INFO_URL = 'https://covidtracking.com/api/states/info'
STATE_CACHE_NAME = 'state_cov_info_cache.json'
STATE_COV_CACHE = {}

STATE_DATA_URL = 'https://www.kff.org/statedata/'
HEALTH_STATUS_URL = 'https://www.kff.org/state-category/health-status/'
COVID_RISK_URL = 'https://www.kff.org/other/state-indicator/adults-at-higher-risk-of-serious-illness-if-infected-with-coronavirus/'

TWITTER_BASEURL = "https://api.twitter.com/1.1/search/tweets.json"
TWITTER_CACHE_FILENAME = "twitter_cache.json"
TWITTER_CACHE_DICT = {}

NEWS_API_BASE_URL = 'https://newsapi.org/v2/top-headlines'
NEWS_CACHE_FILENAME = "news_cache.json"
NEWS_CACHE_DICT = {}

FIPS_CACHE_NAME = "fips_cache.json"
FIPS_CACHE = {}

client_key = secrets.TWITTER_API_KEY
client_secret = secrets.TWITTER_API_SECRET
access_token = secrets.TWITTER_ACCESS_TOKEN
access_token_secret = secrets.TWITTER_ACCESS_TOKEN_SECRET

oauth = OAuth1(client_key,
            client_secret=client_secret,
            resource_owner_key=access_token,
            resource_owner_secret=access_token_secret)

headers = {
    'User-Agent': 'UMSI 507 Course Project - Python Scraping',
    'From': 'karbates@umich.edu',
    'Course-Info': 'https://si.umich.edu/programs/courses/507'
}


def load_cache(cache_file):
    '''opens cache if it exists and loads JSON into
    respective cache_dict

    if the cache file doesn't exist, it creates a new cache dictionary

    Parameters:
    None

    Returns:
    Cache
    '''
    try:
        cache_file = open(cache_file, 'r')
        cache_file_contents = cache_file.read()
        cache_dict = json.loads(cache_file_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict


COVID_CACHE = load_cache('cov_cache.json')
URL_CACHE = load_cache('state_cov_info_cache.json')



def save_cache(cache_dict):
    ''' saves the information in cache

    Parameters:
    cache_dict: dict
        Information to save

    Returns:
    None
    '''
    contents_to_write = json.dumps(cache_dict)
    cache_file = open(CACHE_FILE_NAME, 'w')
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
    unique_key = baseurl + connector + connector.join(param_strings) + connector + str(date.today())
    return unique_key


def make_twitter_request(baseurl, params):
    '''Make a request to the Web API using the baseurl and params

    Parameters
    ----------
    baseurl: string
        The URL for the API endpoint
    params: dictionary
        A dictionary of param:value pairs

    Returns
    -------
    string
        the data returned from making the request in the form of
        a dictionary
    '''
    response = requests.get(TWITTER_BASEURL, params=params, auth=oauth)
    return response.json()


def make_twitter_request_with_cache(baseurl, params):
    '''Check the cache for a saved result for baseurl+params:values
    combo. If the result is found, return it. Otherwise send a new
    request, save it, then return it.

    Parameters
    ----------
    baseurl: string
        The URL for the API endpoint
    account: string
        account to search for
    count: int
        the number of tweets to retrieve

    Returns
    -------
    string
        the results of the query loaded from cache
    '''
    request_key = construct_unique_key(TWITTER_BASEURL, params)
    if request_key in TWITTER_CACHE_DICT.keys():
        print("Using Cache")
        return TWITTER_CACHE_DICT[request_key]
    else:
        print("Calling API")
        TWITTER_CACHE_DICT[request_key] = make_twitter_request(TWITTER_BASEURL, params)
        save_cache(TWITTER_CACHE_DICT)
        return TWITTER_CACHE_DICT[request_key]


TWITTER_CACHE_DICT = load_cache('state_cov_info_cache.json')


def find_tweets(TWITTER_BASEURL, account, count):
    ''' Finds the hashtag that most commonly co-occurs with the hashtag
    queried in make_request_with_cache().

    Parameters
    ----------
    tweet_data: dict
        Twitter data as a dictionary for a specific query
    hashtag_to_ignore: string
        the same hashtag that is queried in make_request_with_cache()
        (e.g. "#election2020")

    Returns
    -------
    string
        the hashtag that most commonly co-occurs with the hashtag
        queried in make_request_with_cache()

    '''
    tweet_list = []
    params= dict(q=account, count=count)
    results = make_twitter_request_with_cache(TWITTER_BASEURL, params)
    tweets = results['statuses']
    for tweet in tweets:
        tweet_text = tweet['text']
        tweet_list.append(tweet_text)
    return tweet_list


def get_covid_data(call_type, state=None):
    '''Obtain API data on daily counts of COVID cases.

    Parameters
    ----------
    place: string
        a state someone wants to see
        the COVID totals for

    Returns
    -------
    dict
        a converted API return from COVID API
    '''
    params = {'state': state}
    results = make_request_using_cache(COVID_BASE_URL+call_type, params, COVID_CACHE)
    json_results = json.loads(results)
    return json_results


def get_covid_state_data(input_state):
    '''Obtain API data on daily counts of COVID cases.

    Parameters
    ----------
    place: string
        a state someone wants to see
        the COVID totals for

    Returns
    -------
    dict
        a converted API return from COVID API
    '''
    results = get_covid_data("daily", state=input_state)
    state_covid_cases = {}
    state = results[0]['state']
    state_covid_cases[state] = {}
    for group in results:
        date = group['date']
        state_covid_cases[state][date] = {}
        state_covid_cases[state][date]['positive cases'] = group['positive']
        if 'hospitalizedCurrently' in group.keys():
            if group['hospitalizedCurrently'] == None:
                state_covid_cases[state][date]['currently hospitalized'] = 0
            else:
                state_covid_cases[state][date]['currently hospitalized'] = group['hospitalizedCurrently']
        else:
            state_covid_cases[state][date]['currently hospitalized'] = 0
        if 'recovered' in group.keys():
            if group['recovered'] == None:
                state_covid_cases[state][date]['recovered'] = 0
            else:
                state_covid_cases[state][date]['recovered'] = group['recovered']
        else:
            state_covid_cases[state][date]['recovered'] = 0
        if 'death' in group.keys():
            state_covid_cases[state][date]['deaths'] = group['death']
        else:
            state_covid_cases[state][date]['deaths'] = 0
    return state_covid_cases


def plotly_lists(state):
    pos_cases_list = []
    cur_hosp_list = []
    recov_list = []
    deaths_list = []
    state_string = str(state)
    state_info = get_covid_state_data(state_string)
    for key, values in state_info[state_string].items():
        for key, value in values.items():
            if key == 'positive cases':
                pos_cases_list.append(value)
            if key == 'currently hospitalized':
                cur_hosp_list.append(value)
            if key == 'recovered':
                recov_list.append(value)
            if key == 'deaths':
                deaths_list.append(value)
    return pos_cases_list, cur_hosp_list, recov_list, deaths_list


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


def write_csv(py_dict, csv_file):
    with open(csv_file, mode='w') as csv_file:
        writer = csv.writer(csv_file)
        for key, value in py_dict.items():
            writer.writerow([value])


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
            "PCT_AT_RISK_POPULATION"  TEXT NOT NULL
        );
    '''

    drop_obese_sql = '''
        DROP TABLE IF EXISTS ObesePopulation;
    '''

    create_obese_sql = '''
        CREATE TABLE IF NOT EXISTS ObesePopulation (
            "STATE" TEXT NOT NULL,
            "OBESE_POPULATION"  INT NOT NULL,
            "PCT MALE" INT NOT NULL,
            "PCT FEMALE" INT NOT NULL
        );
    '''

    drop_icu_sql = '''
        DROP TABLE IF EXISTS ICUBeds;
    '''

    create_icu_sql = '''
        CREATE TABLE IF NOT EXISTS ICUBeds (
            "STATE" TEXT NOT NULL,
            "ICU_BEDS"  INT NOT NULL,
            "ICU_BEDS_PER_10K" INT NOT NULL
        );
    '''

    drop_hosp_sql = '''
        DROP TABLE IF EXISTS HospBeds;
    '''

    create_hosp_sql = '''
        CREATE TABLE IF NOT EXISTS HospBeds (
            "STATE" TEXT NOT NULL,
            "TOTAL_BEDS"  INT NOT NULL,
            "BEDS_PER_1K" INT NOT NULL
        );
    '''

    drop_state_sql = '''
        DROP TABLE IF EXISTS StateInfo;
    '''

    create_state_sql = '''
        CREATE TABLE IF NOT EXISTS StateInfo (
            "Id" INTEGER PRIMARY KEY AUTOINCREMENT,
            "FIPS" INTEGER NOT NULL,
            "STATE_NAME" TEXT NOT NULL,
            "STATE_ABBRV" TEXT NOT NULL,
            "NUMERIC_INFO_SITE" TEXT,
            "INFORMATIONAL_SITE"  TEXT,
            "TWITTER"  TEXT
        );
    '''

    cur.execute(drop_risk_sql)
    cur.execute(drop_obese_sql)
    cur.execute(drop_icu_sql)
    cur.execute(drop_hosp_sql)
    cur.execute(drop_state_sql)

    cur.execute(create_risk_sql)
    cur.execute(create_obese_sql)
    cur.execute(create_icu_sql)
    cur.execute(create_hosp_sql)
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


def load_obesity():

    file_contents = open('state_obesity_stats.csv', 'r')
    csv_reader = csv.reader(file_contents)
    next(csv_reader)

    insert_obesity_sql = '''
        INSERT INTO ObesePopulation
        VALUES (?, ?, ?, ?)
    '''

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()


    for r in csv_reader:
        cur.execute(insert_obesity_sql,
            [
                r[0], #state
                r[1], #obese population
                r[2], #male
                r[3], #female
            ]
        )
    conn.commit()
    conn.close()


def load_icu_beds():

    file_contents = open('icu_beds.csv', 'r')
    csv_reader = csv.reader(file_contents)
    next(csv_reader)

    insert_icu_sql = '''
        INSERT INTO ICUBeds
        VALUES (?, ?, ?)
    '''

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()


    for r in csv_reader:
        cur.execute(insert_icu_sql,
            [
                r[0], #state
                r[1], #icu_beds
                r[2] #icu_beds_per_10k
            ]
        )
    conn.commit()
    conn.close()


def load_hosp_beds():

    file_contents = open('hosp_beds.csv', 'r')
    csv_reader = csv.reader(file_contents)
    next(csv_reader)

    insert_hosp_sql = '''
        INSERT INTO HospBeds
        VALUES (?, ?, ?)
    '''

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()


    for r in csv_reader:
        cur.execute(insert_hosp_sql,
            [
                r[0], #state
                r[1], #total beds
                r[2], #beds per 1K
            ]
        )
    conn.commit()
    conn.close()


def load_state():

    results = get_covid_data("info")

    insert_state_sql = '''
        INSERT INTO StateInfo
        VALUES (NULL, ?, ?, ?, ?, ?, ?)
    '''

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    for r in results:
        cur.execute(insert_state_sql,
            [
                r["fips"], #FIPS
                r["name"], #STATE
                r["state"], #STATE ABBRV
                r["covid19Site"], #NUM INFO SITE
                r["covid19SiteSecondary"], #INFO SITE
                r["twitter"] #TWITTER
            ]
        )
    conn.commit()
    conn.close()



''' FUNCTIONS FOR FLASK '''

create_db()
load_risk()
load_obesity()
load_icu_beds()
load_hosp_beds()
load_state()


def get_db_info(info, state):
    conn = sqlite3.connect("covid_state_info.sqlite")
    cur = conn.cursor()

    select_statement = f'SELECT "{info}"'
    where_clause = f'WHERE STATE_ABBRV = "{state}"'

    q = f'''
        {select_statement}
        FROM AtRiskPopulation
        JOIN StateInfo ON AtRiskPopulation.STATE = StateInfo.STATE_NAME
        {where_clause}
    '''
    results = cur.execute(q).fetchall()
    conn.close()
    return results[0]


def addl_db_info(info, state, table):
    conn = sqlite3.connect("covid_state_info.sqlite")
    cur = conn.cursor()

    select_statement = f'SELECT {info}'
    where_clause = f'WHERE STATE_ABBRV = "{state}"'

    q = f'''
        {select_statement}
        FROM {table}
        JOIN StateInfo ON {table}.STATE = StateInfo.STATE_NAME
        {where_clause}
    '''
    results = cur.execute(q).fetchall()
    conn.close()
    return results[0]


@app.route('/')
def index():
    return render_template('index.html') # just the static HTML


@app.route('/handle_form', methods=['POST'])
def handle_the_form():
    selected_state = request.form["states"]
    state_name = get_db_info("STATE_NAME", selected_state)[0]
    state_info = get_covid_state_data(selected_state)[selected_state]
    want_health_status = "health_status" in request.form.keys()
    want_cdc_tweets = "cdc_tweets" in request.form.keys()
    want_state_hd_tweets = "state_hd_tweets" in request.form.keys()
    graph_string=f'/covid_plot/{selected_state}'
    state_pct_at_risk = get_db_info("PCT_AT_RISK_POPULATION", selected_state)[0]
    state_obese_pop = addl_db_info("OBESE_POPULATION", selected_state, "ObesePopulation")[0]
    state_obese_pop = round(state_obese_pop*100,1)
    state_obese_pop = f'{state_obese_pop}%'
    state_icu_beds = addl_db_info("ICU_BEDS", selected_state, "ICUBeds")[0]
    state_hosp_beds = addl_db_info("TOTAL_BEDS", selected_state, "HospBeds")[0]
    cdc_tweets = find_tweets(TWITTER_BASEURL, "from:@CDCgov", 5)
    state_hd_twitter_acct = get_db_info("TWITTER", selected_state)[0]
    from_acct = f'from:{state_hd_twitter_acct}'
    state_tweets = find_tweets(TWITTER_BASEURL, from_acct, 5)
    return render_template('response.html',
        states=selected_state,
        state_name=state_name,
        want_health_status=want_health_status,
        pct_at_risk_stat = state_pct_at_risk,
        state_obese_pop=state_obese_pop,
        state_icu_beds=state_icu_beds,
        state_hosp_beds=state_hosp_beds,
        want_cdc_tweets=want_cdc_tweets,
        cdc_tweets = cdc_tweets,
        want_state_hd_tweets=want_state_hd_tweets,
        state_tweets = state_tweets,
        state_info=state_info,
        graph_link=graph_string
        )


@app.route('/articles')
def get_headlines():
    params = {
        "country": "us",
        "apiKey": secrets.NEWSAPI_KEY,
        "q": "COVID-19"
    }
    article_info_list = []
    response = requests.get(NEWS_API_BASE_URL, params)
    result = response.json()
    articles = result['articles']
    for a in articles:
        headline = a['title']
        author = a['author']
        link = a['url']
        article_info = (f'{headline} by {author}. Read here: {link}')
        article_info_list.append(article_info)
    return render_template('articles.html',
        articles=article_info_list,
        )


@app.route('/covid_plot/<state>')
def plot(state):
    date_list = []
    pos_cases_list = []
    cur_hosp_list = []
    recov_list = []
    deaths_list = []
    state_info = get_covid_state_data(state)
    state_name = get_db_info("STATE_NAME", state)[0]
    state_pct_at_risk = get_db_info("PCT_AT_RISK_POPULATION", state)[0]
    state_obese_pop = addl_db_info("OBESE_POPULATION", state, "ObesePopulation")[0]
    state_obese_pop = round(state_obese_pop*100,1)
    state_obese_pop = f'{state_obese_pop}%'
    state_icu_beds = addl_db_info("ICU_BEDS", state, "ICUBeds")[0]
    state_hosp_beds = addl_db_info("TOTAL_BEDS", state, "HospBeds")[0]
    for key, values in state_info[state].items():
        date_str = str(key)
        date = datetime(year=int(date_str[0:4]), month=int(date_str[4:6]), day=int(date_str[6:8]))
        date_list.append(date)
        for key, value in values.items():
            if key == 'positive cases':
                pos_cases_list.append(value)
            if key == 'currently hospitalized':
                cur_hosp_list.append(value)
                cur_hosp_list = [0 if i is None else i for i in cur_hosp_list]
            if key == 'recovered':
                recov_list.append(value)
            if key == 'deaths':
                deaths_list.append(value)

    x_vals = date_list
    y_vals = pos_cases_list

    line_data_one = go.Line(
        x=x_vals,
        y=y_vals
    )

    x_vals = date_list
    y_vals = cur_hosp_list

    line_data_two = go.Line(
        x=x_vals,
        y=y_vals
    )

    x_vals = date_list
    y_vals = recov_list

    line_data_three = go.Line(
        x=x_vals,
        y=y_vals
    )

    x_vals = date_list
    y_vals = deaths_list

    line_data_four = go.Line(
        x=x_vals,
        y=y_vals
    )

    basic_layout = go.Layout(title='Positive Cases')
    fig_one = go.Figure(data=line_data_one, layout=basic_layout)
    div_one = fig_one.to_html(full_html=False)

    basic_layout = go.Layout(title='Currently Hospitalized')
    fig_two = go.Figure(data=line_data_two, layout=basic_layout)
    div_two = fig_two.to_html(full_html=False)

    basic_layout = go.Layout(title='Recovered')
    fig_three = go.Figure(data=line_data_three, layout=basic_layout)
    div_three = fig_three.to_html(full_html=False)

    basic_layout = go.Layout(title='Deaths')
    fig_four = go.Figure(data=line_data_four)
    div_four = fig_four.to_html(full_html=False)

    return render_template("covid_plot.html",
        state_name=state_name,
        pct_at_risk_stat = state_pct_at_risk,
        state_obese_pop = state_obese_pop,
        state_icu_beds = state_icu_beds,
        state_hosp_beds = state_hosp_beds,
        plot_div1=div_one,
        plot_div2=div_two,
        plot_div3=div_three,
        plot_div4=div_four)


if __name__ == "__main__":
    app.run(debug=True)


