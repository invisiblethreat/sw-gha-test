# filename => logs/app.log
# format => %(asctime)-15s %(message)s
# PLATFORM => windows
# config_file => config/simulate.json
# anomaly_flag_file => config/anomaly.json
# anomaly_value_file => config/normal_vs_anomalous_def.json

from organization import Organization
import util
import json
import random
import time
import logging
import signal
import sys
import asyncio  
import aiohttp
import os
from multiprocessing import Process
import threading
import functools

if os.path.isfile('logs/app.log'):
	os.remove('logs/app.log')
if not os.path.exists('logs'):
	os.mkdir('logs')

logging.basicConfig(filename='logs/app.log', level=logging.DEBUG, format='%(asctime)-15s %(message)s')
logging.getLogger("urllib3").setLevel(logging.WARNING)
log = logging.getLogger(__file__)

orgs_list = []
GROUP_SIZE = 1000
WORKERS = 100

def receiveSignal(signalNumber, frame):  
    print("\nX--------------ABORTING PROCESS--------------X\n")
    print(os.getpid())
    sys.exit(0)
    return

def get_json(json_file):
	json_obj = {}
	try:
		with open(json_file,'r') as f:
			json_obj = json.loads(f.read())
	except IOError:
		log.debug("Cannot open %s", json_file)
	return json_obj


def main(config_obj, anomaly_flags, anomaly_values):
	signal.signal(signal.SIGINT, receiveSignal)
	
	j = config_obj

	normal_time = []
	anomalous_time = []

	flag = 1
	for orgs in j:
		org_obj = Organization(orgs["ORG_INFO"]["EPOCH_ORGANIZATION_ID"],orgs["ORG_INFO"]["EPOCH_ORGANIZATION_NAME"],orgs["ORG_INFO"]["EPOCH_AOC_HOST"],orgs["ORG_INFO"]["EPOCH_AOC_PORT"], orgs["ORG_INFO"]["EPOCH_APPLICATION_KEY"])
		convert_to_absolute(orgs["CONFIG"])
		normal_time.append(orgs["CONFIG"]["NORMAL_VS_ANOMALOUS_MIN"][0]*60)
		anomalous_time.append(orgs["CONFIG"]["NORMAL_VS_ANOMALOUS_MIN"][1]*60)
			
		for hst in range(orgs["CONFIG"]["NO_OF_COLLECTORS"]):
			tags = {}
			for tag in orgs["CONFIG"]:
				if(tag == "NO_OF_COLLECTORS" or tag == "NORMAL_VS_ANOMALOUS_MIN"):
					continue
				ind = (random.randint(1,1001))%len(orgs["CONFIG"][tag])
				dict = orgs["CONFIG"][tag][ind]
				for t in dict:
					if(dict[t] == 1):
						orgs["CONFIG"][tag].remove(dict)
						tags[tag] = t
						break	
					else:
						dict[t] -= 1
						tags[tag] = t
			host_ips = ["127.0.0.1"]
			host_ips.append(str(tags['IP']))
			org_obj.create_collector(id=str(hst), ips=host_ips,myttl=tags['TTL'],tags=extracted_tags(tags), anomaly_flags=anomaly_flags, anomaly_values=anomaly_values, mode = tags['MODE'])
		log.debug("Organization %s populated with %d Collectors", org_obj.org_id, orgs["CONFIG"]["NO_OF_COLLECTORS"])
		orgs_list.append(org_obj)


	processes = []
	
	for i in range(len(orgs_list)) :
		
		# p = Process(target = keep_alive_callback_parallel, args = (orgs_list[i], normal_time[i],anomalous_time[i],))
		# p.start()
		# processes.append(p)

		tot_coll = len(orgs_list[i].collector_list)
		loops = tot_coll//GROUP_SIZE
		if tot_coll%GROUP_SIZE > 0:
			loops = loops + 1
		start = 0
		end = GROUP_SIZE - 1
		for j in range(loops) :
			if end > tot_coll - 1:
				end = tot_coll - 1
			p = Process(target = event_loop_starter, args = (orgs_list[i], normal_time[i],anomalous_time[i],start, end,))
			p.start()
			start = end + 1
			end = end + GROUP_SIZE
			if end > tot_coll - 1:
				end = tot_coll - 1
			processes.append(p)
	
	for p in processes:
		p.join()

def process_info(title):
    print(title)
    print('module name:', __name__)
    print('parent process:', os.getppid())
    print('process id:', os.getpid())


def extracted_tags(tags):
	new_tags = {'testing':True}
	if('PLATFORM' in tags):
		if(tags['PLATFORM'] == 'windows'):
			new_tags['epoch_platform'] = 'windows'
	return new_tags


