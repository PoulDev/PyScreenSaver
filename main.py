import ctypes
import hashlib
from typing import Any, Callable, Union
from PySide6.QtCore import *
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import *

from PIL import Image, ImageDraw
from PIL.ImageQt import ImageQt

import os
import io
import sys
import mss
import json
import win32con
import win32gui
import ctypes
import keyboard
import pyperclip
import requests
import random
import string
import win32clipboard
from ftplib import FTP


from data.selector import Ui_MainWindow


configs = json.loads(open('data\\configs.json', 'r').read())

OUTLINE = tuple(configs['selector']['outline_rgb'])
FILL = tuple(configs['selector']['fill_rgba'] + [50])
SHORTCUT = tuple([key.lower() for key in configs['shortcut'].split(' ')])

def send_to_clipboard(clip_type, data):
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(clip_type, data)
    win32clipboard.CloseClipboard()

def PillowScreenshot():
    with mss.mss() as sct:
        sct_img = sct.grab(sct.monitors[1])
        return Image.frombytes('RGB', sct_img.size, sct_img.bgra, 'raw', 'BGRX')

def uploadToServer():
    return requests.post(
        f'http://{configs["server"]["server_ip"]}:{configs["server"]["server_port"]}/api/upload',
        files = {
            'file': open('screenshot.png', 'rb')
        },
        headers = {"authentication" : hashlib.sha256(configs['server']['server_password'].encode()).hexdigest()}
    ).json()

class UploadMethod:
    INSTANCE: Any = None

    def __init__(self):
        if UploadMethod.INSTANCE:
            raise RuntimeError('UploadMethod is a singletone Object.')
        UploadMethod.INSTANCE = self
        self.save_image = self._find_upload_method()

    def animate_cursor(self):
        cursor = win32gui.LoadImage(0, 32512, win32con.IMAGE_CURSOR, 
            0, 0, win32con.LR_SHARED)
        self.system_cursor = ctypes.windll.user32.CopyImage(cursor, win32con.IMAGE_CURSOR, 
            0, 0, win32con.LR_COPYFROMRESOURCE)

        cursor = win32gui.LoadImage(0, "working.ani", win32con.IMAGE_CURSOR, 
                0, 0, win32con.LR_LOADFROMFILE);
        ctypes.windll.user32.SetSystemCursor(cursor, 32512)
        ctypes.windll.user32.DestroyCursor(cursor);


    def restore_cursor(self):
        ctypes.windll.user32.SetSystemCursor(self.system_cursor, 32512)
        ctypes.windll.user32.DestroyCursor(self.system_cursor);

    def _find_upload_method(self) -> Callable:
        for upload_method, method_function in {'ftp_server': self._ftp_upload, 'server': self._server_upload}.items():
            if configs[upload_method]['enabled']:
                return method_function
        return self._clipboard_save

    def _ftp_upload(self, image: Image.Image) -> None:
        filename = 'screenshot_' + ''.join(random.choices(string.ascii_letters, k=15)) + '.png'
        image.save(filename)
        with FTP(
                configs['ftp_server']['address'],
                configs['ftp_server']['username'],
                configs['ftp_server']['password']) as ftp, open(filename, 'rb') as file:
            ftp.cwd(configs['ftp_server']['directory'])
            ftp.storbinary(f'STOR {filename}', file)

        pyperclip.copy(f'{configs["ftp_server"]["url"]}/{filename}')
        try:
            os.remove(filename)
        except: pass

    def _server_upload(self, image: Image.Image) -> None:
        image.save('screenshot.png')
        res = uploadToServer()
        if not 'uid' in res:
            ctypes.windll.user32.MessageBoxW(0, res['error'], "Upload Error", 0)
        else:
            pyperclip.copy(f'http://{configs["server"]["server_ip"]}:{configs["server"]["server_port"]}/{res["uid"]}')
        try:
            os.remove('screenshot.png')
        except: pass

    def _clipboard_save(self, image: Image.Image) -> None:
        output = io.BytesIO()
        image.convert("RGB").save(output, "BMP")
        data = output.getvalue()[14:]
        output.close()
        send_to_clipboard(win32clipboard.CF_DIB, data)


UploadMethod()

class SelectorWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.showFullScreen()
        
        self.originalImg = PillowScreenshot()
        self.ui.image.setPixmap(QPixmap.fromImage(ImageQt(self.originalImg)))

        self.show()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        return super().keyPressEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.startpos = (event.position().x(),event.position().y())
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.newpos = (event.scenePosition().x(),event.scenePosition().y())

            drawImage = self.originalImg.copy()
            img1 = ImageDraw.Draw(drawImage, 'RGBA')

            img1.rectangle([self.startpos, self.newpos], fill=FILL, outline=OUTLINE)

            self.ui.image.setPixmap(QPixmap.fromImage(ImageQt(drawImage)))
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.startpos[1] > self.newpos[1]:
                rect = (*self.newpos, *self.startpos)
            else:
                rect = (*self.startpos, *self.newpos)

            try:
                cropped_im = self.originalImg.copy().crop(rect)
            except Exception as e:
                print(rect)
                print(e)
                return self.ui.image.setPixmap(QPixmap.fromImage(ImageQt(self.originalImg)))

            self.close()
            UploadMethod.INSTANCE.animate_cursor()
            UploadMethod.INSTANCE.save_image(cropped_im)
            UploadMethod.INSTANCE.restore_cursor()

        self.startpos = None
        super().mouseReleaseEvent(event)

os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    print('Ready!')
    while True:
        keyboard.wait(SHORTCUT)
        window = SelectorWindow()
        app.exec()
