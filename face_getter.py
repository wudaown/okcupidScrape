import math
import os
import time

import cv2
import numpy as np
import urllib2
from PIL import Image


# python 2

def detect_face_via_facepp(userinfo, file):
    http_url = 'https://api-us.faceplusplus.com/facepp/v3/detect'
    key = userinfo['key']
    secret = userinfo['secret']
    boundary = '----------%s' % hex(int(time.time() * 1000))
    data = []
    data.append('--%s' % boundary)
    data.append('Content-Disposition: form-data; name="%s"\r\n' % 'api_key')
    data.append(key)
    data.append('--%s' % boundary)
    data.append('Content-Disposition: form-data; name="%s"\r\n' % 'api_secret')
    data.append(secret)
    data.append('--%s' % boundary)
    fr = open(file, 'rb')
    data.append('Content-Disposition: form-data; name="%s"; filename="testing.jpg"' % 'image_file')
    data.append('Content-Type: %s\r\n' % 'application/octet-stream')
    data.append(fr.read())
    fr.close()
    data.append('--%s' % boundary)

    data.append('Content-Disposition: form-data; name="%s"\r\n' % 'return_landmark')
    data.append('1')
    data.append('--%s' % boundary)

    data.append('Content-Disposition: form-data; name="%s"\r\n' % 'return_attributes')
    data.append(
        "gender,age,smiling,headpose,facequality,blur,eyestatus,emotion,ethnicity,beauty,mouthstatus,eyegaze,skinstatus")
    data.append('--%s--\r\n' % boundary)

    http_body = '\r\n'.join(data)

    # build http request
    req = urllib2.Request(http_url)
    req.add_header('Content-Type', 'multipart/form-data; boundary=%s' % boundary)
    req.add_data(http_body)

    qrcont = None

    try:
        resp = urllib2.urlopen(req, timeout=20)
        qrcont = resp.read()
    except urllib2.HTTPError as e:
        print(e.read())
    except KeyboardInterrupt:
        raise
    except:
        print('ERROR OCCURED!')

    if qrcont:
        mydict = eval(qrcont)
        faces = mydict["faces"]
        faceNum = len(faces)
        print(" - Recognized %d faces" % (faceNum))
        if faceNum == 1:
            return qrcont
        else:
            # fail if detect more than one face
            return None
    else:
        print(" - Error in detecting faces.")
        return None


def update_dict_for_landmarks(img_dict, landmarks):
    # https://console.faceplusplus.com/documents/6329308
    def distance_between_points(p1, p2):
        return math.sqrt(math.pow(p1[0] - p2[0], 2) + math.pow(p1[1] - p2[1], 2))

    def get_eye_distance(landmarks):
        if "left_eye_center" not in landmarks.keys():
            return None
        if "right_eye_center" not in landmarks.keys():
            return None

        left_eye_center = (landmarks["left_eye_center"]["x"], landmarks["left_eye_center"]["y"])
        right_eye_center = (landmarks["right_eye_center"]["x"], landmarks["right_eye_center"]["y"])
        return distance_between_points(left_eye_center, right_eye_center)

    def get_left_right_face_ratio(landmarks):
        for item in ["nose_tip", "contour_left4", "contour_right4"]:
            if item not in landmarks.keys():
                return None

        nose_tip = (landmarks["nose_tip"]["x"], landmarks["nose_tip"]["y"])
        left_face = (landmarks["contour_left4"]["x"], landmarks["contour_left4"]["y"])
        right_face = (landmarks["contour_right4"]["x"], landmarks["contour_right4"]["y"])
        return distance_between_points(left_face, nose_tip) / distance_between_points(right_face, nose_tip)

    img_dict['left_right_face_ratio'] = get_left_right_face_ratio(landmarks)
    img_dict['eye_dist'] = get_eye_distance(landmarks)

    return img_dict


