from neo4j import GraphDatabase

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
            cls.driver.close()
            cls.driver = None

            return cls.driver
