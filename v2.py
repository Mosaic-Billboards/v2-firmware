#### v2 FIRMWARE ####
#### By Aaren Stade ####
#### 0.0.7 ####
#### March 2021 ####

import os
import pyrebase
import requests
import httplib2
import tkinter as tk
from PIL import ImageTk, Image, ImageDraw, ImageFont

#####  q#### CONSTANTS #########
FIREBASE_CONFIG = {
    "apiKey": "AIzaSyDNyQyZF2P7Rn6lOzYOKh-UHB5YPdWOb_I",
    "authDomain": "mosaic-billboards.firebaseapp.com",
    "databaseURL": "https://mosaic-billboards.firebaseio.com",
    "projectId": "mosaic-billboards",
    "storageBucket": "mosaic-billboards.appspot.com",
}
BILLBOARD_ID = "v2m1-001"
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 1920
WORKING_DIR = "/home/v2-firmware/"
IMAGES_PATH = os.path.join(WORKING_DIR, "images/")
SCREENS_PATH = os.path.join(WORKING_DIR, "screens/")
FIRMWARE_FILE = os.path.join(WORKING_DIR, "firmware.txt")
DISPLAY_TIME = 6500
MAX_IMAGES = 5

######### VARIABLES #########
current_image = None
label = None
image_list = []
rot_index = 0

root = tk.Tk()
firebase = pyrebase.initialize_app(FIREBASE_CONFIG)
db = firebase.database()

class Root_Window(object):
    def __init__(self, master, **kwargs):
        self.tk = master
        self.tk.configure(background='black')
        self.tk.title('v2-process')
        self.tk.geometry(str(WINDOW_WIDTH) + 'x' + str(WINDOW_HEIGHT))
        self.tk.attributes('-fullscreen', True)
        self.frame = tk.Frame(self.tk)
        self.frame.pack()
        self.tk.bind("<Escape>", self.end_fullscreen)

    def end_fullscreen(self, event=None):
        self.tk.attributes('-fullscreen', False)
        self.tk.quit()

###############################################
# PROCESS UPLOAD SCREEN FUNCTIONS
###############################################

def get_old_price():
    path = os.path.join(WORKING_DIR, 'price.txt')
    if (os.path.exists(path)):
        with open(path) as pricef:
            price = pricef.read()
        return str(price)

def write_new_price(price):
    path = os.path.join(WORKING_DIR, 'price.txt')
    if (os.path.exists(path)):
        os.remove(path)
    with open(path, 'w') as pricef:
        pricef.write(str(price))

def generate_upload_screen(price):
    file_path = os.path.join(SCREENS_PATH, 'upload.jpg')
    if (os.path.exists(file_path)):
        os.remove(file_path)
    text = "${:,.2f}".format(price)
    img = Image.open(os.path.join(WORKING_DIR, 'base-upload-screen.jpg'))
    draw = ImageDraw.Draw(img)
    fnt = ImageFont.truetype(os.path.join(WORKING_DIR, 'AlteHaasGroteskBold.ttf'), 300)
    w, h = draw.textsize(text, font=fnt)
    draw.text(((WINDOW_WIDTH-w)/2,((WINDOW_HEIGHT-h)/2) + 27), text, font=fnt,fill="black")
    img.save(file_path)
    write_new_price(price)

###############################################
# QUERY AND DISPLAY FUNCTIONS
###############################################

def create_tk_image(path):
    global current_image
    try:
        if (current_image):
            current_image.close()
        current_image = None
        current_image = open_image(path)
        img = ImageTk.PhotoImage(image=current_image)
        return img
    except:
        print('image {} failed to open'.format(path))
        return None

def display_image(path):
    global label
    new_image = create_tk_image(path)
    if (new_image != None):
        if (label != None):
            label.configure(image=new_image)
            label.image = new_image
        else:
            label = tk.Label(root, image=new_image, highlightthickness=0)
        label.pack(expand=True)  

def append_image_list(filename):
    global image_list
    if (len(image_list) < MAX_IMAGES):
        image_list.append(filename)
    else:
        delete_image(image_list[0])
        image_list.append(filename)

def download_image(filename, url):
    if(url != None):
        global image_list
        file_path = os.path.join(IMAGES_PATH, filename)
        request = requests.get(url, stream=True)
        print('downloading image...')
        if not request.ok:
            print(request.text)
        with open(file_path, 'wb') as img_file:
            for block in request.iter_content(1024):
                if not block:
                    break
                img_file.write(block)
            img_file.close()
        append_image_list(filename)

def open_image(path):
    img = Image.open(path)
    resized = img.resize((WINDOW_WIDTH, WINDOW_HEIGHT), Image.ANTIALIAS)
    return resized

def delete_image(delete_filename):
    global image_list
    file_path = os.path.join(IMAGES_PATH, delete_filename)
    if (os.path.exists(file_path)):
        os.remove(file_path)
        image_list.remove(delete_filename)

def handle_query(data):
    try:
        upload_id = data['image']['uuid']
        upload_url = data['image']['url']
        upload_filename = upload_id + '.jpg'
        if not (upload_filename in image_list):
            download_image(upload_filename, upload_url)
    except:
        pass

def handle_query(data):
    try:
        upload_id = data['image']['uuid']
        upload_url = data['image']['image']
        upload_filename = upload_id + '.jpg'
        if not (upload_filename in image_list):
            download_image(upload_filename, upload_url)
    except:
        pass
    try:
        price = data['price']
        old_price = get_old_price()
        if (str(price) != old_price):
            generate_upload_screen(price)
    except:
        pass

def query_for_new_ads():
    query = db.child(BILLBOARD_ID).get()
    data = query.val()
    if (data != None):
        handle_query(data)

###############################################
# MAIN CONTROL FUNCTIONS
###############################################

def check_connection(url='www.google.com', timeout=15):
    req = httplib2.HTTPConnectionWithTimeout(url, timeout=timeout);
    try:
        req.request('HEAD', "/")
        req.close()
        print('connected')
        return True
    except Exception as e:
        print('no connection: {}'.format(e))
        return False;

def rotate_index():
    global rot_index
    if (rot_index >= len(image_list)):
        rot_index = 0
    else:
        rot_index = rot_index + 1
    print('rotated index to {}'.format(rot_index))
    return rot_index

def init_images():
    if not (os.path.exists(IMAGES_PATH)):
        os.mkdir(IMAGES_PATH)
    else:
        global image_list
        image_list = [f for f in os.listdir(IMAGES_PATH) if os.path.isfile(os.path.join(IMAGES_PATH, f))]

def loop():
    if (rot_index != len(image_list)):
        display_image(os.path.join(IMAGES_PATH, image_list[rot_index]))
    else:
        display_image(os.path.join(SCREENS_PATH, 'upload.jpg'))
    has_connection = check_connection()
    if (has_connection == True):
        query_for_new_ads()
    rotate_index()
    root.after(DISPLAY_TIME, loop)


def setup():
    Root_Window(root)
    init_images()

if __name__ == "__main__":
    setup()
    loop()
    root.mainloop()