import pytest
from bs4 import BeautifulSoup
import sys
import os
import requests
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(parent_dir)
from scraper import calculate_vote_direction_and_strength, scrape_mp_votes, scrape_constituency_regions, get_constituencies_from_table


def test_calculate_vote_direction_and_strength():
    text1 = "300 votes for, 200 votes against"
    direction1, strength1 = calculate_vote_direction_and_strength(text1)
    assert direction1 == "voted_for"
    assert strength1 == 0.6

    text2 = "100 votes for, 200 votes against"
    direction2, strength2 = calculate_vote_direction_and_strength(text2)
    assert direction2 == "voted_against"
    assert strength2 == 0.66667

    text3 = "150 votes for, 150 votes against"
    direction3, strength3 = calculate_vote_direction_and_strength(text3)
    assert direction3 == "vote_split"
    assert strength3 == 0.5


@pytest.fixture
def mp_twfy_id():
    yield "25344"


@pytest.fixture
def mp_votes_soup(mp_twfy_id):
    URL = f"https://www.theyworkforyou.com/mp/{mp_twfy_id}/votes"
    print(URL)
    page = requests.get(URL)
    print(page.content)
    yield BeautifulSoup(page.content, "html.parser")


def test_scrape_mp_votes(mp_twfy_id, mp_votes_soup):
    mp_votes = scrape_mp_votes(mp_twfy_id)
    
    test_votes = 0
    elements = mp_votes_soup.find("div", class_="primary-content__unit")
    panels = elements.find_all("div", class_="panel")
    for panel in panels:
        issue = panel.find("h2")
        if issue is not None and issue.has_attr('id'):
            vote_descriptions = panel.find("ul", class_="vote-descriptions")
            votes = vote_descriptions.find_all("li", class_="vote-description")
            test_votes += len(votes)

    assert len(mp_votes) == test_votes


@pytest.fixture
def constituency_regions_soup():
    URL = "https://en.wikipedia.org/wiki/Constituencies_of_the_Parliament_of_the_United_Kingdom"
    page = requests.get(URL)
    return BeautifulSoup(page.content, "html.parser")


def test_scrape_constituency_regions(constituency_regions_soup):
    constituency_region_dict = scrape_constituency_regions()

    england_table = constituency_regions_soup.find("table", {"id": "England"})
    england_tr_elements = england_table.find_all('tr')

    assert len(constituency_region_dict) >= len(england_tr_elements) - 1


def test_get_constituencies_from_table(constituency_regions_soup):
    country_id = "Scotland"
    constituency_region_dict = get_constituencies_from_table(constituency_regions_soup, country_id)

    scotland_table = constituency_regions_soup.find("table", {"id": country_id})
    scotland_tr_elements = scotland_table.find_all('tr')

    assert len(constituency_region_dict) == len(scotland_tr_elements) - 1

