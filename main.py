import time
import requests
import json
from person import Person, MP
import os
from database import Database

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

def parse_mp_data_from_file(filepath):
    mp_list = []
    with open(filepath, 'r') as f:
        data = json.load(f)
    for person in data:
        mp = MP(person['name'], person['party'], person['constituency'])
        mp_list.append(mp)
    return mp_list

def create_person_work(tx, name, party, constituency):
    return tx.run("MERGE (m:MP {name: $name}) ON CREATE SET m.constituency = $constituency\
                   MERGE (p:Party {name: $party}) \
                   MERGE (m)-[:IS_A_MEMBER_OF]->(p) \
                   RETURN m, p",
        name=name, party=party, constituency=constituency).single()

def create_person(mp: MP):
    print(f"Creating node for {mp.name}")
    # Create a Session for the `people` database
    session = driver.session()

    # Create a node within a write transaction
    record = session.execute_write(create_person_work,
                                    name=mp.name, party=mp.party, constituency=mp.constituency)

    # Get the `p` value from the first record
    person = record["p"]

    # Close the session
    session.close()

    # Return the property from the node
    return person["name"]

driver = Database.init_driver(os.getenv("NEO4J_URI"), os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))

mp_list = parse_mp_data_from_file('mp-data.json')
for mp in mp_list:
    create_person(mp)

