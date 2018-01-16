import requests
import json
import argparse
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
import threading


def readZip(zipPath):
	file = open(zipPath,"r")
	zipQueue = Queue()
	for i in file:
		zipQueue.put(i.split(",")[0][1:-1])
	return zipQueue

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
	for line in lines_set:
		out.write(line)
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
		# print(i, " ", dataJson)
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
	for i in result:
		file.write(json.dumps(i))
		file.write('\n')
	file.close()
	removeDup(filePath)
	lock.release()

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
	zipQueue = readZip(args.z)
	# while (not zipQueue.empty()):
	# # for i in range(zipQueue.qsize()):
	# 	t = threading.Thread(target=dataScrape, args=(zipQueue.get(),lock))
	# 	thread.append(t)

	les = (63,1,128,'other','other','white')
	gay = (63,2,2,'other','other','white')
	stw = (63,1,1,'other','other','white')
	stm = (63,2,1,'other,','other','white')
	# dataScrape(zipQueue.get(),lock,*stm)
	pool = ThreadPoolExecutor(max_workers=5)
	for i in range(1):
		while (not zipQueue.empty()):

			if args.o == 'gay':
				filePath = 'gay.json'
				pool.submit(dataScrape,zipQueue.get(), filePath, lock, *gay)
			elif args.o == 'les':
				filePath = 'les.json'
				pool.submit(dataScrape,zipQueue.get(), filePath, lock, *les)
			elif args.o	== 'stw':
				filePath = 'stw.json'
				pool.submit(dataScrape,zipQueue.get(), filePath, lock, *stw)
			elif args.o == 'stm':
				filePath = 'stm.json'
				pool.submit(dataScrape,zipQueue.get(), filePath, lock, *stm)
	# for i in thread:
	# 	i.start()
	# for i in thread:
	# 	i.join()

if __name__ == '__main__':
	main()

