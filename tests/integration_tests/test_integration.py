import pytest
from dotenv import load_dotenv
import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
grandparent_dir = os.path.abspath(os.path.join(parent_dir, os.pardir))
sys.path.append(parent_dir)
sys.path.append(grandparent_dir)
from test_helpers import load_sample_mps_from_file
import database
from database import Database

@pytest.fixture(scope="module")
def neo4j_driver(sample_mps):
    load_dotenv()
    driver = Database.init_driver(os.getenv("NEO4J_URI_TEST"), os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))

    for mp in sample_mps:
        # Create a person in the database using the create_person function
        database.create_person(driver, mp)

    yield driver

    # Clear the database after tests are complete
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")

    driver.close()


def get_mp_by_name(neo4j_driver, name):
    """
    Retrieves an MP node from the Neo4j database based on the MP's name.
    """
    with neo4j_driver.session() as session:
        result = session.run("MATCH (m:MP {name: $name}) RETURN m", name=name)
        mp_node = result.single()
        if mp_node:
            return dict(mp_node['m'])
        else:
            return None
        
def get_mps_by_party(neo4j_driver, party):
    with neo4j_driver.session() as session:
        result = session.run("""
            MATCH (m:MP)-[:IS_A_MEMBER_OF]->(p:Party {name: $party})
            RETURN m.name
            """, party=party)
        
        mps_by_party = [record['m.name'] for record in result]

        return mps_by_party
    
def get_mps_by_region(neo4j_driver, region):
    with neo4j_driver.session() as session:
        result = session.run("""
            MATCH (m:MP)-[:REPRESENTS_REGION]->(r:Region {name: $region})
            RETURN m.name
            """, region=region)
        
        mps_by_region = [record['m.name'] for record in result]

        return mps_by_region





@pytest.fixture(scope="module")
def sample_mps():
    return load_sample_mps_from_file('sample_mps.json')

def test_integration_create_person(neo4j_driver, sample_mps):

    for mp in sample_mps:
        # Nodes are created in database using create_person function in neo4j_driver fixture  
        # Fetch the MP from the database using the get_mp_by_name function
        mp_from_db = get_mp_by_name(neo4j_driver, mp.name)

        # Verify that the MP data in the database matches the data from the API
        assert mp_from_db["name"] == mp.name
        assert mp_from_db["constituency"] == mp.constituency
        assert mp_from_db["gender"] == mp.gender

def test_mp_voting_records(neo4j_driver, sample_mps):
    for mp in sample_mps:
        with neo4j_driver.session() as session:
            for vote in mp.votes:
                policy_name, vote_direction, strength = vote
                vote_direction = vote_direction.upper()

                result = session.run(f"""
                    MATCH (m:MP {{name: $name}})-[r:{vote_direction}]->(p:Policy {{name: $p_name}})
                    RETURN r.strength, p.name
                """, name=mp.name, p_name=policy_name)

                record_from_db = result.single()
                assert record_from_db['r.strength'] == strength and record_from_db['p.name'] == policy_name

def test_query_mps_by_party(neo4j_driver, sample_mps):
    party = 'Labour'
    expected_mps = [mp for mp in sample_mps if mp.party == party]
    mps_by_party = get_mps_by_party(neo4j_driver, party)

    assert len(expected_mps) == len(mps_by_party)
    for mp in expected_mps:
        assert mp.name in mps_by_party

def test_query_mps_by_region(neo4j_driver, sample_mps):
    region = 'London'
    expected_mps = [mp for mp in sample_mps if mp.region == region]
    mps_by_region = get_mps_by_region(neo4j_driver, region)
    assert len(expected_mps) == len(mps_by_region)
    for mp in expected_mps:
        assert mp.name in mps_by_region

