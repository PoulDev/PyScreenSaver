from flask import Flask, render_template, send_file, url_for
from configs import configs
from PIL import Image

import os
from api import uploadApi

owner = configs['owner']
anonymous = configs['owner']['anonymous']

app = Flask(__name__)
app.register_blueprint(uploadApi, url_prefix='/api')

@app.route('/')
def home():
    return render_template(
        'index.html',
        owner=owner['username'],
        redirect_link=owner['redirect_link'],
        anonymous=anonymous)

@app.route('/<imgID>')
def imageEmbed(imgID):
    if not os.path.exists(f'images/{imgID}.png'):
        return f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PyScreenSaver</title>
    <meta content="404 Image not found" property="og:title" />
    <meta name="theme-color" content="#e63737">
<body>
</body>
</html>
'''
    pilImg = Image.open(f'images/{imgID}.png')
    return render_template(
        'image.html',
        owner = configs['owner']['username'] if not configs['owner']['anonymous'] else 'by an anonymous user',
        imgID = imgID,
        color = configs['embed']['color'],
        width = pilImg.size[0],
        height = pilImg.size[1],
    )

@app.route('/images/<imgID>')
def getImage(imgID):
    if not os.path.exists(f'images/{imgID}.png'):
        return "404 Image not found"
    return send_file(f'images/{imgID}.png')

app.run('0.0.0.0', configs["port"], debug=True)