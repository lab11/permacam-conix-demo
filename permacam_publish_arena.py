#!/usr/bin/env python3
import os
import argparse
import json
import base64
from PIL import Image
from io import BytesIO
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import arena

parser = argparse.ArgumentParser(description='Subscribe to Permacam Images and display in an ARENA scene')
parser.add_argument('-s', '--subscribe_host', default='localhost', help='Optional mqtt hostname to subscribe/publish from/to, default is localhost')
parser.add_argument('-t', '--topic', default='device/Permacam/#', help='Optional mqtt topic to subscribe/publish from/to, default is "device/Permacam/#"')
parser.add_argument('-d', '--save_dir', default='.', help='Optional save detected images to file')
parser.add_argument('-u', '--url_path', help='Optional location of hosted images')
args = parser.parse_args()

if not args.url_path:
    url_path = args.save_dir.strip()
else:
    url_path = args.url_path.strip()

arena.init("arena.andrew.cmu.edu", "realm", "hello")
arena_image = arena.Object(objType=arena.Shape.cube, location=(0,1.5,0))
arena_detect = arena.Object(objType=arena.Shape.cube, location=(1.5,1.5,0))

def on_connect(client, userdata, flags, rc):
    print("connected with code " + str(rc), flush=True)
    client.subscribe(args.topic)

previous_image = None

def on_message(client, userdata, msg):
    global previous_image
    try:
        data = json.loads(msg.payload.decode('utf-8'))
        image_id = 0
        if 'image_id' in data:
            image_id = data['image_id']

        topic = data['_meta']['topic']
        if topic == 'image_jpeg' or topic == 'image_detection_jpeg':
            if 'image_is_demosaiced' not in data or not data['image_is_demosaiced']:
                return
            # get jpeg format
            jpeg = BytesIO(base64.b64decode(data['image_jpeg']))
            image = Image.open(jpeg)
            if previous_image:
                os.remove(previous_image)
            det_fname = "_"
            if topic == 'image_detection_jpeg':
                det_fname = "_detect_"
            fname = '/permacam_latest' + det_fname + str(image_id) + '.png'
            image.save(args.save_dir.strip() + fname, format='PNG')
            previous_image = args.save_dir.strip() + fname
            arena_data = '{"material": {"src": "' + url_path + fname + '"}}'
            print(arena_data, flush=True)
            if topic == 'image_detection_jpeg':
                arena_detect.update(data=arena_data)
            else:
                arena_image.update(data=arena_data)
    except Exception as e:
        print(e, flush=True)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(args.subscribe_host)

client.loop_start()
arena.handle_events()
