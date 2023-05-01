from neo4j import GraphDatabase
from logger_config import get_logger

logger = get_logger(__name__)

class Database(object):
    """
    Singleton class to manage the Neo4j graph database operations.
    """
    _instance = None
    driver = None

    def __init__(self):
        """
        Raises:
        RuntimeError: If the user tries to directly instantiate the class.
        """
        raise RuntimeError('Call init_driver() instead')

    @classmethod
    def init_driver(cls, uri, username, password):
        """
        Initialize the Neo4j driver with the given connection parameters.
        If the driver has already been initialized, returns the existing instance.

        Args:
            uri (str): The connection URI for the Neo4j database.
            username (str): The username for authentication.
            password (str): The password for authentication.

        Returns:
            The initialized Neo4j driver.
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
        Get the instance of the Neo4j driver created in the `init_driver` function.

        Returns:
            The Neo4j driver instance, or None if not initialized.
        """
        if cls.driver is None:
            print('Driver has not been initialised, initialise with `init_driver` function')
        
        return cls.driver

    @classmethod
    def close_driver(cls):
        """
        If the driver has been instantiated, close it and all remaining open sessions.

        Returns:
            None
        """
        if cls.driver is not None:
            logger.info("Driver is not none")
            cls.driver.close()
            cls.driver = None
            cls._instance = None
        else:
            logger.info("Driver is none")

        return None
    
def create_person_work(tx, name, party, constituency, region, gender,
                    start_date, electorate, turnout, majority, govt_post):
    """
    Function to be executed within a write transaction to create or update an MP node
    with associated Party, Region, and Start_Date nodes, and relationships between them.

    Args:
        tx: The transaction object.
        name (str): The name of the MP.
        party (str): The name of the party the MP belongs to.
        constituency (str): The constituency the MP represents.
        region (str): The region the MP represents.
        gender (str): The gender of the MP.
        start_date (str): The date the MP joined the House.
        electorate (int): The size of the electorate in the MP's constituency.
        turnout (int): The voter turnout in the MP's constituency.
        majority (int): The majority that the MP holds in their constituency.
        govt_post (str): Any government post held by the MP.

    Returns:
        A Record object containing the created or updated nodes and relationships.
    """
    return tx.run("MERGE (m:MP {name: $name}) SET m.constituency = $constituency,\
                                                           m.gender = $gender,\
                                                           m.electorate = $electorate, m.turnout = $turnout,\
                                                           m.majority = $majority, m.govt_post = $govt_post \
                MERGE (p:Party {name: $party}) \
                MERGE (r:Region {name: $region}) \
                MERGE (s:Start_Date {date: $start_date}) \
                MERGE (m)-[:IS_A_MEMBER_OF]->(p) \
                MERGE (m)-[:REPRESENTS_REGION]->(r) \
                MERGE (m)-[:JOINED_HOUSE]->(s)  \
                RETURN m, p, r, s",
                name=name, party=party, constituency=constituency, region=region, 
                gender=gender, start_date=start_date, electorate=electorate, 
                turnout=turnout, majority=majority, govt_post=govt_post).single()

def create_vote_for_work(tx, name, vote, strength):
    """
    Function to be executed within a write transaction to create or update an MP node's
    VOTED_FOR relationship with a Policy node.

    Args:
        tx: The transaction object.
        name (str): The name of the MP.
        vote (str): The name of the policy the MP voted for.
        strength (float): The strength of the MP's vote.

    Returns:
        A Record object containing the created or updated nodes and relationships.
    """
    return tx.run("MATCH (m:MP {name: $name}) \
                MERGE (p:Policy {name: $vote}) \
                MERGE (m)-[:VOTED_FOR {strength: $strength}]->(p) \
                RETURN p",
                name=name, vote=vote, strength=strength).single()

def create_vote_against_work(tx, name, vote, strength):
    """
    Function to be executed within a write transaction to create or update an MP node's
    VOTED_AGAINST relationship with a Policy node.

    Args:
        tx: The transaction object.
        name (str): The name of the MP.
        vote (str): The name of the policy the MP voted against.
        strength (float): The strength of the MP's vote.

    Returns:
        A Record object containing the created or updated nodes and relationships.
    """
    return tx.run("MATCH (m:MP {name: $name}) \
                MERGE (p:Policy {name: $vote}) \
                MERGE (m)-[:VOTED_AGAINST {strength: $strength}]->(p) \
                RETURN p",
                name=name, vote=vote, strength=strength).single()

def create_vote_split_work(tx, name, vote, strength):
    """
    Function to be executed within a write transaction to create or update an MP node's
    VOTE_SPLIT relationship with a Policy node.

    Args:
        tx: The transaction object.
        name (str): The name of the MP.
        vote (str): The name of the policy the MP's vote was split on.
        strength (float): The strength of the MP's vote.

    Returns:
        A Record object containing the created or updated nodes and relationships.
    """
    return tx.run("MATCH (m:MP {name: $name}) \
                MERGE (p:Policy {name: $vote}) \
                MERGE (m)-[:VOTE_SPLIT {strength: $strength}]->(p) \
                RETURN p",
                name=name, vote=vote, strength=strength).single()

def create_person(driver, mp):
    """
    Creates or updates an MP node and its associated relationships in the graph database.
    
    Args:
    driver (neo4j.Driver): The Neo4j driver instance.
    mp (MP): An MP object containing the MP's attributes and voting records.

    Returns:
        The name of the created or updated MP node.
    """
    logger.info(f"Creating node for {mp.name}")
    session = driver.session()
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
        # If MP voted in for / against / split the issue then add relationship to graph
        if vote[1] == 'voted_for':
            session.execute_write(create_vote_for_work,
                                    name=mp.name, vote=vote[0], strength=vote[2])

        elif vote[1] == 'voted_against':
            session.execute_write(create_vote_against_work,
                                    name=mp.name, vote=vote[0], strength=vote[2])
        elif vote[1] == 'vote_split':
            session.execute_write(create_vote_split_work,
                                    name=mp.name, vote=vote[0], strength=vote[2])
    # Get the value from the first record
    person = record["p"]
    session.close()
    # Return the property from the node
    return person["name"]