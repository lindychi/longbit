from upbit.model.UpbitConfig import UpbitConfig

import uuid
from urllib.parse import urlencode
import hashlib
import jwt
import requests

def make_payload(user, url, query={}, method="GET"):
    try:
        config = UpbitConfig.objects.get(user=user)
    except UpbitConfig.DoesNotExist:
        config = UpbitConfig.objects.create(user=user)

    if not config.access_key:
        return {'error':{'message':'액세스키가 미등록 상태입니다.'}}
    
    payload = {
        'access_key': config.access_key,
        'nonce': str(uuid.uuid4())
    }

    query_string = ""
    if query:
        query_string = urlencode(query).encode()

        m = hashlib.sha512()
        m.update(query_string)
        query_hash = m.hexdigest()
        payload['query_hash'] = query_hash
        payload['query_hash_alg'] = 'SHA512'

    jwt_token = jwt.encode(payload, config.secret_key)
    authorize_token = 'Bearer {}'.format(jwt_token)
    headers = {"Authorization": authorize_token}

    if method == "GET":
        return requests.get('https://api.upbit.com{}'.format(url), params=query_string, headers=headers).json()
    else:
        return requests.post('https://api.upbit.com{}'.format(url), params=query, headers=headers).json()