def convert_to_absolute(dict={}):
	tot = dict["NO_OF_COLLECTORS"]
	for i in dict:
		if(i == "NO_OF_COLLECTORS" or i == "NORMAL_VS_ANOMALOUS_MIN"):
			continue
		for j in dict[i]:
			for k in j:
				j[k] = int((j[k]*tot)/100)
		sum = 0
		for j in dict[i]:
			for k in j:
				sum += j[k]
		if(sum < tot):
			for j in dict[i]:
				for k in j:
					j[k] += tot-sum
					sum = tot
					break
				break
		to_be_removed = []
		for j in dict[i]:
			for k in j:	
				if(j[k] == 0):
					to_be_removed.append(j)
					break
		for j in to_be_removed:
			dict[i].remove(j)

def on_task_done(semaphore, tasks, sent_metrics, error_calls, average_time, no_of_calls_per_min, start_time, metric, task):
	tasks.remove(task)
	res = False
	try:
		res = task.result()
	except Exception as e:
		log.debug("Exception noticed in callback when retrieving the result, type is: %s", e.__class__.__name__)
		print_exc()
	if(res == True):
		no_of_calls_per_min[metric] = no_of_calls_per_min[metric] + 1
		sent_metrics[metric] = sent_metrics[metric] + 1
		average_time[metric] += (int(time.time()) - start_time)
	else:
		error_calls[metric] = error_calls[metric] + 1
	semaphore.release()


def event_loop_starter(org, normal_time,anomalous_time, start, end):
	loop = asyncio.get_event_loop()  
	client = aiohttp.ClientSession(loop=loop)
	semaphore = asyncio.Semaphore(WORKERS)
	tasks = set()
	asyncio.ensure_future(keep_alive_callback_parallel(org, normal_time,anomalous_time, start, end, loop, client, semaphore, tasks), loop=loop)   
	loop.run_forever()


async def keep_alive_callback_parallel(org, normal_time,anomalous_time, start, end, loop, client, semaphore, tasks):
	process_info("function keep_alive_callback_parallel")
	total_time = normal_time+anomalous_time
	prev_time = 0
	metric_indicator = ['registered', 'info_sent', 'metadata_sent', 'metricdata_sent']

	sent_metrics = {}
	total_calls = {}
	error_calls = {}
	average_time = {}
	no_of_calls_per_min = {}
	for metric in metric_indicator:
		sent_metrics[metric] = 0
		error_calls[metric] = 0
		average_time[metric] = 0.0
		total_calls[metric] = 0
		no_of_calls_per_min[metric] = 0

	while(True):
		print("Sending data for " + org.org_name + " Collectors " + str(start) + " to " + str(end))
		
		log.debug("Process(%d) : Sending data for Org %s Collectors %d to %d", os.getpid(), org.org_name, start, end)
		log.debug("Process(%d) : Sending for %d Collectors", os.getpid(),end - start + 1)

		for loop_var in range(start, end + 1):
			collector = org.collector_list[loop_var]
			if(collector.is_active == True):
				# Registering Collector
				await semaphore.acquire()
				start_time = int(time.time())
				task = asyncio.ensure_future(collector.register_collector(org.AOC_IP, org.AOC_PORT, client),loop=loop)
				total_calls['registered'] += 1
				tasks.add(task)
				task.add_done_callback(functools.partial(on_task_done,semaphore,tasks,sent_metrics,error_calls,average_time, no_of_calls_per_min, start_time, 'registered'))

				# Sending Collector Info
				await semaphore.acquire()
				start_time = int(time.time())
				task = asyncio.ensure_future(collector.send_collector_info(org.AOC_IP, org.AOC_PORT, client),loop=loop)
				total_calls['info_sent'] += 1
				tasks.add(task)
				task.add_done_callback(functools.partial(on_task_done,semaphore,tasks,sent_metrics,error_calls,average_time, no_of_calls_per_min, start_time,'info_sent'))

				#Sending Metadata
				await semaphore.acquire()
				start_time = int(time.time())
				task = asyncio.ensure_future(collector.send_meta_data(org.AOC_IP, org.AOC_PORT, client),loop=loop)
				total_calls['metadata_sent'] += 1
				tasks.add(task)
				task.add_done_callback(functools.partial(on_task_done,semaphore,tasks,sent_metrics,error_calls,average_time, no_of_calls_per_min, start_time,'metadata_sent'))
				
				# Getting collector count from Druid
				curr_time = int(time.time())
				if (curr_time - prev_time) > 60 :
					log.debug("Process(%d) : Total Calls to AOC, Register count : %d \t Info count: %d \t MetricData count : %d \t Metadata count : %d", os.getpid(), total_calls['registered'], total_calls['info_sent'], total_calls['metricdata_sent'], total_calls['metadata_sent'])
					log.debug("Process(%d) : Calls with Status Code 200, Register count: %d \t Info count: %d \t MetricData count : %d \t Metadata count : %d", os.getpid(), sent_metrics['registered'], sent_metrics['info_sent'], sent_metrics['metricdata_sent'], sent_metrics['metadata_sent'])
					log.debug("Process(%d) : Calls with Errors, Register count: %d \t Info count: %d \t MetricData count : %d \t Metadata count : %d", os.getpid(), error_calls['registered'], error_calls['info_sent'], error_calls['metricdata_sent'], error_calls['metadata_sent'])
					asyncio.ensure_future(org.generate_collector_count(client),loop=loop)
					for metric in metric_indicator:
						if no_of_calls_per_min[metric] == 0:
							average_time[metric] = 0
						else :
							average_time[metric] = average_time[metric]/no_of_calls_per_min[metric]
					log.debug("Process(%d) : Average Time, Register : %f \t Info : %f \t MetricData : %f \t Metadata : %f", os.getpid(), average_time['registered'], average_time['info_sent'], average_time['metricdata_sent'], average_time['metadata_sent'])
					for metric in metric_indicator:
						no_of_calls_per_min[metric] = 0
						average_time[metric] = 0.0
					prev_time = curr_time

				# Sending Metricdata
				if(curr_time%total_time < normal_time):
					await semaphore.acquire()
					start_time = int(time.time())
					task = asyncio.ensure_future(collector.send_series_data(org.AOC_IP, org.AOC_PORT, client, False),loop=loop)
					total_calls['metricdata_sent'] += 1
					tasks.add(task)
					task.add_done_callback(functools.partial(on_task_done,semaphore,tasks,sent_metrics,error_calls,average_time, no_of_calls_per_min, start_time,'metricdata_sent'))
				else:
					await semaphore.acquire()
					start_time = int(time.time())
					task = asyncio.ensure_future(collector.send_series_data(org.AOC_IP, org.AOC_PORT, client, True),loop=loop)
					total_calls['metricdata_sent'] += 1
					tasks.add(task)
					task.add_done_callback(functools.partial(on_task_done,semaphore,tasks,sent_metrics,error_calls,average_time, no_of_calls_per_min, start_time,'metricdata_sent'))
			await asyncio.sleep(0.001)

		log.debug("Process(%d) : Sent data for Org %s Collectors %d to %d", os.getpid(), org.org_name, start, end)
		

