"""Small RFC 6455 server-to-browser text stream for local metrics.

Supports upgrade and unfragmented server text frames; client control stays on REST.
This is an unauthenticated LAN demonstration endpoint, NOT a public service.
"""
import base64
import hashlib
import json
import time

MAGIC='258EAFA5-E914-47DA-95CA-C5AB0DC85B11'

def encode_text_frame(text):
    payload=text.encode('utf-8')
    length=len(payload)
    if length<126:header=bytes([0x81,length])
    elif length<65536:header=bytes([0x81,126])+length.to_bytes(2,'big')
    else:header=bytes([0x81,127])+length.to_bytes(8,'big')
    return header+payload

def handle_websocket(handler,get_snapshot,period_s=.25):
    key=handler.headers.get('Sec-WebSocket-Key')
    if handler.headers.get('Upgrade','').lower()!='websocket' or not key:
        handler.send_error(400,'Expected WebSocket upgrade');return
    accept=base64.b64encode(hashlib.sha1((key+MAGIC).encode()).digest()).decode()
    handler.send_response(101,'Switching Protocols')
    handler.send_header('Upgrade','websocket');handler.send_header('Connection','Upgrade')
    handler.send_header('Sec-WebSocket-Accept',accept);handler.end_headers()
    try:
        while True:
            handler.wfile.write(encode_text_frame(json.dumps(get_snapshot(),default=str)))
            handler.wfile.flush();time.sleep(period_s)
    except (BrokenPipeError,ConnectionResetError,OSError):
        handler.close_connection=True
        return
