import requests
import json
import re
import time
import logging
from pymongo import MongoClient
from io import StringIO
import valve.source
from valve.source.a2s import ServerQuerier as server_querier, NoResponseError
import valve.source.master_server as master_server_querier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MongoDBConnection():
    ''' mongodb connection '''

    def __init__(self, host='127.0.0.1', port=27017):
        ''' initialize host and port '''
        self.host = host
        self.port = port
        self.connection = None

    def __enter__(self):
        ''' start connection '''
        self.connection = MongoClient(self.host, self.port)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        ''' close connection when finished '''
        self.connection.close()

class ArkCrawler():
    def __init__(self):
        self.master_host = 'hl2master.steampowered.com'
        self.master_timeout = 60
        self.server_timeout = 5
        self.ark_servers = {}

    def get_server_list(self):
        ''' get servers and returns a list '''
        URL = 'http://arkdedicated.com/officialservers.ini'
        server_list = requests.get(URL)

        return [server_list for server_list in re.findall(r"\d{1,3}(?:\.\d{1,3}){3}", StringIO(server_list.text).getvalue())]
    

    def steam_query(self, server_list):
        ''' iterates over list of servers and ports '''
        ports = [27015, 27017, 27019]
        mongo = MongoDBConnection()

        with mongo:
            ark_servers_db = mongo.connection.ark_server_db
            
            for address in server_list:
                for port in ports:
                    try:
                        server = (address, port)
                        output = server_querier(server, timeout=self.server_timeout)
                        info = output.info()
                        server = address + ":" + str(port)
                        self.ark_servers[server] = info.values
                        
                        active_servers = ark_servers_db['active_servers']
                        active_servers.insert_one(self.ark_servers[server])
                        
                    except NoResponseError:
                        continue
    
       
if __name__ == "__main__":
    ark_crawler = ArkCrawler()
    server_list = ark_crawler.get_server_list()
    ark_crawler.steam_query(server_list)
