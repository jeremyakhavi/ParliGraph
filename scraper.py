from bs4 import BeautifulSoup
import requests
import re
from logger_config import get_logger
import os

logger = get_logger(__name__)

def calculate_vote_direction_and_strength(text):
    """
    Calculate the vote direction and strength from a given text string.
    
    Args:
        text (str): The text containing vote information.
    
    Returns:
        tuple: A tuple containing the vote direction (str) and vote strength (float).
    """
    # Define patterns to extract vote counts for and against
    votes_for_pattern = r"(\d+) votes? for"
    votes_against_pattern = r"(\d+) votes? against"
    
    # Extract vote counts using regex patterns
    votes_for = int(re.search(votes_for_pattern, text).group(1))
    votes_against = int(re.search(votes_against_pattern, text).group(1))
    
    # Determine vote direction and calculate vote strength
    if votes_for > votes_against:
        direction = 'voted_for'
        strength = votes_for / (votes_for + votes_against)
    elif votes_against > votes_for:
        direction = 'voted_against'
        strength = votes_against / (votes_for + votes_against)
    else:
        direction = 'vote_split'
        strength = 0.5
    
    # Round the vote strength to 5 decimal places    
    strength = round(strength, 5)
    
    return direction, strength

def scrape_mp_votes(mp_twfy_id):
    """
    Scrape MP voting records from the TheyWorkForYou website using a given MP's TWFY ID.
    
    Args:
        mp_twfy_id (int): The TheyWorkForYou ID of the MP.
    
    Returns:
        list: A list of tuples containing MP's voting data.
    """
    # Construct URL with MP's TWFY ID and send a GET request
    URL = f"https://www.theyworkforyou.com/mp/{mp_twfy_id}/votes"
    page = requests.get(URL)

    soup = BeautifulSoup(page.content, "html.parser")

    # Find the main content container and locate all panels containing vote information
    elements = soup.find("div", class_="primary-content__unit")
    panels = elements.find_all("div", class_="panel")

    mp_votes = []
    # Iterate over panels to find relevant vote information
    for panel in panels:
        issue = panel.find("h2")
        if issue is not None and issue.has_attr('id'):
            vote_descriptions = panel.find("ul", class_="vote-descriptions")
            votes = vote_descriptions.find_all("li", class_="vote-description")        
            # Extract vote data and calculate vote direction and strength
            for vote in votes:
                vote_evidence = vote.find("a", class_="vote-description__evidence")
                vote_evidence = vote_evidence.get_text(strip=True)
                vote_direction, vote_strength = calculate_vote_direction_and_strength(vote_evidence)
                vote_tuple = (vote['data-policy-desc'], vote_direction, vote_strength)
                # Append vote data to the list of MP votes
                mp_votes.append(vote_tuple)
    
    return mp_votes

def scrape_constituency_regions():
    """
    Scrape constituency regions from the Wikipedia page.
    
    Returns:
        dict: A dictionary mapping constituency names (str) to their regions (str).
    """
    logger.info("Scrape constituency regions")
    constituency_region_dict = {}
    
    # Send a GET request to the Wikipedia page containing constituency information
    URL = "https://en.wikipedia.org/wiki/Constituencies_of_the_Parliament_of_the_United_Kingdom"
    page = requests.get(URL)

    soup = BeautifulSoup(page.content, "html.parser")

    # English Constituencies
    logger.info("Scraping consituency data for England")
    england_table = soup.find("table", {"id":"England"})
    england_th_elements = england_table.find_all('th')

    # Find the index of the th elements with values 'Constituency' and 'Region'
    for i, th in enumerate(england_th_elements):
        value = th.text.strip()
        if value == 'Constituency':
            england_constituency_index = i
        if value == 'Region':
            england_region_index = i
    
    england_tr_elements = england_table.find_all('tr')

    # Find constituency and region values in table (skip first `tr` as it's the header)
    for tr in england_tr_elements[1:]:
        td_elements = tr.find_all('td')
        constituency = td_elements[england_constituency_index].text.strip().lower()
        region = td_elements[england_region_index].text.strip()
        # Add constituency and region to dictionary
        constituency_region_dict[constituency] = region

    # Don't need to find region for other countries constituencies as region is just country
    countries = ['Scotland', 'Wales', 'NI']
    for country in countries:
        output_dict = get_constituencies_from_table(soup, country)
        constituency_region_dict.update(output_dict)
    
    return constituency_region_dict

def get_constituencies_from_table(html, country_id):
    """
    Extract constituencies from an HTML table element for a given country ID.
    
    Args:
        html (bs4.BeautifulSoup): The BeautifulSoup object containing the HTML page content.
        country_id (str): The country ID, used to find the corresponding table in the HTML.
    
    Returns:
        dict: A dictionary mapping constituency names (str) to their regions (str).
    """
    logger.info(f"Scraping consituency data for {country_id}")
    constituency_region_dict = {}
    
    # Find the table with the specified country_id
    table = html.find("table", {"id":country_id})
    th_elements = table.find_all('th')

    # Find the index of the th element with value 'Constituency'
    for i, th in enumerate(th_elements):
        value = th.text.strip()
        if value == 'Constituency':
            constituency_index = i
    
    tr_elements = table.find_all('tr')

    # Find constituency values in table (skip first `tr` as it is the header)
    for tr in tr_elements[1:]:
        td_elements = tr.find_all('td')
        constituency = td_elements[constituency_index].text.strip().lower()
        # Add constituency and region to dictionary
        constituency_region_dict[constituency] = country_id
    
    return constituency_region_dict

def get_twfy_ids():
    """
    Retrieve TWFY IDs and MP names using the TWFY API.
    
    Returns:
        dict: A dictionary mapping constituency names (str) to a dictionary 
              containing MP names (str) and TWFY IDs (int).
    """
    logger.info("Getting TWFY IDs and MP names from TWFY getMPs API")
    twfy_dict = {}
    
    # Set the URL and parameters for the TWFY API request
    url = 'https://www.theyworkforyou.com/api/getMPs'
    params = {'key': os.getenv("TWFY_API_KEY"), 'output': 'json'}

    response = requests.get(url, params=params)
    data = response.json()
    logger.debug(f"Data from TWFY getMPS API: {data}")

    # Iterate through the data, extracting constituency names, MP names, and TWFY IDs
    for mp in data:
        constituency = mp['constituency'].lower()
        twfy_dict[constituency] = {'name': mp['name'], 'twfy_id': mp['person_id']}
    
    logger.debug(f"TWFY dict: {twfy_dict}")
    
    return twfy_dict

def get_govt_posts_from_members_api():
    """
    Retrieve government posts using the UK Parliament Members API.
    
    Returns:
        dict: A dictionary mapping MP IDs (int) to their government post names (str).
    """
    logger.info("Getting govt posts from Members GovernmentPosts API")
    govt_post_dict = {}
    
    # Set the URL for the Members API request
    url = 'https://members-api.parliament.uk/api/Posts/GovernmentPosts'

    response = requests.get(url)
    data = response.json()
    logger.debug(f"Data from GovernmentPosts API {data}")

    # Iterate through the data, extracting MP IDs and government post names
    for govt_post in data:
        mp_id = govt_post['value']['postHolders'][0]['member']['value']['id']
        post_name = govt_post['value']['name']
        # Add MP ID and government post name to the dictionary
        govt_post_dict[mp_id] = post_name

    logger.debug(f"Govt posts dict: {govt_post_dict}")
    
    return govt_post_dict

    