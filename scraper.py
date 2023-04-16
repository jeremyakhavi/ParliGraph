from bs4 import BeautifulSoup
import requests
import re
from logger_config import get_logger
import os

logger = get_logger(__name__)

def calculate_vote_direction_and_strength(text):
    # extract number of votes for and against the policy
    votes_for_pattern = r"(\d+) votes? for"
    votes_against_pattern = r"(\d+) votes? against"
    votes_for = int(re.search(votes_for_pattern, text).group(1))
    votes_against = int(re.search(votes_against_pattern, text).group(1))
    if votes_for > votes_against:
        direction = 'voted_for'
        strength = votes_for / (votes_for + votes_against)
    elif votes_against > votes_for:
        direction = 'voted_against'
        strength = votes_against / (votes_for + votes_against)
    else:
        direction = 'vote_split'
        strength = 0.5     
    strength = round(strength, 5)
    return direction, strength

#TODO: should I move this to person.py?
def scrape_mp_votes(mp_twfy_id):
    URL = f"https://www.theyworkforyou.com/mp/{mp_twfy_id}/votes"
    page = requests.get(URL)

    soup = BeautifulSoup(page.content, "html.parser")

    elements = soup.find("div", class_="primary-content__unit")
    panels = elements.find_all("div", class_="panel")

    mp_votes = []
    for panel in panels:
        issue = panel.find("h2")
        if issue is not None and issue.has_attr('id'):
            vote_descriptions = panel.find("ul", class_="vote-descriptions")
            votes = vote_descriptions.find_all("li", class_="vote-description")
            for vote in votes:
                vote_evidence = vote.find("a", class_="vote-description__evidence")
                vote_evidence = vote_evidence.get_text(strip=True)
                vote_direction, vote_strength = calculate_vote_direction_and_strength(vote_evidence)
                vote_tuple = (vote['data-policy-desc'], vote_direction, vote_strength)
                mp_votes.append(vote_tuple)
    return mp_votes

def scrape_constituency_regions():
    constituency_region_dict = {}
    print("Scrape constituency regions")
    URL = "https://en.wikipedia.org/wiki/Constituencies_of_the_Parliament_of_the_United_Kingdom"
    page = requests.get(URL)

    soup = BeautifulSoup(page.content, "html.parser")

    # ENGLISH CONSTITUENCIES
    print("Scraping consituency data for England")
    england_table = soup.find("table", {"id":"England"})
    england_th_elements = england_table.find_all('th')

    # find the index of the th elements with values 'Constituency' and 'Region'
    for i, th in enumerate(england_th_elements):
        value = th.text.strip()
        if value == 'Constituency':
            england_constituency_index = i
        if value == 'Region':
            england_region_index = i
    
    england_tr_elements = england_table.find_all('tr')

    # find constituency and region values in table (skip first `tr` as it is header)
    for tr in england_tr_elements[1:]:
        td_elements = tr.find_all('td')
        constituency = td_elements[england_constituency_index].text.strip().lower()
        region = td_elements[england_region_index].text.strip()
        # add constituency and region to dictionary
        constituency_region_dict[constituency] = region

    # don't need to find region for other countries constituencies as region is just country
    countries = ['Scotland', 'Wales', 'NI']
    for country in countries:
        output_dict = get_constituencies_from_table(soup, country)
        constituency_region_dict.update(output_dict)
    
    return constituency_region_dict

def get_constituencies_from_table(html, country_id):
    print(f"Scraping consituency data for {country_id}")
    constituency_region_dict = {}
    table = html.find("table", {"id":country_id})
    th_elements = table.find_all('th')

    # find the index of the th element with value 'Constituency'
    for i, th in enumerate(th_elements):
        value = th.text.strip()
        if value == 'Constituency':
            constituency_index = i
    
    tr_elements = table.find_all('tr')

    # find constituency values in table (skip first `tr` as it is header)
    for tr in tr_elements[1:]:
        td_elements = tr.find_all('td')
        constituency = td_elements[constituency_index].text.strip().lower()
        # add constituency and region to dictionary
        constituency_region_dict[constituency] = country_id
    return constituency_region_dict

def get_twfy_ids():
    """
    Submit get request to TheyWorkForYou (twfy)
    Extract relevant ids and names from response and put in dictionary
    Return dictionary
    """
    logger.info("Getting TWFY IDs and MP names from TWFY getMPs API")
    twfy_dict = {}

    url = 'https://www.theyworkforyou.com/api/getMPs'
    params = {'key': os.getenv("TWFY_API_KEY"), 'output': 'json'}

    response = requests.get(url, params=params)
    data = response.json()
    logger.debug(f"Data from TWFY getMPS API: {data}")
    for mp in data:
        constituency = mp['constituency'].lower()
        twfy_dict[constituency] = {'name': mp['name'], 'twfy_id': mp['person_id']}
    logger.debug(f"TWFY dict: {twfy_dict}")
    return twfy_dict

def get_govt_posts_from_members_api():
    logger.info("Getting govt posts from Members GovernmentPosts API")
    url = 'https://members-api.parliament.uk/api/Posts/GovernmentPosts'
    govt_post_dict = {}
    response = requests.get(url)
    data = response.json()
    logger.debug(f"Data from GovernmentPosts API {data}")
    for govt_post in data:
        mp_id = govt_post['value']['postHolders'][0]['member']['value']['id']
        post_name = govt_post['value']['name']
        govt_post_dict[mp_id] = post_name
    logger.debug(f"Govt posts dict: {govt_post_dict}")
    return govt_post_dict

    