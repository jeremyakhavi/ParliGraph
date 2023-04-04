import time
import requests
import json
from person import MP
import os
from database import Database
import scraper
import traceback
from tqdm import tqdm

API_KEY = 'ByYxD9BjmESCCbdKusCwZCCj'

def twfy_get(payload):
    """
    Submit get request to TheyWorkForYou (twfy) and return response
    """
    service_url = 'https://www.theyworkforyou.com/api/'
    payload['key'] = API_KEY
    payload['output'] = 'json'

    response = requests.get(service_url, params=payload)
    return response

def jprint(obj):
    """
    Create nicely formatted strong of Python JSON object
    """
    text = json.dumps(obj, sort_keys=True, indent=4)
    print(text)

def mp_data_to_file():
    response = requests.get(SERVICE_URL, params=payload)
    data = response.json()
    with open('mp-data.json', 'w') as f:
        json.dump(data, f)
    jprint(data)

def parse_mp_data_from_file(filepath, constituency_region_dict):
    mp_list = []
    with open(filepath, 'r') as f:
        data = json.load(f)
    for person in data:
        region = constituency_region_dict[person['constituency']]
        mp = MP(person['person_id'], person['name'], person['party'], person['constituency'], region)
        mp_list.append(mp)
    return mp_list

def get_region_from_constituency(dict, constituency):
    return dict[constituency]

def create_person_work(tx, name, party, constituency, region):
    return tx.run("MERGE (m:MP {name: $name}) ON CREATE SET m.constituency = $constituency\
                   MERGE (p:Party {name: $party}) \
                   MERGE (r:Region {name: $region}) \
                   MERGE (m)-[:IS_A_MEMBER_OF]->(p) \
                   MERGE (m)-[:REPRESENTS_REGION]->(r) \
                   RETURN m, p, r",
        name=name, party=party, constituency=constituency, region=region).single()

def create_vote_for_work(tx, name, vote, strength):
    return tx.run("MATCH (m:MP {name: $name}) \
                   MERGE (p:Policy {name: $vote}) \
                   MERGE (m)-[:VOTED_FOR {strength: $strength}]->(p) \
                   RETURN p",
                   name=name, vote=vote, strength=strength).single()

def create_vote_against_work(tx, name, vote, strength):
    return tx.run("MATCH (m:MP {name: $name}) \
                   MERGE (p:Policy {name: $vote}) \
                   MERGE (m)-[:VOTED_AGAINST {strength: $strength}]->(p) \
                   RETURN p",
                   name=name, vote=vote, strength=strength).single()

def create_person(driver, mp: MP):
    # print(f"Creating node for {mp.name}")
    # Create a Session for the `people` database
    session = driver.session()
    # Create a node within a write transaction
    record = session.execute_write(create_person_work,
                                    name=mp.name, party=mp.party, constituency=mp.constituency, region=mp.region)
    voted_for = ['voted for', 'generally voted for', 'consistently voted for']
    voted_against = ['voted against', 'generally voted against', 'consistently voted against']
    for vote in mp.votes:
        # if MP voted in favour of or against the issue then add relationship to graph
        if vote[1] in voted_for:
            session.execute_write(create_vote_for_work,
                                    name=mp.name, vote=vote[0], strength=vote[1])

        elif vote[1] in voted_against:
            session.execute_write(create_vote_against_work,
                                    name=mp.name, vote=vote[0], strength=vote[1])
    # Get the `p` value from the first record
    person = record["p"]

    # Close the session
    session.close()

    # Return the property from the node
    return person["name"]

def main():
    driver = Database.init_driver(os.getenv("NEO4J_URI"), os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))

    constituency_region_dict = scraper.scrape_constituency_regions()
    if constituency_region_dict is None:
        print('Error getting constituency - region mapping')
    mp_list = parse_mp_data_from_file('mp-data.json', constituency_region_dict)
    print(len(mp_list))
    for mp in tqdm(mp_list):
        try:
            scraper.scrape_mp_votes(mp)
        except Exception:
            traceback.print_exc()
        finally:
            try:
                create_person(driver, mp)
            except Exception:
                traceback.print_exc()

    for mp in mp_list:
        print(vars(mp))

if __name__ == '__main__':
    main()


