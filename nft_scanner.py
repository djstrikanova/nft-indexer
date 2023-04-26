import requests
import json
import re

from pprint import pprint
from models.nft import NFT
from models.ipfs_hashes import HashTable
from models.script_status import ScriptStatus
from config.database import db_session, init_db
import time

# Constants
ATOMIC_ASSETS_API_BASE_URL = "https://eos.api.atomicassets.io/atomicassets/v1/"
LIMIT = 1000

lookforward_page_limit = 1000
lookback_page_limit = 10

init_db()


def fetch_nfts(page, order="desc"):
    url = f"{ATOMIC_ASSETS_API_BASE_URL}assets?limit={LIMIT}&page={page}&order={order}&sort=created"
    
    response = requests.get(url,timeout=30)

    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return []

    data = response.json()
    # print(json.dumps(data, indent=4))
    return data

# Returns true if the NFT was added to the database, false if it already exists
def save_nft_to_db(nft_data):
    # Check if the NFT has the required data
    try:
        collection_name = nft_data['collection']['collection_name']
        schema_name = nft_data['schema']['schema_name']
        template_id = nft_data['template']['template_id']
        asset_id = nft_data['asset_id']
        asset_immutable_data = nft_data['immutable_data']
        template_immutable_data = nft_data['template']['immutable_data']
    except KeyError:
        print("Key Error: Invalid Template, missing data\n")
        return
    except TypeError:
        print("TypeError: Invalid Template, missing data\n")
        return

    # Check if asset_id already exists in the database
    asset_id_exists = db_session.query(NFT).filter_by(asset_id=asset_id).first()

    if asset_id_exists is None:
        # Add the NFT to the database
        nft = NFT(
            asset_id=asset_id,
            collection_name=collection_name,
            schema_name=schema_name,
            template_id=template_id,
            asset_immutable_data=asset_immutable_data,
            template_immutable_data=template_immutable_data
        )
        db_session.add(nft)
        db_session.commit()
        nft_added_to_db = True
        
    else:
        print(f"NFT with asset_id {asset_id} already exists in the database\n")
        nft_added_to_db = False

    process_immutable_templates(template_immutable_data, collection_name, template_id)
    process_immutable_assets(asset_immutable_data, collection_name, asset_id)

    return nft_added_to_db


def process_immutables(immutables, collection_name, id, type):

    #Add Unique IPFS Content Hashes to Database
    hashes = []
    ipfs_regex = r"Qm[a-zA-Z\d]{43}"
    meta = {}


    #Check if IPFS Hash already exists in the database
    print(f"Parsing {type} with ID: {id} for IPFS Hashes\n")
    for key, value in immutables.items():
        try:
            if re.match(ipfs_regex, value):
                hash_exists = db_session.query(HashTable).filter_by(ipfs_hash=value).first()
                hashes.append({key: value})
                # Hash Not Found, Add to Database
                if(hash_exists is None):
                    
                    meta = {"collections":{collection_name:{type:{key:[id]}}}}
                
                    hash = HashTable(ipfs_hash=value, meta=meta)
                    db_session.add(hash)
                # Hash Found, Update meta
                else:
                    print(f"IPFS Hash {value} already exists in the database\n")
                    #Get Meta From Database
                    meta = hash_exists.meta
                    # Check of Collection Already Exists in Meta
                    if(collection_name in meta['collections']):
                            # Check if Type Already Exists in Meta
                            if(type in meta['collections'][collection_name]):
                                # Check if Tag Already Exists in Meta
                                if(key in meta['collections'][collection_name][type]):
                                    if(id in meta['collections'][collection_name][type][key]):
                                        print(f"ID:{id} Already Exists in Meta for Hash {value}")
                                    else:
                                        meta['collections'][collection_name][type][key].append(id)
                                else:
                                    meta['collections'][collection_name][type][key] = [id]
                            else:
                                meta['collections'][collection_name][type] = {key:[id]} 
                    # Collection Doesn't Exist in Meta
                    else:
                        meta['collections'][collection_name] = {type:{key:[id]}}
                    db_session.query(HashTable).filter_by(ipfs_hash=value).update({"meta": meta})                 
            
                db_session.commit()
        except TypeError:
            print(f"TypeError: Invalid {type} with ID: {id}\n")
            return
    print(hashes)

