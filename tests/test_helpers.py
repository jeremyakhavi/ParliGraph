import json
import random
import sys
import os
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(parent_dir)
from person import MP

def generate_sample_mps(num_mps):
    sample_mps = []
    parties = ['Labour', 'Conservative']
    regions = ['London', 'South East', 'East Midlands', 'North East', 'North West', 'Yorkshire']

    for i in range(num_mps):
        mp = {
            'id': i + 1,
            'name': f'MP {i + 1}',
            'party': random.choice(parties),
            'constituency': f'Constituency {i + 1}',
            'region': random.choice(regions),
            'gender': random.choice(['M', 'F']),
            'start_date': random.choice(['2019-01-01', '2015-01-01', '2010-01-01']),
            'votes': [
                ('Policy 1', 'voted_for', 0.75),
                ('Policy 2', 'voted_against', 0.9),
                ('Policy 3', 'vote_split', 0.5),
            ]
        }
        sample_mps.append(mp)

    return sample_mps

def save_sample_mps_to_file(sample_mps, filename):
    with open(filename, 'w') as f:
        json.dump(sample_mps, f)

def load_sample_mps_from_file(filename):
    with open(filename, 'r') as f:
        sample_mps_data = json.load(f)
    
    sample_mps = []
    for mp_data in sample_mps_data:
        mp = MP(
            id=mp_data['id'],
            name=mp_data['name'],
            party=mp_data['party'],
            constituency=mp_data['constituency'],
            gender=mp_data['gender'],
            start_date=mp_data['start_date']
        )
        mp.set_region(mp_data['region'])
        mp.set_votes(mp_data['votes'])
        sample_mps.append(mp)

    return sample_mps

if __name__ == '__main__':
    # Generate a random list of 10 MPs
    sample_mps = generate_sample_mps(10)

    # Save the list of MPs to the sample_mps.json file
    save_sample_mps_to_file(sample_mps, 'sample_mps.json')