if(__name__ == '__main__'):
	config_file = 'config/simulate.json'
	anomaly_flag_file = 'config/anomaly.json'
	anomaly_value_file = 'config/normal_vs_anomalous_def.json'
	
	config_obj = get_json(config_file)
	anomaly_flags = get_json(anomaly_flag_file)
	anomaly_values = get_json(anomaly_value_file)
	
	EPOCH_AOC_HOST = os.getenv('EPOCH_AOC_HOST')
	EPOCH_AOC_PORT = os.getenv('EPOCH_AOC_PORT')
	EPOCH_ORGANIZATION_NAME = os.getenv('EPOCH_ORGANIZATION_NAME')
	EPOCH_ORGANIZATION_ID = os.getenv('EPOCH_ORGANIZATION_ID')
	EPOCH_APPLICATION_KEY = os.getenv('EPOCH_APPLICATION_KEY')
	NO_OF_COLLECTORS = os.getenv('NO_OF_COLLECTORS')

	for org_obj in config_obj:
		if(EPOCH_AOC_HOST is not None):
			org_obj['ORG_INFO']['EPOCH_AOC_HOST'] = EPOCH_AOC_HOST
		if(EPOCH_AOC_PORT is not None):
			org_obj['ORG_INFO']['EPOCH_AOC_PORT'] = int(EPOCH_AOC_PORT)
		if(EPOCH_ORGANIZATION_NAME is not None):
			org_obj['ORG_INFO']['EPOCH_ORGANIZATION_NAME'] = EPOCH_ORGANIZATION_NAME
		if(EPOCH_ORGANIZATION_ID is not None):
			org_obj['ORG_INFO']['EPOCH_ORGANIZATION_ID'] = EPOCH_ORGANIZATION_ID
		if(EPOCH_APPLICATION_KEY is not None):
			org_obj['ORG_INFO']['EPOCH_APPLICATION_KEY'] = EPOCH_APPLICATION_KEY
		if(NO_OF_COLLECTORS is not None):
			org_obj['CONFIG']['NO_OF_COLLECTORS'] = int(NO_OF_COLLECTORS)

	main(config_obj, anomaly_flags, anomaly_values)