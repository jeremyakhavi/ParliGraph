from neo4j import GraphDatabase
from logger_config import get_logger

logger = get_logger(__name__)

class Database(object):
    _instance = None
    driver = None

    def __init__(self):
        raise RuntimeError('Call init_driver() instead')

    @classmethod
    def init_driver(cls, uri, username, password):
        """
        Initiate the Neo4j Driver
        """
        if cls._instance is None:
            print('Creating new driver')
            cls._instance = cls.__new__(cls)

            # Create an instance of the driver
            cls.driver = GraphDatabase.driver(uri, auth=(username, password))

            # Verify connectivity
            cls.driver.verify_connectivity()
        else:
            print('Already intialised')

        return cls.driver

    @classmethod
    def get_driver(cls):
        """
        Get the instance of the Neo4j Driver created in the `init_driver` function
        """
        if cls.driver is None:
            print('Driver has not been initialised, initialise with `init_driver` function')
        
        return cls.driver

    @classmethod
    def close_driver(cls):
        """
        If the driver has been instantiated, close it and all remaining open sessions
        """
        if cls.driver is not None:
            print("Driver is not none")
            cls.driver.close()
            cls.driver = None
            cls._instance = None
        else:
            print("Driver is none")

        return None
    
def create_person_work(tx, name, party, constituency, region, gender,
                    start_date, electorate, turnout, majority, govt_post):
    return tx.run("MERGE (m:MP {name: $name}) ON CREATE SET m.constituency = $constituency,\
                                                            m.gender = $gender, m.start_date = $start_date,\
                                                            m.electorate = $electorate, m.turnout = $turnout,\
                                                            m.majority = $majority, m.govt_post = $govt_post \
                MERGE (p:Party {name: $party}) \
                MERGE (r:Region {name: $region}) \
                MERGE (m)-[:IS_A_MEMBER_OF]->(p) \
                MERGE (m)-[:REPRESENTS_REGION]->(r) \
                RETURN m, p, r",
                name=name, party=party, constituency=constituency, region=region, 
                gender=gender, start_date=start_date, electorate=electorate, 
                turnout=turnout, majority=majority, govt_post=govt_post).single()

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

def create_vote_split_work(tx, name, vote, strength):
    return tx.run("MATCH (m:MP {name: $name}) \
                MERGE (p:Policy {name: $vote}) \
                MERGE (m)-[:VOTE_SPLIT {strength: $strength}]->(p) \
                RETURN p",
                name=name, vote=vote, strength=strength).single()

def create_person(driver, mp):
    logger.info(f"Creating node for {mp.name}")
    # Create a Session for the `people` database
    session = driver.session()
    # Create a node within a write transaction
    record = session.execute_write(create_person_work,
                            name=mp.name, 
                            party=mp.party, 
                            constituency=mp.constituency, 
                            region=mp.region,
                            gender=mp.gender,
                            start_date=mp.start_date,
                            electorate=mp.electorate,
                            turnout=mp.turnout,
                            majority=mp.majority,
                            govt_post=mp.govt_post)
    for vote in mp.votes:
        # if MP voted in favour of or against the issue then add relationship to graph
        if vote[1] == 'voted_for':
            session.execute_write(create_vote_for_work,
                                    name=mp.name, vote=vote[0], strength=vote[2])

        elif vote[1] == 'voted_against':
            session.execute_write(create_vote_against_work,
                                    name=mp.name, vote=vote[0], strength=vote[2])
        elif vote[1] == 'vote_split':
            session.execute_write(create_vote_split_work,
                                    name=mp.name, vote=vote[0], strength=vote[2])
    # Get the `p` value from the first record
    person = record["p"]

    # Close the session
    session.close()

    # Return the property from the node
    return person["name"]