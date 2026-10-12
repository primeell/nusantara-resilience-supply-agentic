"""Loopback-only authenticated OpenAI-compatible proxy for SAP AI Core.
Run with: python -m uvicorn bridge.proxy:app --host 127.0.0.1 --port 8765
"""
import os
from contextlib import asynccontextmanager
from typing import Any

import requests
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

from .sap_common import SAPClient

_CLIENT = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _CLIENT
    if not os.environ.get('NSRA_PROXY_KEY'):
        raise RuntimeError('NSRA_PROXY_KEY missing in .env; run setup first')
    _CLIENT = SAPClient()
    yield


app = FastAPI(title='Local SAP AI Core Bridge', lifespan=lifespan,
              docs_url=None, redoc_url=None, openapi_url=None)


@app.get('/health')
def health():
    return {'status': 'ok', 'backend': 'SAP AI Core', 'auth': 'required for chat'}


@app.get('/v1/models')
def models(authorization: str | None = Header(default=None)):
    check_auth(authorization)
    return {'object': 'list', 'data': [{'id': 'sap-gpt54', 'object': 'model'}]}


def check_auth(authorization):
    import hmac
    key = os.environ['NSRA_PROXY_KEY']
    if not authorization or not hmac.compare_digest(authorization, 'Bearer ' + key):
        raise HTTPException(status_code=401, detail='Unauthorized')


def relay_stream(upstream):
    try:
        for chunk in upstream.iter_content(chunk_size=8192):
            if chunk:
                yield chunk
    finally:
        upstream.close()


@app.post('/v1/chat/completions')
async def chat(request: Request, authorization: str | None = Header(default=None)):
    check_auth(authorization)
    payload: dict[str, Any] = await request.json()
    # The SAP deployment is fixed by the server, never by arbitrary client input.
    payload.pop('model', None)
    # OpenCode SDK may send stream_options not understood by some SAP deployments.
    payload.pop('stream_options', None)
    stream = bool(payload.get('stream'))
    try:
        upstream = _CLIENT.post(payload, stream=stream)
    except requests.RequestException:
        return JSONResponse(status_code=502, content={'error': {'message': 'Upstream network error (details hidden)'}})
    except Exception as exc:
        return JSONResponse(status_code=502, content={'error': {'message': f'SAP authentication/request failed ({type(exc).__name__}); details hidden'}})
    if not upstream.ok:
        status = upstream.status_code
        upstream.close()
        # Client sees upstream status but never tokens or verbose SAP response body.
        return JSONResponse(status_code=502, content={'error': {'message': f'SAP inference returned HTTP {status}; upstream body hidden'}})
    if stream:
        return StreamingResponse(relay_stream(upstream), media_type='text/event-stream',
                                 headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})
    try:
        result = upstream.json()
    except ValueError:
        return JSONResponse(status_code=502, content={'error': {'message': 'SAP inference returned non-JSON response'}})
    finally:
        upstream.close()
    return result
