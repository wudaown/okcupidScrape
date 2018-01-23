import requests
import json
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
# from concurrent.futures import as_completed
# from ThreadPoolExecutor import ThreadPoolExecutorWithQueueSizeLimit
from queue import Queue
import threading
import concurrent.futures.thread


def readZip(zipPath):
	file = open(zipPath,"r")
	zipQueue = Queue()
	for i in file:
		zipQueue.put(i.split(",")[0][1:-1])
	file.close()
	return zipQueue

# def readZipList(zipPath):
# 	file = open(zipPath,'r')
# 	zipList = []
# 	for i in file:
# 		zipList.append(i.split(",")[0][1:-1])
# 	file.close
# 	return zipList

def readZipList(zipPath):
	file = open(zipPath,'r')
	zipList = []
	for i in file:
		zipList.append(i)
	file.close()
	return zipList

def remainderZip(zipPath, qsize):
	zipList = readZipList(zipPath)
	file = open(zipPath,'w')
	for i in range(qsize):
		# print(i)
		file.write(zipList[i])
		# file.write("\n")
	file.close()




def locationQuery(zipCode):
	locationUrl = 'https://www.okcupid.com/1/apitun/location/query?q='
	result = requests.get(locationUrl+str(zipCode)).json()['results'][0]
	return result


def	newPayload(page,location,*p):
	payload = {"order_by":"SPECIAL_BLEND",
			   "gentation":[p[0]],
			   "gender_tags":p[1],
			   "orientation_tags":p[2],
			   "minimum_age":18,
			   "maximum_age":49,
			   "locid":2605031457,
			   "radius":25,"lquery":"",
			   "location":location,
			   "located_anywhere":0,
			   "last_login":31536000,
			   "i_want":p[3],"they_want":p[4],
			   "languages":0,
			   "ethnicity":[p[5]],
			   "religion":[],
			   "availability":"any",
			   "monogamy":"unknown",
			   "looking_for":[],
			   "smoking":[],
			   "drinking":[],
			   "drugs":[],
			   "answers":[],
			   "interest_ids":[],
			   "education":[],
			   "children":[],
			   "cats":[],
			   "dogs":[],
			   "tagOrder":[],
			   "after":page,
			   "save_search":"true",
			   "limit":18,
			   "fields":"userinfo,thumbs"}
	return payload

def removeDup(filePath):
	lines = open(filePath, 'r').readlines()
	lines_set = set(lines)
	out = open(filePath, 'w')
	# fileLength = len(lines_set)
	j = 0
	for line in lines_set:
		out.write(line)
		# j += 1
		# while j <= fileLength // 8:
		# 	out.flush()
		# 	j = 0
	out.close()


def dataScrape(zipCode, filePath, lock,*p):
	result = []
	r = requests.Session()
	url = 'https://www.okcupid.com/match'
	searchUrl = 'https://www.okcupid.com/1/apitun/match/search'
	headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
	location = locationQuery(zipCode)
	print(location)
	r.get(url)
	for i in range(56):
		if i == 0:
			page = None
		else:
			page = dataJson.json()['paging']['cursors']['after']
		payload = newPayload(page,location,*p)
		dataJson = r.post(searchUrl, data=json.dumps(payload),headers=headers)
		print(i, " ", dataJson)
		if dataJson.status_code == 200:
			userData = dataJson.json()['data']
			for usr in userData:
				orientation = usr['userinfo']['orientation']
				age = usr['userinfo']['age']
				userid = usr['userid']
				username = usr['username']
				gender = usr['userinfo']['gender_letter']
				thumbsNail = usr['thumbs']
				# thumbs = i['thumbs'][0]['800x800']
				thumbs = []
				for thb in thumbsNail:
					thumbs.append(thb['800x800'])
				userInfo = {
					"userid" : userid,
					"username" : username,
					"gender": gender,
					"age" : age,
					"orientation" : orientation,
					"thumbs" : thumbs
				}
				result.append(userInfo)
				# file.write(json.dumps(userInfo))
				# file.write("\n")
	lock.acquire()
	file = open(filePath,"a")
	# fileLength = len(result)
	j = 0
	for i in result:
		file.write(json.dumps(i))
		file.write('\n')
		file.flush()
		# j += 1
		# while j <= fileLength//8:
		# 	file.flush()
		# 	j = 0
	file.close()
	lock.release()

	print("Done " + str(zipCode))


