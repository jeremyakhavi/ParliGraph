import requests
import time
from logger_config import get_logger

logger = get_logger(__name__)

class MP:
    def __init__(self, id, party, constituency, gender, start_date):
        self.id = id
        self.twfy_id = None
        self.party = party
        self.constituency = constituency.lower()
        self.region = None
        self.votes = []
        self.gender = gender
        self.start_date = start_date
        self.name = None
        self.electorate = None
        self.turnout = None
        self.majority = None
        self.govt_post = None

    def __str__(self):
        return f"MP object: id={self.id}\ntwfy_id={self.twfy_id}\nparty={self.party}\nconstituency={self.constituency}\n\
                gender={self.gender}\nstart_date={self.start_date}\nname={self.name}\n\
                electorate={self.electorate}\nturnout={self.turnout}\nmajority={self.majority}\nvotes={self.votes}"

    def set_election_result(self):
        url = f'https://members-api.parliament.uk/api/Members/{self.id}/LatestElectionResult'
        response = requests.get(url)

        if response.status_code != 200:
            raise Exception(f'API request failed with response code {response.status_code}')
        
        data = response.json()

        if 'value' in data:
            self.electorate = data['value'].get('electorate')
            self.turnout = data['value'].get('turnout')
            self.majority = data['value'].get('majority')
        else:
            logger.error('Election result data is missing or invalid.')

    def set_twfy_id_name(self, twfy_dict):
        if 'name' in twfy_dict and 'twfy_id' in twfy_dict:
            self.name = twfy_dict['name']
            self.twfy_id = twfy_dict['twfy_id']
        else:
            err_msg = f"TheyWorkForYou dictionary is missing required keys 'name' and/or 'twfy_id' for MP id: {self.id}"
            logger.critical(err_msg)
            raise ValueError(err_msg)

    def set_region(self, region):
        if region:
            self.region = region
        else:
            logger.error(f"Region value is missing or invalid for MP id: {self.id}.")

    def set_govt_post(self, govt_post):
        if govt_post:
            self.govt_post = govt_post
        else:
            logger.error(f"Government post value is missing or invalid for MP id: {self.id}.")

    def set_votes(self, votes):
        if isinstance(votes, list):
            self.votes = votes
        else:
            err_msg = f"Votes data is invalid for MP id: {self.id}."
            logger.critical(err_msg)
            raise ValueError(err_msg)
        
def get_mps_from_members_api():
    logger.info("Getting list of MPs from members API")
    # Set up the API endpoint and request parameters
    url = 'https://members-api.parliament.uk/api/Members/Search'
    params = {'take': 20, 'skip': 0, 'IsCurrentMember': True, 'House': 1}

    mp_dict = {}

    # Loop through each page of results until we've retrieved all MPs
    while True:
        # Make the API request with the current pagination parameters
        response = requests.get(url, params=params)
        # If response isn't valid, wait 5 seconds before trying again
        if response.status_code != 200:
            logger.debug(f'Get Members API request failed with code: {response.status_code}, {response.json()}')
            time.sleep(5)
            continue
        # Parse the response data as JSON
        data = response.json()

        # Extract the MPs from the response and add them to our list
        for mp in data['items']:       
            party = mp['value']['latestParty']['name']
            # Labour (Co-op) MPs are generally regarded as Labour Party MPs
            if party == 'Labour (Co-op)':
                party = 'Labour'
            
            mp_obj = MP(id=mp['value']['id'], party=party, 
                        constituency=mp['value']['latestHouseMembership']['membershipFrom'],
                        gender=mp['value']['gender'],
                        start_date=mp['value']['latestHouseMembership']['membershipStartDate'].split("T")[0])
            # add to mp dictionary, with key as constituency (as constituency is unique for each MP)
            mp_dict[mp_obj.constituency] = mp_obj

        # Check if we've retrieved all MPs
        if len(mp_dict) == data['totalResults']:
            break
        # Update the pagination parameters for the next API request
        params['skip'] += params['take']
        logger.debug(f"Members API Search params: {params}")
    
    return mp_dict