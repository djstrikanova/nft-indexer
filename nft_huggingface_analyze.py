from PIL import Image
from clip_interrogator import Config, Interrogator
import time
from pprint import pprint
from models.ipfs_hashes import HashTable
from config.database import db_session, init_db
from nft_elasticsearch import index_content_hashes
import torch
import sys

cur_index = "nfts"

model_1 = "ViT-L-14/openai"
model_2 = "ViT-H-14/laion2b_s32b_b79k"
cur_model = model_2


# Open Interrogator Connection
# May need to install CUDA https://developer.nvidia.com/cuda-toolkit-archive
# Go here https://pytorch.org/get-started/locally/ and install the correct version of pytorch for your system if GPU not working
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
if not torch.cuda.is_available():
    print("CUDA is not available, using CPU. Warning: this will be very slow!")
    sys.exit()

ci = Interrogator(Config(device=device,clip_model_name=cur_model))

# Just Wait for New Jobs from DB
while True:
    #Get Batch From DB that have a filepath, no content description, and file types .png and .jpg only
    init_db()
    ipfs_hashes = db_session.query(HashTable).filter(HashTable.file_path != None).filter(HashTable.file_type.in_([".png", ".jpg",".jpeg"])).all()

    #Process Each Hash
    for ipfs_hash in ipfs_hashes:
        meta = ipfs_hash.content_description

        #Check if model already exists in meta, skip if it does
        if meta is not None:
            if(cur_model in meta["models"]):
                print(f"Model {cur_model} already in meta, skipping")
                continue

        
        print(f"Processing Hash: {ipfs_hash.ipfs_hash} located at {ipfs_hash.file_path}")
        #Open Image
        try:
            image = Image.open(ipfs_hash.file_path).convert('RGB')
            #Interrogate Image
            result = ci.interrogate(image)
            # No Content Description, Create New
            if meta is None:
                meta = {"models":{cur_model: result}}
            else:
                # Content Description Exists, Add to Existing
                if(cur_model not in meta["models"]):
                    meta["models"][cur_model] = result
                else:
                    print(f"Model {cur_model} already in meta")
                
            print(f"Completed Hash: {ipfs_hash.ipfs_hash} with result: {result}")
            print(f"https://atomichub-ipfs.com/ipfs/{ipfs_hash.ipfs_hash}")
            #Update DB
            db_session.query(HashTable).filter_by(ipfs_hash=ipfs_hash.ipfs_hash).update({"content_description": meta}) 
            db_session.commit()
            # Index to Elasticsearch
            index_content_hashes(cur_index, [ipfs_hash])


        #Update DB with result
        except Exception as e:
            print(f"Error opening image: {e}")
            continue



    #Sleep for 1 seconds
    sleeptime = 0.1
    print(f"Completed Batch, Sleeping for {sleeptime} seconds")
    time.sleep(sleeptime)

