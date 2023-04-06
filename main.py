import time
import requests
import json
from person import MP
import os
from database import Database
import scraper
import traceback
from tqdm import tqdm
from dotenv import load_dotenv

API_KEY = 'ByYxD9BjmESCCbdKusCwZCCj'

def jprint(obj):
    """
    Create nicely formatted string of Python JSON object
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

def get_mps_from_members_api():
    print('Getting members')
    # Set up the API endpoint and request parameters
    url = 'https://members-api.parliament.uk/api/Members/Search'
    params = {'take': 20, 'skip': 0, 'IsCurrentMember': True, 'House': 1}

    mp_dict = {}

    # Loop through each page of results until we've retrieved all MPs
    while True:
        # Make the API request with the current pagination parameters
        response = requests.get(url, params=params)
        # Check for errors in the response
        if response.status_code != 200:
            print(f'Get Members API request failed with code: {response.status_code}')
            time.sleep(5)
            continue
        # Parse the response data as JSON
        data = response.json()

        # Extract the MPs from the response and add them to our list
        for mp in data['items']:
            mp_obj = MP(id=mp['value']['id'], party=mp['value']['latestParty']['name'], 
                        constituency=mp['value']['latestHouseMembership']['membershipFrom'],
                        gender=mp['value']['gender'],
                        start_date=mp['value']['latestHouseMembership']['membershipStartDate'])
            
            mp_dict[mp_obj.constituency] = mp_obj

        # Check if we've retrieved all MPs
        if len(mp_dict) == data['totalResults']:
            break

        # Update the pagination parameters for the next API request
        params['skip'] += params['take']
        print(params)
    
    return mp_dict

def get_twfy_ids():
    """
    Submit get request to TheyWorkForYou (twfy)
    Extract relevant ids and names from response and put in dictionary
    Return dictionary
    """
    print('Getting twfy ids')
    twfy_dict = {}

    url = 'https://www.theyworkforyou.com/api/getMPs'
    params = {'key': API_KEY, 'output': 'json'}

    response = requests.get(url, params=params)
    data = response.json()
    for mp in data:
        constituency = mp['constituency'].lower()
        twfy_dict[constituency] = {'name': mp['name'], 'twfy_id': mp['person_id']}

    return twfy_dict

def get_govt_posts_from_members_api():
    print('Getting government posts')
    url = 'https://members-api.parliament.uk/api/Posts/GovernmentPosts'
    govt_post_dict = {}
    response = requests.get(url)
    data = response.json()
    for govt_post in data:
        mp_id = govt_post['value']['postHolders'][0]['member']['value']['id']
        post_name = govt_post['value']['name']
        govt_post_dict[mp_id] = post_name
    
    return govt_post_dict

def main():
    # load environment variables from .env file
    load_dotenv()
    driver = Database.init_driver(os.getenv("NEO4J_URI"), os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))

    constituency_region_dict = scraper.scrape_constituency_regions()
    if constituency_region_dict is None:
        print('Error getting constituency - region mapping')

    twfy_dict = get_twfy_ids()
    govt_post_dict = get_govt_posts_from_members_api()

    mp_dict = get_mps_from_members_api()
    
    for mp in tqdm(mp_dict.values()):       
        mp.set_region(constituency_region_dict)
        mp.set_twfy_id_name(twfy_dict)
        mp.set_election_result()
        
        if mp.id in govt_post_dict:
            mp.set_govt_post(govt_post_dict[mp.id])
        try:
            scraper.scrape_mp_votes(mp)
        except Exception:
            traceback.print_exc()
        finally:
            try:
                create_person(driver, mp)
            except Exception:
                traceback.print_exc()
    

    
    # mp_list = parse_mp_data_from_file('mp-data.json', constituency_region_dict)
    # print(len(mp_list))
    # for mp in tqdm(mp_list):
    #     try:
    #         scraper.scrape_mp_votes(mp)
    #     except Exception:
    #         traceback.print_exc()
    #     finally:
    #         try:
    #             create_person(driver, mp)
    #         except Exception:
    #             traceback.print_exc()

    # for mp in mp_list:
    #     print(vars(mp))

if __name__ == '__main__':
    main()


