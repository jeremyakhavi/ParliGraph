import requests
import time
from logger_config import get_logger

logger = get_logger(__name__)

class MP:
    def __init__(self, id, name, party, constituency, gender, start_date):
        self.id = id
        self.name = name
        self.twfy_id = None
        self.party = party
        self.constituency = constituency.lower()
        self.region = None
        self.votes = []
        self.gender = gender
        self.start_date = start_date
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
    url = 'https://members-api.parliament.uk/api/Members/Search'
    params = {'take': 20, 'skip': 0, 'IsCurrentMember': True, 'House': 1}

    mp_dict = {}
    max_retries = 30
    retry_count = 0

    while True:
        response = requests.get(url, params=params)
        
        if response.status_code != 200:
            logger.debug(f'Get Members API request failed with code: {response.status_code}, {response.json()}')
            retry_count += 1
            if retry_count >= max_retries:
                logger.critical("Max retries reached. Exiting.")
                raise(RecursionError)
            time.sleep(5)
            continue

        data = response.json()
        for mp in data['items']:
            party = mp['value']['latestParty']['name']
            if party == 'Labour (Co-op)':
                party = 'Labour'
            
            mp_obj = MP(id=mp['value']['id'], name= mp['value']['nameDisplayAs'], party=party, 
                        constituency=mp['value']['latestHouseMembership']['membershipFrom'],
                        gender=mp['value']['gender'],
                        start_date=mp['value']['latestHouseMembership']['membershipStartDate'].split("T")[0])
            mp_dict[mp_obj.constituency] = mp_obj

        if len(mp_dict) == data['totalResults']:
            break

        params['skip'] += params['take']
        logger.debug(f"Members API Search params: {params}")

    return mp_dict