def update_dict_for_attributes(img_dict, attributes):
    def get_glass_status(attributes, threshold=80):
        if "eyestatus" in attributes.keys():
            if attributes["eyestatus"]["left_eye_status"]["normal_glass_eye_open"] + \
                    attributes["eyestatus"]["left_eye_status"]["normal_glass_eye_close"] > threshold and \
                                    attributes["eyestatus"]["right_eye_status"]["normal_glass_eye_open"] + \
                                    attributes["eyestatus"]["right_eye_status"]["normal_glass_eye_close"] > threshold:
                return "normal"
            elif attributes["eyestatus"]["left_eye_status"]["no_glass_eye_open"] + \
                    attributes["eyestatus"]["left_eye_status"]["no_glass_eye_close"] > threshold and \
                                    attributes["eyestatus"]["right_eye_status"]["no_glass_eye_open"] + \
                                    attributes["eyestatus"]["right_eye_status"]["no_glass_eye_close"] > threshold:
                return "no"
            elif attributes["eyestatus"]["left_eye_status"]["dark_glasses"] > threshold and \
                            attributes["eyestatus"]["right_eye_status"]["dark_glasses"] > threshold:
                return "dark"
            else:
                return "uncertain"
        else:
            return "invalid"

    def get_eye_openness_status(attributes, threshold=80):
        if "eyestatus" in attributes.keys():
            if attributes["eyestatus"]["left_eye_status"]["normal_glass_eye_open"] + \
                    attributes["eyestatus"]["left_eye_status"]["no_glass_eye_open"] > threshold and \
                                    attributes["eyestatus"]["right_eye_status"]["normal_glass_eye_open"] + \
                                    attributes["eyestatus"]["right_eye_status"]["no_glass_eye_open"] > threshold:
                return "both_open"
            elif attributes["eyestatus"]["left_eye_status"]["dark_glasses"] > threshold and \
                            attributes["eyestatus"]["right_eye_status"]["dark_glasses"] > threshold:
                return "no_eyes"
            else:
                return "uncertain"
        else:
            return "invalid"

    def get_mouth_status(attributes, threshold=80):
        if "mouthstatus" in attributes.keys():
            if attributes["mouthstatus"]["close"] > threshold:
                return "close"
            elif attributes["mouthstatus"]["open"] > threshold:
                return "open"
            elif attributes["mouthstatus"]["surgical_mask_or_respirator"] + attributes["mouthstatus"][
                "other_occlusion"] > threshold:
                return "blocked"
            else:
                return "uncertain"
        else:
            return "invalid"

    img_dict["glass_on_eye"] = get_glass_status(attributes)
    img_dict["mouth"] = get_mouth_status(attributes)
    img_dict["glass"] = attributes["glass"]["value"] if "glass" in attributes.keys() else None
    img_dict["ethnicity"] = attributes["ethnicity"] if "ethnicity" in attributes.keys() else None
    img_dict["headpose"] = attributes["headpose"] if "headpose" in attributes.keys() else None
    img_dict["blurness"] = attributes["blur"]["blurness"]["value"] if "blur" in attributes.keys() and "blurness" in \
                                                                                                      attributes[
                                                                                                          "blur"].keys() else None

    return img_dict


def image_pre(file, userinfo):
    img_dict = {}
    img_dict['qrcont'] = detect_face_via_facepp(userinfo, file)
    if img_dict['qrcont'] is None:
        img_dict['Fail'] = True
        return img_dict

    qrcont_dict = eval(img_dict['qrcont'])

    # save face token
    img_dict['face_token'] = qrcont_dict['faces'][0]['face_token']

    # get face landmarks
    landmarks = qrcont_dict['faces'][0]['landmark']

    if landmarks is None:
        img_dict['Fail'] = True
        return img_dict
    else:
        img_dict['num_landmarks'] = len(landmarks)
        img_dict = update_dict_for_landmarks(img_dict, landmarks)

    # get face attributes
    attributes = qrcont_dict['faces'][0]['attributes']
    if attributes is None:
        img_dict['Fail'] = True
        return img_dict
    else:
        img_dict = update_dict_for_attributes(img_dict, attributes)

    face_rectangle = qrcont_dict['faces'][0]['face_rectangle']
    width = face_rectangle['width']
    top = face_rectangle['top']
    left = face_rectangle['left']
    height = face_rectangle['height']

    img_dict['position'] = (left, top, left + width, top + height)
    edge = int(height / 3)
    side = int(width / 5)
    img_dict['enlarge'] = (left - side, top - edge, left + width + side, top + height + edge)
    img_dict['Remove'] = False
    return img_dict


