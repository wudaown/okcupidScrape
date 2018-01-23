import argparse
import json
import os
import face_getter as fg
import requests
from concurrent.futures import ThreadPoolExecutor
#from queue import Queue
from Queue import Queue
import threading

from dropbox_api import Dropbox_API
#local_path = '/Users/i309943/Desktop/okcupid_temp'
ACCESS_TOKEN=''
local_path = '.'
remote_dir = '/okcupid_white'
dbx = Dropbox_API(ACCESS_TOKEN)
def thumbDownloader(info,current_ori, APIKEY, lock, remote, processed_file = set([]),get_face=False):
    try:
        # thumbsUrl = URLs of one user 's pics
        thumbsUrl = info['thumbs']
        username = info['username']
        userid = info['userid']
        orientation = info['orientation'].lower()
    except KeyError:
        print('Error: json info\n\t%s' % (info))
        return

    if orientation not in ['gay','les','straight']:
        return

    orientation = current_ori

    print('Processing user %s\t%s'%(userid,username))
    for j in range(len(thumbsUrl)):
        filename = orientation + "_" + userid + "_" + str(j + 1) + ".jpg"
        # determine whether a pic had been process eariler
        if filename in processed_file:
            continue

        try:
            data = requests.get(thumbsUrl[j])
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as e:
            print('Error in getting data from: %s'%thumbsUrl[j])
            with open("error_log.txt",'a') as f:
                f.write(thumbsUrl[j])
                f.write(":")
                f.write(str(e))
                f.write("\n")
            continue

        open(local_path + "/" + orientation + "/" + filename, 'wb').write(data.content)
        if get_face:
            if get_face_from_image(filename,local_path+"/"+current_ori, APIKEY, lock):
                upload_file_name = filename.split('.')[0]+'_face.jpg'
                os.remove(local_path + "/" + orientation + "/" + filename)
            else:
                os.remove(local_path + "/" + orientation + "/" + filename)
                print('Error: detect invalid faces.')
                continue

        else:
            upload_file_name = filename

        if remote:
            if dbx.upload_file(local_path + "/" + orientation + "/" + upload_file_name,
                               "%s/%s/%s" % (remote_dir, orientation, upload_file_name)):
                os.remove(local_path + "/" + orientation + "/" + upload_file_name)
                print('Success: upload file %s' % filename)



def get_face_from_image(filename,folder_path, APIKEY, lock):
    return fg.face_detector_caller(filename,folder_path, APIKEY, lock)

def get_processed_file_name(filepath):
    if os.path.exists(filepath):
        with open(filepath,'r') as f:
            lines = f.readlines()
            filenames = (l.split(',')[0] for l in lines)
            return set(filenames)
    else:
        print('Error: face_info file not exist: %s'%filepath)
        return set([])

def readJson(jsonPath):
    file = open(jsonPath,'r')
    jsonQueue = Queue()
    for i in file:
        try:
            jsonQueue.put(json.loads(i))
        except ValueError as e:
            print('Error in parsing json line: %s' % i )
            with open("error_log.txt", 'a') as f:
                f.write(i)
                f.write(":")
                f.write(str(e))
                f.write("\n")
                continue
    return jsonQueue

def readFaceAPI():
    file = open('FaceApi','r')
    apiList = []
    for i in file:
        apiList.append(json.loads(i)) 

    return apiList

def main():
    parser = argparse.ArgumentParser()
    json_file = '%s.json'
    parser.add_argument("f",type=str,help="Path to userinfo file")
    parser.add_argument("--r", type=bool, help="Upload to Dropbox, default True", default=True)
    args = parser.parse_args()
    current_orientation = args.f
    remote = args.r

    if not os.path.exists(local_path + '/' + current_orientation):
        os.mkdir(current_orientation)
    face_info_filepath = '%s/%s/faces_info.csv'%(local_path,current_orientation)
    processed_file = get_processed_file_name(face_info_filepath)

    if len(processed_file) == 0:
        print("Warning: no face_info file found. Will process all files in json.")
    else:
        print("%d files has been processed."%len(processed_file))

    # gay.json
    file = open(json_file%current_orientation,"r")

    jsonPath = (json_file%current_orientation)
    jsonQueue =  readJson(jsonPath)
    #while not jsonQueue.empty():
    #    print(jsonQueue.get())

    lock = threading.Lock()

    apiList = readFaceAPI()
    MAX = len(apiList)
    counter = 0
    pool = ThreadPoolExecutor(max_workers=MAX)
    for i in range(MAX/2):
        while (not jsonQueue.empty()):
            if counter == MAX:
                counter = 0
            else:
                pool.submit(thumbDownloader, jsonQueue.get(), current_orientation, apiList[counter], lock, remote, processed_file, get_face=True)
                counter += 1
    #for i in file:
    #    try:
    #        json_line = json.loads(i)
    #    except ValueError as e:
    #        print('Error in parsing json line: %s' % json_line)
    #        with open("error_log.txt", 'a') as f:
    #            f.write(json_line)
    #            f.write(":")
    #            f.write(str(e))
    #            f.write("\n")
    #            continue

    #    # json_line = a single line of json with one user info
    #    thumbDownloader(json_line,current_orientation,apiList[0], processed_file,get_face=True)


if __name__ == '__main__':
    main()
