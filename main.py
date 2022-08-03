from PySide6.QtCore import *
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import *

from PIL import Image, ImageDraw
from PIL.ImageQt import ImageQt

import io
import sys
import mss
import json
import keyboard
import win32clipboard

from data.selector import Ui_MainWindow

configs = json.loads(open('data\\configs.json', 'r').read())

OUTLINE = tuple(configs['selector']['outline_rgb'])
FILL = tuple(configs['selector']['fill_rgba'] + [50])
SHORTCUT = tuple([key.lower() for key in configs['shortcut'].split(' ')])

def clipboardCopy(clip_type, data):
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(clip_type, data)
    win32clipboard.CloseClipboard()

def PillowScreenshot():
    with mss.mss() as sct:
        sct_img = sct.grab(sct.monitors[1])
        return Image.frombytes('RGB', sct_img.size, sct_img.bgra, 'raw', 'BGRX')

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

            # Copy screenshot to clipboard
            output = io.BytesIO()
            cropped_im.convert("RGB").save(output, "BMP")
            data = output.getvalue()[14:]
            output.close()

            clipboardCopy(win32clipboard.CF_DIB, data)
            self.close()
        self.startpos = None
        super().mouseReleaseEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    print('Ready!')
    while True:
        keyboard.wait(SHORTCUT)
        window = SelectorWindow()
        app.exec()