def img_remove(img_dict):
    # Remove Landmarks
    # if Num_Land(img_dict['landmark_qrcont'])<83 or img_dict['eyedist']<40 or (img_dict['headpose_dict']['yaw_angle']>15 and img_dict['headpose_dict']['pitch_angle']>10):
    #   images=np.delete(images,img_dict['index'])
    if 'Remove' not in img_dict.keys():
        return img_dict
    if img_dict['Remove'] is True:
        return img_dict
    if img_dict['num_landmarks'] < 83:
        img_dict['Remove'] = True
        img_dict['FEW_LANDMARK'] = True

    if (math.fabs(img_dict['headpose']['yaw_angle']) > 20 or math.fabs(
            img_dict['headpose']['pitch_angle']) > 20 or math.fabs(img_dict['headpose']['roll_angle']) > 30):
        img_dict['Remove'] = True
        img_dict['BAD_ANGLE'] = True

    if img_dict['eye_dist'] < 40:
        img_dict['Remove'] = True
        img_dict['NEAR_EYE'] = True

    if img_dict['glass_on_eye'] == "dark":
        img_dict['Remove'] = True
        img_dict['SUNGLASS'] = True

    if img_dict['mouth'] == "blocked":
        img_dict['Remove'] = True
        img_dict['MOUTH_BLOCK'] = True

    if img_dict['left_right_face_ratio'] < 1 / 2 or img_dict['left_right_face_ratio'] > 2:
        img_dict['Remove'] = True
        img_dict['LEFT_RIGHT_INBALANCE'] = True

    return img_dict


def saveFaces(file, save_dir, pos, low_resolution_threshold=120):
    low_resolution = False
    cropped_out = False
    dra_path = (file.split('/')[-1]).split('.')[-2]
    (x1, y1, x2, y2) = pos

    img = cv2.imread(file)
    width = img.shape[0]
    height = img.shape[1]
    out = False
    if x1 < 0 or y1 < 0 or x2 > width or y2 > height:
        out = True
    Original = Image.open(file).crop((x1, y1, x2, y2))
    opencvImage = cv2.cvtColor(np.array(Original), cv2.COLOR_RGB2BGR)
    if out:
        print('\tError: Too low resolution.')
        save_dir = save_dir + '/_cropped_out/'
        cropped_out = True
    elif opencvImage.shape[0] < low_resolution_threshold:
        print('\tError: Too low resolution.')
        save_dir = save_dir + '/_low_resolution/'
        low_resolution = True

    Resized = cv2.resize(opencvImage, (224, 224))
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    file_name = os.path.join(save_dir, dra_path + "_face.jpg")
    cv2.imwrite(file_name, Resized)
    return low_resolution, cropped_out, opencvImage.shape, np.mean(opencvImage), np.std(opencvImage)


