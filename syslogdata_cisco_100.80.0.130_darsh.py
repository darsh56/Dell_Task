
import sys
import time
import requests
import json
import elasticsearch
from elasticsearch import Elasticsearch
import datetime

import logging
from logging.handlers import RotatingFileHandler
import argparse

from termcolor import cprint
# terminal text colors
print_error = lambda text: cprint(text, 'white', 'on_red')
print_warning = lambda text: cprint(text, 'yellow')
print_info = lambda text: cprint(text, 'green')


class Switch_data:
	#database connection
    def __init__(self, host, port=9200):
        self.database = "cisco_syslogdata_100.80.0.130"
        self.table = "switch_counts"
        self.host = host
        self.port = port
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
    def api(self):
    	 
        url='http://100.80.0.130/ins'
        switchuser='admin'
        switchpassword='Password.1'

        myheaders={'content-type':'application/json'}
        payload={
         "ins_api": {
           "version": "1.0",
           "type": "cli_conf",
           "chunk": "0",
           "sid": "1",
           "input": "show logging",
           "output_format": "json"
         }
        }
        response = requests.post(url,data=json.dumps(payload), headers=myheaders,auth=(switchuser,switchpassword)).json()
        return response

    

        
    #get data from switch and send data to database
    def generate_data(self,response):


      import datetime
      import pytz
      collection_time = datetime.datetime.now(pytz.utc)
      cisco_data = {}
      data=response['ins_api']['outputs']['output']['body']
      b=[]
      c=[]
      cisco_data = {}
      text = data.split(' ')
      count=1
#print (text)

      a = text.index('1(alerts)')


      for item in text[a:]:
        b.append(item)
#print (b)
      str1 = ' '.join(b)

#print (str1)

      text = str1.split('\n')
#print(text)

      bi = text.index('')
#print (bi)

      for item in text[bi:]:
        c.append(item)
      
#print (c)

      for item in c:
        cisco_data['date']= item[0:11]
        cisco_data['m_time']= item[12:20] #log generated time
        cisco_data['time']= collection_time
        cisco_data['name']= item[21:33]
        cisco_data['message']= item[34:]
        cisco_data['message_count']= count
        count = count + 1
        self.es.index(index=self.database, doc_type=self.table, body=cisco_data)
  
      
         


    # print data into logfiles
    def print_data(self):
        #print in log files
        result = self.es.search(index=self.database, doc_type=self.table)
        data = result['hits']['hits']
        for item in data:
            original_data = item['_source']
            app_log.debug("date: \'{date}\' time: {time}  m_time: {m_time} name: {name} message: {message} message_count: {message_count}".
                          format(date=original_data['date'],
                                 time=original_data['time'],
                                 m_time=original_data['m_time'],
                                 name=original_data['name'],
                                 message=original_data['message'],
                                 message_count=original_data['message_count'],
                          ))

#####################################################
# main 
#####################################################f
if __name__ == "__main__":
    my_handler = RotatingFileHandler(filename='./cisco_data.log',
                                     mode='a',
                                     maxBytes=1*1024*1024,  # 1 MB
                                     backupCount=10,
                                     encoding=None,
                                     delay=0)

    log_level = logging.DEBUG
    app_log = logging.getLogger()
    my_handler.setLevel(log_level)
    formatter = logging.Formatter('%(asctime)s %(levelname)s,%(message)s',
                                              datefmt='%b %d,%Y %H:%M:%S')
    my_handler.setFormatter(formatter)
    app_log.setLevel(log_level)
    app_log.addHandler(my_handler)
    #
    std_out = logging.StreamHandler(sys.stdout)
    std_out.setLevel(log_level)
    std_out.setFormatter(formatter)
    app_log.addHandler(std_out)
    #
    logging.info("Starting cisco_data")
    logging.info("log level: {}".format(logging.getLevelName(log_level)))
    #
    parser = argparse.ArgumentParser()
    parser.add_argument('--init', type=bool, help='reinitialize the data index',
                        default=False)
    parser.add_argument('--ip', type=str, help='elasticsearch ip default: 100.80.97.105',
                        default='100.80.97.105')
    parser.add_argument('--port', type=int, help='elasticsearch port default: 9200',
                        default=9200)
    parser.add_argument('--loop', type=bool, help='run script continuously (every 5 seconds)',
                        default=False)
    #########################################

    args, unknown = parser.parse_known_args()

    init = args.init
    #
    generator = Switch_data(args.ip, args.port)
    if args.init:
        generator.create_index()
    # added for testing
    if args.loop:
        while True:
          response=generator.api()

          generator.generate_data(response)
          time.sleep(5)
  
