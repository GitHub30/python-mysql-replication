import eventlet
eventlet.monkey_patch()
import socketio
import threading
import asyncio

sio = socketio.Server()
app = socketio.WSGIApp(sio)
connected = False

@sio.event
def connect(sid, environ):
    print("connect ", sid)
    global connected
    connected = True

@sio.event
def query(sid, sql):
    print("query ", type(sql))
    conn = pymysql.connect(**MYSQL_SETTINGS)
    c = conn.cursor()
    c.execute(sql)
    #conn.close()
    result = c.fetchall()
    print('result type', type(result), result)
    return result
    #await sio.emit('reply', {'foo': None}, room=sid)

@sio.event
def disconnect(sid):
    print('disconnect ', sid)


import os
import pymysql
from pymysqlreplication import BinLogStreamReader

MYSQL_SETTINGS = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "passwd": os.getenv("MYSQL_ROOT_PASSWORD", ""),
    "charset": "utf8mb4",
    "autocommit": True
}

def binlog():
    # server_id is your slave identifier, it should be unique.
    # set blocking to True if you want to block and wait for the next event at
    # the end of the stream
    stream = BinLogStreamReader(connection_settings=MYSQL_SETTINGS,
                                server_id=3,
                                blocking=True)

    for binlogevent in stream:
        print(type(binlogevent), connected)
        if hasattr(binlogevent, 'rows') and connected:
            print(sio, type(binlogevent.rows))
            sio.emit('reply', binlogevent.rows)

    stream.close()

if __name__ == '__main__':
    threading.Thread(target=binlog).start()
    eventlet.wsgi.server(eventlet.listen(('', 8080)), app)
