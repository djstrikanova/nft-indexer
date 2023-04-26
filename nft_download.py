import requests
import os
import mimetypes
from pprint import pprint
import time

from concurrent.futures import ThreadPoolExecutor
import signal
import sys 

from models.ipfs_hashes import HashTable
from config.database import db_session, init_db
valid_file_extensions = [".png", ".jpg", ".jpeg",".gif"]
max_size_bytes_mb = 25
timeout_cap = 3

def download_ipfs_content(cid, local_directory):
    cloudflare_gateway = "https://atomichub-ipfs.com/ipfs/"
    timeout_seconds = 30
    max_size_bytes = max_size_bytes_mb * 1000000
    # Clear Whitespace Because Some people accidently add a space to their hash in the NFT
    original_cid = cid
    cid=cid.strip()
    do_not_download = False
    # Construct the URL
    url = f"{cloudflare_gateway}{cid}"

    try:
        # Get file size from the 'Content-Length' header
        head_response = requests.head(url, timeout=timeout_seconds)
        file_size_bytes = int(head_response.headers.get("Content-Length", "0"))
        print("{:.2f}Mb File Found".format(file_size_bytes/1000000)) 
        

        # Get the content type and find the corresponding file extension
        content_type = head_response.headers.get("Content-Type")
        file_extension = mimetypes.guess_extension(content_type)

        # Check if Hash exists in DB 
        ipfs_hash_exists = db_session.query(HashTable).filter_by(ipfs_hash=original_cid).first()
        if(ipfs_hash_exists is not None):
            ipfs_hash_exists.file_type = file_extension
            ipfs_hash_exists.file_size = file_size_bytes

        

        if max_size_bytes is not None and file_size_bytes > max_size_bytes:
            raise Exception(f"File size {file_size_bytes} bytes exceeds the maximum allowed size of {max_size_bytes} bytes")
        if file_extension not in valid_file_extensions:
            raise Exception(f"File extension {file_extension} is not in the list of valid file extensions: {valid_file_extensions}")



        # Download the content
        response = requests.get(url, timeout=timeout_seconds)
        response.raise_for_status()

        # Check if the request was successful
        if response.status_code == 200:
            # Check if the directory exists, if not, create it
            if not os.path.exists(local_directory):
                os.makedirs(local_directory)
            


            # Append the file extension to the filename, if found
            file_name = f"{cid}"
            if file_extension not in file_name:
                if file_extension:
                    file_name += f"{file_extension}"
            # Flatten the file name, no need for subdirectories. Replace "/" with "_" to avoid issues
            file_name = file_name.replace("/", "_")

            # Concatenate the file path and file name and create the file
            file_path = os.path.join(local_directory, file_name)
            with open(file_path, "wb") as f:
                f.write(response.content)


            #Check If IPFS Hash is in DB
            if(ipfs_hash_exists is not None):
                ipfs_hash_exists.file_path = file_path

            db_session.commit()


            return file_path
        else:
            raise Exception(f"Error downloading content: {response.status_code}")
    except Exception as e:
        ipfs_hash_exists = db_session.query(HashTable).filter_by(ipfs_hash=original_cid).first()
        if(ipfs_hash_exists is not None):
            ipfs_hash_exists.timeouts += 1
            db_session.commit()
        print(f"Error: {e}")

def download_multiple_hashes(ipfs_hashes, local_directory, max_workers=5):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:

        # Catch KeyboardInterrupt exception and shutdown threads gracefully
        def signal_handler(sig, frame):
            print('You pressed Ctrl+C!')
            executor.shutdown(wait=True)
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        futures = [executor.submit(download_ipfs_content, ipfs_hash, local_directory) for ipfs_hash in ipfs_hashes]
        return [future.result() for future in futures]

# Download Hashes From DB that have no filepath and no Content Description, and timeout is less than 5
def get_hashes_from_db(amount=100):
    # init_db()
    ipfs_hashes = db_session.query(HashTable).filter(HashTable.file_path == None).filter(HashTable.timeouts < timeout_cap).limit(amount).all()
    
    if not ipfs_hashes:
        print("No Hashes Found")
        return []


    return [ipfs_hash.ipfs_hash for ipfs_hash in ipfs_hashes]

# Download Loop

def loop_download(amount):
    while True:
        local_directory = "downloads"
        hashes = get_hashes_from_db(amount)
        file_paths = download_multiple_hashes(hashes, local_directory)
        print(f"Files downloaded to: {file_paths}")
        #Sleep for 10 seconds
        sleeptime = 5
        print(f"Completed Batch, Sleeping for {sleeptime} seconds")
        time.sleep(sleeptime)


loop_download(5)