def face_detector_caller(filename, folder_path):
    userinfo = {'key': "6rJYlqwU-0nEhkYGKELxpf30322cdsTE", 'secret': "-QXvSZJUqlozn4qrCNCuT5w3RBS7WrJp"}
    if not filename.endswith('.jpg'):
        return False
    file = folder_path + "/" + filename
    img_dict = image_pre(file, userinfo)
    img_dict = img_remove(img_dict)

    if 'Fail' in img_dict.keys():
        with open(folder_path + '/faces_info.csv', 'a') as f:
            f.write(u','.join([filename,'not 1 face']))
            f.write("\n")
        return False

    original_resolution = (0, 0, 0)
    color_mean = 0
    color_std = 0

    if 'Remove' not in img_dict.keys():
        return False
    result = False
    if img_dict['Remove'] is True:
        if 'BAD_ANGLE' in img_dict.keys():
            low_resolution, cropped_out, original_resolution, color_mean, color_std = saveFaces(file,
                                                                                                folder_path + '/_bad_angle',
                                                                                                img_dict['enlarge'])
            print('\tError: Bad face angle \n\t{}'.format(img_dict['headpose']))

        elif 'FEW_LANDMARK' in img_dict.keys():
            low_resolution, cropped_out, original_resolution, color_mean, color_std = saveFaces(file,
                                                                                                folder_path + '/_few_landmarks',
                                                                                                img_dict['enlarge'])
            print('\tError: Too few landmarks \n\t{}'.format(img_dict['num_landmarks']))
        elif 'LEFT_RIGHT_INBALANCE' in img_dict.keys():
            low_resolution, cropped_out, original_resolution, color_mean, color_std = saveFaces(file,
                                                                                                folder_path + '/_few_landmarks',
                                                                                                img_dict['enlarge'])
            print('\tError: Left right unbalance \n\t{}'.format(img_dict['left_right_face_ratio']))
        elif 'MOUTH_BLOCK' in img_dict.keys():
            low_resolution, cropped_out, original_resolution, color_mean, color_std = saveFaces(file,
                                                                                                folder_path + '/_left_right_unbalance',
                                                                                                img_dict['enlarge'])
            print('\tError: Mouth blocked \n\t{}'.format(img_dict['mouth']))
        elif 'SUNGLASS' in img_dict.keys():
            low_resolution, cropped_out, original_resolution, color_mean, color_std = saveFaces(file,
                                                                                                folder_path + '/_wear_sunglass',
                                                                                                img_dict['enlarge'])
            print('\tError: Wear sunglasses \n\t{}'.format(img_dict['glass_on_eye']))
        elif 'NEAR_EYE' in img_dict.keys():
            low_resolution, cropped_out, original_resolution, color_mean, color_std = saveFaces(file,
                                                                                                folder_path + '/_near_eyes',
                                                                                                img_dict['enlarge'])
            print('\tError: Small eye distance \n\t{}'.format(img_dict['eye_dist']))
    else:
        try:
            low_resolution, cropped_out, original_resolution, color_mean, color_std = saveFaces(file,
                                                                                                folder_path,
                                                                                                img_dict['enlarge'])
            if low_resolution:
                print('\tError: Low resolution \n\t{}'.format(original_resolution))
            elif cropped_out:
                print('\tError: Cropped out of the image \n\t')
            else:
                print('\tSuccess: 1 face saved - {}\t{}\t{}'.format(original_resolution, color_mean, color_std))
                result = True
        except KeyboardInterrupt:
            raise
        except:
            pass
    # write: filename, yaw, pitch, roll, original_resolution, position,
    with open(folder_path + '/faces_info.csv', 'a') as f:
        f.write(u','.join([str(i) for i in [filename,
                                            'Nan' if 'headpose' not in img_dict.keys() else
                                            img_dict['headpose'][
                                                'yaw_angle'],
                                            'Nan' if 'headpose' not in img_dict.keys() else
                                            img_dict['headpose'][
                                                'pitch_angle'],
                                            'Nan' if 'headpose' not in img_dict.keys() else
                                            img_dict['headpose'][
                                                'roll_angle'],
                                            original_resolution[0],
                                            'Nan' if 'position' not in img_dict.keys() else
                                            img_dict['position'][0],
                                            'Nan' if 'position' not in img_dict.keys() else
                                            img_dict['position'][1],
                                            'Nan' if 'position' not in img_dict.keys() else
                                            img_dict['position'][2],
                                            'Nan' if 'position' not in img_dict.keys() else
                                            img_dict['position'][3],
                                            'Nan' if 'mouth' not in img_dict.keys() else
                                            img_dict['mouth'],
                                            'Nan' if 'glass_on_eye' not in img_dict.keys() else
                                            img_dict['glass_on_eye'],
                                            'Nan' if 'ethnicity' not in img_dict.keys() else
                                            img_dict['ethnicity'],
                                            'Nan' if 'blurness' not in img_dict.keys() else
                                            img_dict['blurness'],
                                            'Nan' if 'glass' not in img_dict.keys() else
                                            img_dict['glass'],
                                            'Nan' if 'eye_dist' not in img_dict.keys() else
                                            img_dict['eye_dist'],
                                            'Nan' if 'left_right_face_ratio' not in img_dict.keys() else
                                            img_dict['left_right_face_ratio'],
                                            color_mean,
                                            color_std]]).encode('utf-8').strip())
        f.write("\n")
        return result