def process_immutable_templates(immutables, collection_name, id):
    return process_immutables(immutables, collection_name, id, "templates")

def process_immutable_assets(immutables, collection_name, id):
    return process_immutables(immutables, collection_name, id, "assets")

def scrape_nfts(type, reset=False):
    if reset == True:
        store_api_call_depth(0)
    

    #Default Lookback
    cur_page = 1
    num_pages_limit = lookback_page_limit


    if(type == "lookforward"):
        # Get current depth from database
        cur_page = get_api_call_depth()
        num_pages_limit = lookforward_page_limit
        print(f"Looking Forward from Beggining. Current Script Status Page: {cur_page}")
    else:
        print("Looking Backward From Latest NFTs")
        
    
    
    num_pages = 0

    while num_pages < num_pages_limit:
        page_success = False
        timeout_errors = 0
        while page_success == False:
            nfts = None
            print(f"Scraping page {cur_page}")
            try:
                if(type == "lookforward"):
                    nfts = fetch_nfts(cur_page, "asc")
                    page_success = True
                else:
                    nfts = fetch_nfts(cur_page, "desc")
                    page_success = True
            except requests.exceptions.Timeout:
                print("Timeout Error: Retrying")
                #Sleep to avoid Rate-Limit
                timeout_errors+=1
                sleeptime = 60
                if(timeout_errors > 3):
                    nfts = None
                    break
                print(f"Failed to grab Page, Sleeping for {sleeptime} seconds")
                time.sleep(sleeptime)

        if not nfts:
            print("No NFTs Found, Exiting\n")
            break

        #Count Saved NFTs to Database, if equal to number of NFT's on page that means there is no need to lookback further. 
        saved_nfts = 0

        if "success" in nfts:
            if nfts['success'] == True:
                if "data" in nfts:
                    for nft_data in nfts['data']:
                        nft_saved_to_db = save_nft_to_db(nft_data)
                        if nft_saved_to_db:
                            saved_nfts += 1
                        if type=="lookforward":
                            store_api_call_depth(cur_page)
                        else:
                            if saved_nfts == len(nfts['data']):
                                print("No New NFTs Found, Exiting\n")
                                break

                    cur_page += 1
                    num_pages += 1
                    #Sleep to avoid Rate-Limit        
                    sleeptime = 30
                    print(f"Completed Page, Sleeping for {sleeptime} seconds")
                    time.sleep(sleeptime)
                else:
                    print("Data Attribute Not Found, Exiting\n")
                    break
            else:
                print("Success Attribute found, but false, Exiting\n")
                break
        else:
            print("Success Attribute Not Found\n")
            break


def deep_scan(reset=False):
    scrape_nfts("lookforward", reset)

def lookback_scan():
    scrape_nfts("lookback")

# Store the API call depth
def store_api_call_depth(depth):
    metadata_key = "api_call_depth"
    entry = db_session.query(ScriptStatus).filter_by(key=metadata_key).first()

    if entry is None:
        # Create a new entry if it doesn't exist
        entry = ScriptStatus(key=metadata_key, value=str(depth))
        db_session.add(entry)
    else:
        # Update the existing entry
        entry.value = str(depth)

    db_session.commit()

# Retrieve the API call depth
def get_api_call_depth():
    metadata_key = "api_call_depth"
    entry = db_session.query(ScriptStatus).filter_by(key=metadata_key).first()
    if entry is not None:
        return int(entry.value)
    else:
        return 1

if __name__ == "__main__":
    # lookback_scan()
    deep_scan()