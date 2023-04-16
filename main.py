from person import get_mps_from_members_api
import os
from database import Database, create_person
import scraper
import traceback
from tqdm import tqdm
from dotenv import load_dotenv
from logger_config import get_logger

logger = get_logger(__name__)

def main():
    # load environment variables from .env file
    load_dotenv()
    driver = Database.init_driver(os.getenv("NEO4J_URI"), os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))

    constituency_region_dict = scraper.scrape_constituency_regions()
    if constituency_region_dict is None:
        logger.error('Error getting constituency - region mapping')

    twfy_dict = scraper.get_twfy_ids()
    govt_post_dict = scraper.get_govt_posts_from_members_api()

    mp_dict = get_mps_from_members_api()
    
    for mp in tqdm(mp_dict.values()):       
        mp.set_region(constituency_region_dict[mp.constituency])
        mp.set_twfy_id_name(twfy_dict[mp.constituency])
        mp.set_election_result()
        
        if mp.id in govt_post_dict:
            mp.set_govt_post(govt_post_dict[mp.id])
        try:
            votes = scraper.scrape_mp_votes(mp.twfy_id)
            mp.set_votes(votes)
        except Exception:
            traceback.print_exc()
        finally:
            try:
                create_person(driver, mp)
            except Exception:
                traceback.print_exc()

if __name__ == '__main__':
    main()