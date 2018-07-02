import requests
import json
from elasticsearch import Elasticsearch
import datetime
import pytz
import logging
import re
import time



class model_93180:
	
    def __init__(self, host, port, switchip, username, password):
        self.database = "cisco_switch_data"
        self.table = "switch_counts"
        self.host = host
        self.port = port
        self.switchip=switchip
        self.username = username
        self.password = password
        self.es = Elasticsearch([{'host': self.host, 'port': self.port}])
    
    #index is created
    def create_index(self):
        logging.debug("Enter create_index")
        #
        if self.es.indices.exists(self.database):
            logging.info("Removing index {index} to recreate".format(index=self.database))
            self.es.indices.delete(index=self.database)
        self.es.indices.create(index=self.database)

    #API call show inteface
    def switch_interface(self):
    	
      url='http://{switch_ip}/ins'.format(switch_ip=self.switchip)	 
      switchuser=self.username
      switchpassword=self.password
      myheaders={'content-type':'application/json'}
      payload={
       "ins_api": {
        "version": "1.0",
        "type": "cli_show",
        "chunk": "0",
        "sid": "1",
        "input": "show interface",
        "output_format": "json"
        }
      }
      interface_info = requests.post(url,data=json.dumps(payload), headers=myheaders,auth=(switchuser,switchpassword)).json()
      return interface_info

    
    #API call show version
    def switch_version(self):
    
      
      url='http://{switch_ip}/ins'.format(switch_ip=self.switchip)	   
      switchuser=self.username
      switchpassword=self.password
      myheaders={'content-type':'application/json'}
      payload={
       "ins_api": {
       "version": "1.0",
       "type": "cli_show",
       "chunk": "0",
       "sid": "1",
       "input": "show version",
       "output_format": "json"
       }
      }
      version_info = requests.post(url,data=json.dumps(payload), headers=myheaders,auth=(switchuser,switchpassword)).json()
      return version_info

    def parse_version_data(self,version_info):

      
      collection_time = datetime.datetime.now(pytz.utc)
      data=version_info['ins_api']['outputs']['output']['body']
      Time=collection_time
      manufacturer=data['manufacturer']
      SwitchID=data['chassis_id']
      host_name=data['host_name']
   
         
      return manufacturer,SwitchID,host_name,Time            
        
    
    def parse_interface_data(self,interface_info):

      InCount=[]
      OutCount=[]
      eth_speed=[]
      PortNumber=[]
   
      pattern = re.compile( r'(\w*)\/(\d*)')
          
      
      for data in interface_info['ins_api']['outputs']['output']['body']['TABLE_interface']['ROW_interface']:
       if 'eth_inpkts' in data.keys():
        if data['eth_inpkts'] is not 0:
         matches= pattern.finditer(data['interface'])
         for match in matches:
           name=match.group(1)
           if "Ethernet1" in name:
             InCount.append(data['eth_inpkts'])
             OutCount.append(data['eth_outpkts'])
             eth_speed.append(data['eth_speed'])
             PortNumber.append(match.group(2))
                        


      return InCount,OutCount,eth_speed,PortNumber



   
    def store_data(self,InCount,OutCount,eth_speed,PortNumber,manufacturer,SwitchID,host_name,Time):

      cisco_data = {}
      cisco_data['manufacturer']=manufacturer
      cisco_data['SwitchID']=SwitchID
      cisco_data['host_name']=host_name

      cisco_data['Time'] = Time

      for i in range(len(InCount)):
  
        cisco_data['In-Count'] = InCount[i]
        cisco_data['Out-Count'] = OutCount[i]
        cisco_data['eth_speed'] = eth_speed[i]
        cisco_data['Port-Number'] = PortNumber[i] 
        self.es.index(index=self.database, doc_type=self.table, body=cisco_data)
  
    def print_data(self):

        result = self.es.search(index=self.database, body= {"from" : 0, "size" : 10000,"query" :{"match_all": {}}})

        data = result['hits']['hits']
        for item in data:
            original_data = item['_source']
            logging.debug("switch: \'{switch}\' port: {port} incount: {incount} outcount: {outcount} eth_speed: {eth_speed} time: {time} host_name: {host_name} manufacturer: {manufacturer}".
                          format(time=original_data['Time'],
                                 switch=original_data['SwitchID'],
                                 port=original_data['Port-Number'],
                                 incount=original_data['In-Count'],
                                 outcount=original_data['Out-Count'],
                                 eth_speed=original_data['eth_speed'],
                                 host_name=original_data['host_name'],
                                 manufacturer=original_data['manufacturer'],
                             
                  

                          ))  
       