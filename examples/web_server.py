from aiohttp import web
import socketio
import threading

sio = socketio.AsyncServer()
app = web.Application()
sio.attach(app)

@sio.event
def connect(sid, environ):
    print("connect ", sid)

@sio.event
async def chat_message(sid, data):
    print("message ", data)
    await sio.emit('reply', {'foo': None}, room=sid)

@sio.event
def disconnect(sid):
    print('disconnect ', sid)

import os
from pymysqlreplication import BinLogStreamReader

MYSQL_SETTINGS = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "passwd": os.getenv("MYSQL_ROOT_PASSWORD", "")
}


def binlog():
    # server_id is your slave identifier, it should be unique.
    # set blocking to True if you want to block and wait for the next event at
    # the end of the stream
    stream = BinLogStreamReader(connection_settings=MYSQL_SETTINGS,
                                server_id=3,
                                blocking=True)

    for binlogevent in stream:
        binlogevent.dump()

    stream.close()

if __name__ == '__main__':
    threading.Thread(target=binlog).start()
    web.run_app(app)