def main():
	parser = argparse.ArgumentParser()
	# parser.add_argument('--zipcode', type=str, default=0, help="enter a zipcode for USA")
	# parser.add_argument("--z", help="ZIPCODE USA")
	# parser.add_argument("--t", type=int, default=1, help="Loop runtime default 1")
	parser.add_argument("z",type=str,help="Path to zipcode file")
	parser.add_argument("o", type=str, help="Looking for orientation", choices=['gay', 'les', 'stm','stw'])
	args = parser.parse_args()
	# if	args.z == None:
	# 	print("Enter a ZIPCODE")
	# else:
	# 	for i in range(args.t):
	# 		dataScrape(args.z)

	lock = threading.Lock()

	thread = []
	#zipQueue = readZip(args.z)
	# while (not zipQueue.empty()):
	# # for i in range(zipQueue.qsize()):
	# 	t = threading.Thread(target=dataScrape, args=(zipQueue.get(),lock))
	# 	thread.append(t)

	zipList = readZipList(args.z)

	les = (63,1,128,'other','other','white')
	gay = (63,2,2,'other','other','white')
	stw = (63,1,1,'other','other','white')
	stm = (63,2,1,'other,','other','white')
	threadpool = []
	pool = ThreadPoolExecutor(max_workers=2)
	#pool = ThreadPoolExecutorWithQueueSizeLimit(max_workers=2, maxsize=2)

	for i in range(1):
		while len(zipList) != 0:
			if args.o == 'gay':
				filePath = 'gay.json'
				threadpool.append(pool.submit(dataScrape,zipList.pop().strip('\n'), filePath, lock, *gay))
			elif args.o == 'les':
				filePath = 'les.json'
				threadpool.append(pool.submit(dataScrape,zipList.pop().strip('\n'), filePath, lock, *les))
			elif args.o	== 'stw':
				filePath = 'stw.json'
				threadpool.append(pool.submit(dataScrape,zipList.pop().strip('\n'), filePath, lock, *stw))
			elif args.o == 'stm':
				filePath = 'stm.json'
				threadpool.append(pool.submit(dataScrape,zipList.pop().strip('\n'), filePath, lock, *stm))

	try:
		for fp in as_completed(threadpool):
			fp.result()
	except KeyboardInterrupt:
		qsize = pool._work_queue.qsize()
		print(qsize)
		remainderZip(args.z, qsize)
		pool._threads.clear()
		concurrent.futures.thread._threads_queues.clear()

	removeDup(filePath)



	# while (not zipQueue.empty()):
	# 	if args.o == 'gay':
	# 		filePath = 'gay.json'
	# 		threadpool.append(pool.submit(dataScrape,zipQueue.get(), filePath, lock, *gay))
	# 	elif args.o == 'les':
	# 		filePath = 'les.json'
	# 		threadpool.append(pool.submit(dataScrape,zipQueue.get(), filePath, lock, *les))
	# 	elif args.o	== 'stw':
	# 		filePath = 'stw.json'
	# 		threadpool.append(pool.submit(dataScrape,zipQueue.get(), filePath, lock, *stw))
	# 	elif args.o == 'stm':
	# 		filePath = 'stm.json'
	# 		threadpool.append(pool.submit(dataScrape,zipQueue.get(), filePath, lock, *stm))
	#
	# try:
	# 	for fp in as_completed(threadpool):
	# 		fp.result()
	# except KeyboardInterrupt:
	# 	print("KKKK")
	# 	while not zipQueue.empty():
	# 		print(zipQueue.get())
	# 	pool._threads.clear()
	# 	concurrent.futures.threadpoolad._threads_queues.clear()
	# for i in thread:
	# 	i.start()
	# for i in thread:
	# 	i.join()

if __name__ == '__main__':
	main()

