import requests
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
        if votes and isinstance(votes, list):
            self.votes = votes
        else:
            err_msg = f"Votes data is missing or invalid for MP id: {self.id}."
            logger.critical(err_msg)
            raise ValueError(err_msg)