import pytest
import requests
from unittest.mock import MagicMock, patch
import sys
import os
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(parent_dir)
from person import MP

@pytest.fixture
def mp_instance():
    yield MP(1, 'Party', 'Constituency', 'M', '2022-01-01')

def test_MP_init(mp_instance):
    assert mp_instance.id == 1
    assert mp_instance.party == 'Party'
    assert mp_instance.constituency == 'constituency'
    assert mp_instance.gender == 'M'
    assert mp_instance.start_date == '2022-01-01'

def test_set_election_result(mp_instance):
    response_data = {
        'value': {
            'electorate': 1000,
            'turnout': 500,
            'majority': 200,
        }
    }
    with patch('requests.get', MagicMock(return_value=MagicMock(status_code=200, json=lambda: response_data))):
        mp_instance.set_election_result()

    assert mp_instance.electorate == 1000
    assert mp_instance.turnout == 500
    assert mp_instance.majority == 200

def test_set_twfy_id_name(mp_instance):
    twfy_dict = {'name': 'MP Name', 'twfy_id': 2}
    mp_instance.set_twfy_id_name(twfy_dict)

    assert mp_instance.name == 'MP Name'
    assert mp_instance.twfy_id == 2

def test_set_region(mp_instance):
    mp_instance.set_region('Region Name')

    assert mp_instance.region == 'Region Name'

def test_set_govt_post(mp_instance):
    mp_instance.set_govt_post('Government Post')

    assert mp_instance.govt_post == 'Government Post'

def test_set_votes(mp_instance):
    votes = [{'vote_id': 1, 'vote_value': 'yes'}]
    mp_instance.set_votes(votes)

    assert mp_instance.votes == votes

def test_set_election_result_api_failure(mp_instance):
    with patch('requests.get', MagicMock(return_value=MagicMock(status_code=404))):
        with pytest.raises(Exception):
            mp_instance.set_election_result()

def test_set_election_result_missing_data(mp_instance):
    response_data = {}
    with patch('requests.get', MagicMock(return_value=MagicMock(status_code=200, json=lambda: response_data))):
        mp_instance.set_election_result()

    assert mp_instance.electorate is None
    assert mp_instance.turnout is None
    assert mp_instance.majority is None

def test_set_twfy_id_name_missing_keys(mp_instance):
    twfy_dict = {'name': 'MP Name'}

    with pytest.raises(ValueError):
        mp_instance.set_twfy_id_name(twfy_dict)

def test_set_region_empty_string(mp_instance):
    mp_instance.set_region('')

    assert mp_instance.region is None

def test_set_govt_post_empty_string(mp_instance):
    mp_instance.set_govt_post('')

    assert mp_instance.govt_post is None

def test_set_votes_empty_list(mp_instance):
    mp_instance.set_votes([])

    assert mp_instance.votes == []

def test_set_votes_not_list(mp_instance):
    with pytest.raises(ValueError):
        mp_instance.set_votes('not a list')
