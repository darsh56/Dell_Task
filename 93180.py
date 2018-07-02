import ciscodata
import logging
import argparse
from logging.handlers import RotatingFileHandler
import sys
import time

#####################################################
# main 
#####################################################
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
    logging.info("Starting cisco_switch_data")
    logging.info("log level: {}".format(logging.getLevelName(log_level)))
    #
   
    parser = argparse.ArgumentParser()
    parser.add_argument('--init', type=bool, help='reinitialize the data index', required=True)
    parser.add_argument('--ip', type=str, help='elasticsearch ip default: 100.80.97.105', required=True)
    parser.add_argument('--port', type=int, help='elasticsearch port default: 9200', required=True)
    parser.add_argument('--switchip', type=str, help='switch ip default: 100.80.0.130', required=True)    
    parser.add_argument('--username', help='switch username default: admin', required=True)
    parser.add_argument('--password', help='switch password default: Password.1', required=True)
    parser.add_argument('--loop', type=bool, help='run script continuously (every 5 seconds)', required=True)
    
    #########################################

    args, unknown = parser.parse_known_args()

    model_93180_obj = ciscodata.model_93180(args.ip, args.port, args.switchip, args.username, args.password)

    if args.init:
        model_93180_obj.create_index()

    if args.loop:
        while True:
          interface_info=model_93180_obj.switch_interface()
          version_info=model_93180_obj.switch_version()
          manufacturer,SwitchID,host_name,Time=model_93180_obj.parse_version_data(version_info)
          InCount,OutCount,eth_speed,PortNumber=model_93180_obj.parse_interface_data(interface_info)
          model_93180_obj.store_data(InCount,OutCount,eth_speed,PortNumber,manufacturer,SwitchID,host_name,Time)
          model_93180_obj.print_data()
          time.sleep(10)
   