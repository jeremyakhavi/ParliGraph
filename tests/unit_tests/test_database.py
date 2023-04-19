from unittest.mock import patch
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
grandparent_dir = os.path.abspath(os.path.join(parent_dir, os.pardir))
sys.path.append(parent_dir)
sys.path.append(grandparent_dir)
from database import Database

import pytest
from unittest.mock import MagicMock, patch
from database import Database

@pytest.fixture
def mock_driver():
    return MagicMock()

@pytest.fixture
def mock_driver_connectivity(mock_driver):
    mock_driver.verify_connectivity = MagicMock()
    return mock_driver

def test_init_driver(mock_driver_connectivity):
    with patch('neo4j.GraphDatabase.driver', return_value=mock_driver_connectivity):
        driver = Database.init_driver('test_uri', 'test_username', 'test_password')

    assert driver is not None
    assert driver.verify_connectivity.called

def test_init_driver_already_initialized(mock_driver_connectivity):
    with patch('neo4j.GraphDatabase.driver', return_value=mock_driver_connectivity):
        Database.init_driver('test_uri', 'test_username', 'test_password')
        driver = Database.init_driver('test_uri', 'test_username', 'test_password')

    assert driver is not None
    assert driver.verify_connectivity.call_count == 1

def test_get_driver(mock_driver_connectivity):
    with patch('neo4j.GraphDatabase.driver', return_value=mock_driver_connectivity):
        Database.init_driver('test_uri', 'test_username', 'test_password')
        driver = Database.get_driver()

    assert driver is not None

def test_get_driver_not_initialized():
    Database.close_driver()
    driver = Database.get_driver()

    assert driver is None

def test_close_driver(mock_driver_connectivity):
    with patch('neo4j.GraphDatabase.driver', return_value=mock_driver_connectivity):
        Database.init_driver('test_uri', 'test_username', 'test_password')

        closed_driver = Database.close_driver()

    assert closed_driver is None
    assert mock_driver_connectivity.close.called


def test_init_driver_multiple_connections(mock_driver_connectivity):
    with patch('neo4j.GraphDatabase.driver', return_value=mock_driver_connectivity) as mock_driver_function:
        driver1 = Database.init_driver('test_uri1', 'test_username1', 'test_password1')
        driver2 = Database.init_driver('test_uri2', 'test_username2', 'test_password2')

    assert driver1 is not None
    assert driver2 is not None
    assert driver1 == driver2

    # Ensure that the driver was only initialized once
    assert mock_driver_function.call_count == 1