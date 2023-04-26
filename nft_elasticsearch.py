from elasticsearch import Elasticsearch
from elasticsearch import helpers

from models.ipfs_hashes import HashTable
from config.database import db_session, init_db
from urllib.parse import urlparse
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.sql.expression import cast, literal
from sqlalchemy import String
from pprint import pprint

import os
import ssl

from config.settings import ELASTIC_SEARCH_FULL_URL_KEY

# Replace 'your_searchly_api_key' with your actual Searchly API key
searchly_api_key = ELASTIC_SEARCH_FULL_URL_KEY

# Elasticsearch connection configuration

es = Elasticsearch([searchly_api_key])

  
    
def create_index(index_name, mapping):
    if not es.indices.exists(index=index_name):
        es.indices.create(index=index_name, body=mapping)
        print(f"Index '{index_name}' created.")
    else:
        print(f"Index '{index_name}' already exists.")


def update_index_mappings(index_name, new_mappings):
    es.indices.put_mapping(index=index_name, body=new_mappings)
    print(f"Index '{index_name}' mappings updated.")


def delete_index(index_name):
    if es.indices.exists(index=index_name):
        es.indices.delete(index=index_name)
        print(f"Index '{index_name}' deleted.")
    else:
        print(f"Index '{index_name}' does not exist.")


def index_document(index_name, doc_id, doc_body):
    try:
        res = es.index(index=index_name, id=doc_id, body=doc_body)
        print(f"Document indexed: {res['_id']}")
        return res['_id']
    except Exception as e:
        print(f"Error indexing document: {e}")
        return None
    

def sync_local_db_to_es(index_name):
    hashes = get_all_ipfs_from_db()
    index_content_hashes(index_name, hashes)


def get_all_ipfs_from_db():
    init_db()
    ipfs_hashes = db_session.query(HashTable).filter(HashTable.content_description != None).filter(cast(HashTable.content_description, String) != cast(literal(JSON.NULL, JSON()), String)).all()    
    return ipfs_hashes


def get_bulk_actions(index_name,ipfs_hashes):
    for ipfs_hash in ipfs_hashes:
        # Prepare the document body for Elasticsearch

        #Prepare ViT-L-14/openai
        caption_model_vit_l_14_openai = ""
        if "models" in ipfs_hash.content_description:
            if 'ViT-L-14/openai' in ipfs_hash.content_description['models']:
                caption_model_vit_l_14_openai = ipfs_hash.content_description['models']['ViT-L-14/openai']
        caption_model_vit_l_14_openai_f1 = extract_phrases(caption_model_vit_l_14_openai,1)

        #Prepare Collections
        associated_collections = []
        if "collections" in ipfs_hash.meta:
            associated_collections = list(ipfs_hash.meta['collections'].keys())
                
        # Remove slashes from ipfs_hash for Elasticsearch
        new_hash = ipfs_hash.ipfs_hash.replace('/', '_')

        print(new_hash)
        doc = {
            "_index": index_name,
            "_id": new_hash,
            "_source": {
                "ipfs_hash": ipfs_hash.ipfs_hash,
                "file_type": ipfs_hash.file_type,
                "file_size": 0,

                "caption_model_vit_l_14_openai": caption_model_vit_l_14_openai,
                "caption_model_vit_l_14_openai_f1": caption_model_vit_l_14_openai_f1,

                "associated_collections": associated_collections,

            }
        }

        yield doc


# Expected HashTable Model array for ipfas_hashes
def index_content_hashes(index_name, ipfs_hashes):
    init_db()
    # get_bulk_actions(index_name, ipfs_hashes)
    helpers.bulk(es, get_bulk_actions(index_name, ipfs_hashes))


def replace_special_chars(obj):
    new_obj = {}
    for key, value in obj.items():
        new_key = key.replace('-', '_').replace('/', '_')
        if isinstance(value, dict):
            new_value = replace_special_chars(value)
        else:
            new_value = value
        new_obj[new_key] = new_value
    return new_obj

# Function to check the connection to Elasticsearch
def test_connection():
    try:
        if es.ping():
            print("Connected to Elasticsearch")
        else:
            print("Could not connect to Elasticsearch")
    except Exception as e:
        print(f"Error connecting to Elasticsearch: {e}")

def search_text(index, text):
    query = {
        "query": {
            "match":{
                "content_description.models.ViT_L_14_openai":  text

            }
        }
    }
    return es.search(index=index, body=query)

def extract_phrases(input_string, max_phrases=3):
    phrases = input_string.split(",")[:max_phrases]
    return ", ".join(phrases)


# Test the connection to Elasticsearch
if __name__ == "__main__":
    # Nested structures seems to break and make things not work as expected, just flatten everything
    flat_index_mapping = {
        "mappings": {
            "properties": {
                "ipfs_hash": {"type": "keyword"},
                "file_type": {"type": "keyword"},
                "file_size": {"type": "integer"},
                "caption_model_vit_l_14_openai": {"type": "text"},
                "caption_model_vit_h_14_laion2b_s32b_b79k": {"type": "text"},
                "caption_model_vit_l_14_openai_f1": {"type": "text"},
                "caption_model_vit_h_14_laion2b_s32b_b79k_f1": {"type": "text"},
                "associated_collection": {"type": "keyword"}
            }
        }
    }
    
    test_connection()
    nft_index_name="nfts"
    # delete_index(nft_index_name)
    # create_index(nft_index_name, flat_index_mapping)
    # update_index_mappings(nft_index_name, flat_index_mapping)
    # delete_index(nft_index_name)
    sync_local_db_to_es(nft_index_name)
    # print(search_text(nft_index_name, "plant"))


