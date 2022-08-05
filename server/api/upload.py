from flask import Blueprint, request
from configs import configs
import hashlib, time, secrets, os

print(__name__)
uploadApi = Blueprint('uploadApi', 'uploadapi')

allowedFileTypes = ('png', 'jpg')

@uploadApi.route('/upload', methods=['POST', 'GET'])
def upload():
    if not 'authentication' in request.headers:
        return {'error': 'No Authentication header'}, 400
    
    else: pass
    
    hash_auth_password = hashlib.sha256(configs['auth']['password']).hexdigest()

    if hash_auth_password == request.headers['authentication']  :
        return {'error': 'Invalid Authentication'}, 400
    
    if not 'file' in request.files:
        return {'error': 'No file?'}

    fileType = request.files['file'].filename.split('.')[-1]

    if not fileType in allowedFileTypes:
        return {'error': 'Invalid File Type'}, 400

    if len(os.listdir('images')) > configs['storage']['max_saved_images']:
        for img in os.listdir('images'):
            os.remove(f'images/{img}')

    UploadID = hashlib.sha256((str(time.time()) + secrets.token_urlsafe(16)).encode()).hexdigest()
    request.files['file'].save(f'images/{UploadID}.{fileType}')

    return {'message': 'Succesfully uploaded', 'uid': UploadID}, 200