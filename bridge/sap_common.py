import os
import time
from pathlib import Path
import requests
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

PROJECT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT / '.env', override=False)
DEPLOYMENT_ID = (
    os.environ.get('SAP_GPT_DEPLOYMENT_ID', '').strip()
    or os.environ.get('SAP_DEPLOYMENT_ID', '').strip()
)
RESOURCE_GROUP = os.environ.get('SAP_RESOURCE_GROUP', 'default')
API_VERSION = (
    os.environ.get('SAP_AI_API_VERSION', '').strip()
    or os.environ.get('SAP_API_VERSION', '2024-12-01-preview').strip()
)


def config():
    cfg = {name: os.environ.get(name, '').strip() for name in (
        'SAP_CLIENT_ID', 'SAP_CLIENT_SECRET', 'SAP_AUTH_URL', 'SAP_AI_API_URL')}
    absent = [k for k, v in cfg.items() if not v]
    if not DEPLOYMENT_ID:
        absent.append('SAP_GPT_DEPLOYMENT_ID')
    if absent:
        raise RuntimeError('Missing .env fields: ' + ', '.join(absent))
    return cfg


class SAPClient:
    def __init__(self):
        self.cfg = config()
        self._token = None
        self._valid_until = 0

    def token(self):
        if self._token and time.time() < self._valid_until:
            return self._token
        auth_base = self.cfg['SAP_AUTH_URL'].rstrip('/')
        # Hackathon service key uses an authorization server root URL.
        auth_url = auth_base if auth_base.endswith('/oauth/token') else auth_base + '/oauth/token'
        resp = requests.post(
            auth_url,
            auth=HTTPBasicAuth(self.cfg['SAP_CLIENT_ID'], self.cfg['SAP_CLIENT_SECRET']),
            data={'grant_type': 'client_credentials'}, timeout=25,
        )
        if not resp.ok:
            raise RuntimeError(f'OAuth failed: HTTP {resp.status_code} (response hidden)')
        result = resp.json()
        self._token = result['access_token']
        self._valid_until = time.time() + max(30, int(result.get('expires_in', 300)) - 90)
        return self._token

    def endpoint(self):
        api_root = self.cfg['SAP_AI_API_URL'].rstrip('/')
        return f'{api_root}/v2/inference/deployments/{DEPLOYMENT_ID}/chat/completions'

    def headers(self):
        return {
            'Authorization': 'Bearer ' + self.token(),
            'AI-Resource-Group': RESOURCE_GROUP,
            'Content-Type': 'application/json',
        }

    def post(self, payload, stream=False):
        return requests.post(self.endpoint(), headers=self.headers(),
                             params={'api-version': API_VERSION},
                             json=payload, stream=stream, timeout=(15, 180))
