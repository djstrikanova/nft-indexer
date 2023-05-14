
# NFT Content Indexer

[This is a project sponsored by a grant from Pomelo](https://pomelo.io/grants/nftindexer), an EOS blockchain crowdfunding site. The purpose of the NFT indexer is to provide code demonstrating the simplicitly of collecting NFT content and analyzing it using HuggingFace models and libraries. The Demo linked below, it uses SearchKit to display all the collected annotations of NFT image content.  

[Demo](https://djstrikanova.github.io/nft-indexer-searchkit/)

Demo Repos:

https://github.com/djstrikanova/nft-indexer-router

https://github.com/djstrikanova/nft-indexer-searchkit

# Windows Setup: 

## Install Anaconda
https://www.anaconda.com/

Set Windows Environment Path Variables
How the path looked for me:
C:\Users\djstrikanova\anaconda3\Scripts
C:\Users\djstrikanova\anaconda3\Library\bin

## Install PostGreSQL
https://www.postgresql.org/download/

I also use https://www.pgadmin.org/download/ to view the database

Create nft_indexer database

## Install Python Dependencies
conda install pip
pip install -r requirements.txt

Need Python 3.10.10 on Windows

## NVIDIA CUDA

May need to install CUDA https://developer.nvidia.com/cuda-toolkit-archive.
Go here https://pytorch.org/get-started/locally/ and install the correct version of pytorch for your system if GPU not working

https://github.com/pharmapsychotic/clip-interrogator

## Elasticsearch

Get Free ElasticSearch for testing at https://searchly.com/

The latest version of Elasticsearch Python may not work with Searchly, I failed with 8.70, but 7.10.1 worked. 

# Usage

## Scanning

Step 1: Collect NFT Data

nft_scanner.py is executed to collect NFT data from AtomicHub (For the AtomicHub standard in particular, I treat "assets" as "NFTs"). Scans can either be in "lookback" which starts from the latest and goes backwards, or "lookforward" which starts from the oldest and goes forwards. The immutable data along with other NFT metadata is stored in the "nfts" table.

Step 2: Download Images

nft_download.py is executed to download all unique NFT hashes found into the "downloads" directory. Currently, only files 25 Mb and under with file types of .png, .jpg, .jpeg, and .gif are downloaded. 

## Analysis

Step 3: Analyze Images

nft_huggingface_analyze.py is executed to generate annotations for each unqiue IPFS hash discovered which had it's image downloaded. All annotations are stored in the "hash_table" in pgsql with their respective IPFS hash.

## Storage

Locally, pgsql is used to store data. The models of these tables are provided in the "models" directory. Publicly, a Searchly Elasticsearch instance is fed information through the nft_elasticsearch.py script. This script exports all the annotations and IPFS hashes to Elasticsearch, allowing the Searchkit Demo to retrieve them. 

## TODO

- Automate scanning, downloading and analysis. In the current iteration, scanning/downloading/analysis is done manually by executing the script through command line. These scripts need to be upgraded such that a cronjob on a linux server can keep these scripts maintaining the most up to date NFT image annotations as they are generated. 

