import requests
import json


url='http://100.80.0.131/ins'
switchuser='admin'
switchpassword='Password.1'

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
response = requests.post(url,data=json.dumps(payload), headers=myheaders,auth=(switchuser,switchpassword)).json()

with open("100.80.0.131.json","w") as f: 
  json.dump(response,f,indent=2)
