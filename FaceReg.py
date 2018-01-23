import requests
import json
import random
import string
from bs4 import BeautifulSoup
import argparse
import time

req = requests.Session()

def usernameGenerate(x):
	username =''.join([random.choice(string.ascii_lowercase) for n in range(x)])
	return username

def phoneGenerate():
	phone = ''.join([random.choice(string.digits) for n in range(8)])
	phone = '132' + phone
	return phone

def verCode(email, headers):
    print("Sleep for 10S before request for verCode")
    time.sleep(10)
    verUrl = 'https://console.faceplusplus.com/api/account/verify_code_send?_ts1513153108179'
    verData = {"email": email}
    if (req.post(verUrl,data=json.dumps(verData),headers=headers).status_code == 200):
        print("Request for VerCode\n")

def regFace(username, phone):
    password = 'Mc12345678'
    email = username+'@cmail.club'
    regUrl = 'https://console.faceplusplus.com/api/account/register?_ts1513152187285'
    headers = {'Content-Type' : 'application/json'}
    regData = {"username":username,"email":email,"password":password,"prefix_phone_code":"+86","phone":phone}
    if (req.post(regUrl,data=json.dumps(regData),headers=headers).status_code == 200):
        print("Send Register Post\n")

    loginUrl = 'https://console.faceplusplus.com/api/account/login?_ts1513152756045'
    loginData = {"username_or_email":username,"password":password}
    if (req.post(loginUrl,data=json.dumps(loginData),headers=headers).status_code == 200):
        print("Send Login Post\n")

    code = None
    #print("Sleep for 10S before request for verCode")
    #time.sleep(10)
    #verUrl = 'https://console.faceplusplus.com/api/account/verify_code_send?_ts1513153108179'
    #verData = {"email": email}
    #if (req.post(verUrl,data=json.dumps(verData),headers=headers).status_code == 200):
    #    print("Request for VerCode\n")

    #print('Sleep for 10S\n')
    #time.sleep(10)
    #code = mailbox(username)
    #if	(code == None):
    #	exit()
    #while ( not code.isdigit() ):
    while ( code == None ):
        verCode(email, headers)
        print('Sleep for 10S before checking inbox\n')
        time.sleep(10)
        code = mailbox(username)
    veriUrl = 'https://console.faceplusplus.com/api/account/verify?_ts1513153204551'
    veriData = {"code":code,"kind":"1","name":username,"location_id":0,"email":email}

    if (req.post(veriUrl,data=json.dumps(veriData),headers=headers).status_code == 200):
        print("Verify Code\n")

    createAPI = 'https://console.faceplusplus.com/api/app/api_key?_ts1513153324875'
    createHeader = {"Referer":"https://console.faceplusplus.com/app/apikey/create", 'Content-Type' : 'application/json'}
    createData = {"name":username+"Face++","category_id":1101,"platform_ids":[3],"description":"","kind":2}

    if (req.post(createAPI,data=json.dumps(createData),headers=createHeader).status_code == 200):
        print("Creating API KEY\n")

    getAPI = 'https://console.faceplusplus.com/api/app/api_key?_ts1513153795639'
    APIHeader = {'Referer' : 'https://console.faceplusplus.com/app/apikey/list'}

    result = req.get(getAPI,headers=APIHeader).json()[0]

    api_key = result['api_key']
    secret = result['secret']

    return api_key,secret

def mailbox(username):
    address = username+"@cmail.club"
    emailUrl = 'https://app.getnada.com/api/v1/inboxes/' + address
    emailHeader = {'Referer' : 'https://app.getnada.com/inbox/'}

    # inbox = req.get(emailUrl,headers=emailHeader).json()
    mail = req.get(emailUrl,headers=emailHeader)

    if mail.status_code == 200:
        inbox = mail.json()
        while len(inbox) < 1:
            print("Message Not Received Yet\n")
            print('Sleep for 10S before request again')
            time.sleep(10)
            # mail = req.get(emailUrl,headers=emailHeader)
            inbox = req.get(emailUrl,headers=emailHeader).json()
        else:
            messageID = inbox[0]['uid']
            messageUrl = 'https://app.getnada.com/api/v1/messages/' + messageID
            messageHeader = {'Referer' : 'https://app.getnada.com/message/'+ messageID}
            message = req.get(messageUrl,headers=messageHeader).json()['html']
            soup = BeautifulSoup(message,'html.parser')
            l = soup.p.string.split(' ')
            t = []
            for i in l:
                t.append(i.split(','))
            return t[38][0][:-1]
    else:
        return None

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("--n",type=int, default=1, help="Number of account")
	args = parser.parse_args()
	file = open('FaceApi','a')
	try:
		for i in range(args.n):
			username = usernameGenerate(6)
			email = username+'@cmail.club'
			print(email)
			phone = phoneGenerate()
			api_key, secret = regFace(username,phone)
			userInfo = {"email":email,
						"key" : api_key,
						"secret": secret}

			file.write(json.dumps(userInfo))
			file.write("\n")
	except KeyboardInterrupt:
		file.flush()
		file.close()
	file.close()


if __name__ == '__main__':
    main()

