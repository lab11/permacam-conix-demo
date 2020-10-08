#!/usr/bin/env python3

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
parser.add_argument('-d', '--save_file', default='.', help='Optional save detected images to file')
parser.add_argument('-u', '--url_path', help='Optional location of hosted images')
args = parser.parse_args()

filename = args.save_file
if not args.url_path:
    url_path = filename
else:
    url_path = args.url_path

i_origin = (0,2,0)

arena.init("arena.andrew.cmu.edu", "realm", "hello")
arena_image = arena.Object(objType=arena.Shape.cube, location=i_origin, data='{"material": {"src": "tmp.png"}}')

def on_connect(client, userdata, flags, rc):
    print("connected with code " + str(rc))
    client.subscribe(args.topic)

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode('utf-8'))
        print('got message ' + data['_meta']['topic'] + ' on ' + msg.topic)
        image_id = 0
        if 'image_id' in data:
            image_id = data['image_id']
        if data['_meta']['topic'] == 'image_jpeg':
            if 'image_is_demosaiced' not in data or not data['image_is_demosaiced']:
                print("not demosaiced!")
                return
            # get jpeg format
            jpeg = BytesIO(base64.b64decode(data['image_jpeg']))
            image = Image.open(jpeg)
            image.save(args.save_file, format='PNG')
            arena_data = '{"material": {"src": "' +  url_path + '"}}'
            print(arena_data)
            arena_image.update(data=arena_data)
    except Exception as e:
        print(e)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(args.subscribe_host)

client.loop_start()
arena.handle_events()
