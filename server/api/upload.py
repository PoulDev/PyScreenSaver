from flask import Blueprint, request
from configs import configs
import hashlib, secrets, os

print(__name__)
uploadApi = Blueprint('uploadApi', 'uploadapi')

allowedFileTypes = ('png', 'jpg')

@uploadApi.route('/upload', methods=['POST', 'GET'])
def upload():
    if not 'authentication' in request.headers:
        return {'error': 'No Authentication'}, 400
    
    hash_auth_password = hashlib.sha256(configs['auth']['password']).hexdigest()

    if hash_auth_password == request.headers['authentication']  :
        return {'error': 'Invalid Authentication'}, 400
    
    if not 'file' in request.files:
        return {'error': 'No file?'}

    fileType = request.files['file'].filename.split('.')[-1]

    if not fileType in allowedFileTypes:
        return {'error': 'Invalid File Type'}, 400

    imagesFile = os.listdir('images')
    if len(imagesFile) > configs['storage']['max_saved_images']:
        for img in imagesFile:
            os.remove(f'images/{img}')

    UploadID = str(len(imagesFile)) + secrets.token_urlsafe(8)[:4]

    request.files['file'].save(f'images/{UploadID}.{fileType}')

    return {'message': 'Succesfully uploaded', 'uid': UploadID}, 200