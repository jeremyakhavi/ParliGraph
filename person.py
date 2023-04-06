import requests

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

        self.electorate = data['value']['electorate']
        self.turnout = data['value']['turnout']
        self.majority = data['value']['majority']

    def set_twfy_id_name(self, twfy_dict):
        self.name = twfy_dict[self.constituency]['name']
        self.twfy_id = twfy_dict[self.constituency]['twfy_id']

    def set_region(self, constituency_region_dict):
        self.region = constituency_region_dict[self.constituency]

    def set_govt_post(self, govt_post):
        self.govt_post = govt_post

    def set_votes(self, votes):
        self.votes = votes