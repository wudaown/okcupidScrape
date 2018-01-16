import argparse
import json
import os
import face_getter as fg
import requests

from dropbox_api import Dropbox_API
local_path = '/Users/i309943/Desktop/okcupid_temp'
ACCESS_TOKEN = 'iPCS8mNt4hAAAAAAAAJjUfXjqNo6IKI6gJidkich6TmuqJEXu4GpJk5ZQdWi8WTF'
remote_dir = '/okcupid_white'
dbx = Dropbox_API(ACCESS_TOKEN)
def thumbDownloader(info,current_ori,processed_file = set([]),get_face=False):
    try:
        thumbsUrl = info['thumbs']
        username = info['username']
        userid = info['userid']
        orientation = info['orientation'].lower()
    except KeyError:
        print('Error: json info\n\t%s' % (info))
        return

<<<<<<< HEAD
def thumbDownloader(info,filePath):
#    filePath = "okcupid.json"
#    
#    file = open(filePath,"r")
    
    orientation =  filePath.split(".")[0]
    thumbsUrl = info['thumbs']
    username = info['username']
    #orientation = info['orientation']
    for j in range(len(thumbsUrl)):
        data = requests.get(thumbsUrl[j])
        open(orientation+"_"+username+"_"+str(j+1)+".jpg",'wb').write(data.content)
=======
    if orientation not in ['gay','les','straight']:
        return

    orientation = current_ori

    print('Processing user %s\t%s'%(userid,username))
    for j in range(len(thumbsUrl)):
        filename = orientation + "_" + userid + "_" + str(j + 1) + ".jpg"
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
            if get_face_from_image(filename,local_path+"/"+current_ori):
                upload_file_name = filename.split('.')[0]+'_face.jpg'
                os.remove(local_path + "/" + orientation + "/" + filename)
            else:
                os.remove(local_path + "/" + orientation + "/" + filename)
                print('Error: detect invalid faces.')
                continue

        else:
            upload_file_name = filename
>>>>>>> upstream/master

        if dbx.upload_file(local_path + "/" + orientation + "/" + upload_file_name,
                           "%s/%s/%s" % (remote_dir, orientation, upload_file_name)):
            os.remove(local_path + "/" + orientation + "/" + upload_file_name)
            print('Success: upload file %s' % filename)



def get_face_from_image(filename,folder_path):
    return fg.face_detector_caller(filename,folder_path)

def get_processed_file_name(filepath):
    if os.path.exists(filepath):
        with open(filepath,'r') as f:
            lines = f.readlines()
            filenames = (l.split(',')[0] for l in lines)
            return set(filenames)
    else:
        print('Error: face_info file not exist: %s'%filepath)
        return set([])

def main():
    parser = argparse.ArgumentParser()
    json_file = '%s.json'
    parser.add_argument("f",type=str,help="Path to userinfo file")
    args = parser.parse_args()
    current_orientation = args.f

    face_info_filepath = '%s/%s/faces_info.csv'%(local_path,current_orientation)
    processed_file = get_processed_file_name(face_info_filepath)

    if len(processed_file) == 0:
        print("Warning: no face_info file found. Will process all files in json.")
    else:
        print("%d files has been processed."%len(processed_file))

    file = open(json_file%current_orientation,"r")

    for i in file:
        try:
            json_line = json.loads(i)
        except ValueError as e:
            print('Error in parsing json line: %s' % json_line)
            with open("error_log.txt", 'a') as f:
                f.write(json_line)
                f.write(":")
                f.write(str(e))
                f.write("\n")
                continue

        thumbDownloader(json_line,current_orientation,processed_file,get_face=True)


<<<<<<< HEAD
    pool = ThreadPoolExecutor(max_workers=10)
    
    for i in range(5):
        while (not thumbQueue.empty()):
            pool.submit(thumbDownloader,thumbQueue.get(),args.f)
=======
>>>>>>> upstream/master

main()
