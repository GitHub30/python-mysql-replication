import eventlet
eventlet.monkey_patch()
import socketio
import threading
from pycolor import GREEN, END

sio = socketio.Server()
app = socketio.WSGIApp(sio)

@sio.event
def _query(sid, sql):
    print(GREEN + sql + END)
    conn = pymysql.connect(**MYSQL_SETTINGS)
    c = conn.cursor(pymysql.cursors.DictCursor)
    c.execute(sql)
    conn.close()
    return c.fetchall()

@sio.event
def _enter_room(sid, room_name):
    sio.enter_room(sid, room_name)


from os import getenv
import pymysql
from pymysqlreplication import BinLogStreamReader
from pymysqlreplication.row_event import WriteRowsEvent, UpdateRowsEvent, DeleteRowsEvent

MYSQL_SETTINGS = {
    'host': getenv('MYSQL_HOST', '127.0.0.1'),
    'port': getenv('MYSQL_PORT', 3306),
    'user': 'root',
    'passwd': getenv('MYSQL_ROOT_PASSWORD', ''),
    'database': getenv('MYSQL_DATABASE'),
    'charset': 'utf8mb4',
    'autocommit': True
}

def binlog():
    # server_id is your slave identifier, it should be unique.
    # set blocking to True if you want to block and wait for the next event at
    # the end of the stream
    only_events = [WriteRowsEvent, UpdateRowsEvent, DeleteRowsEvent]
    stream = BinLogStreamReader(connection_settings=MYSQL_SETTINGS, server_id=3, blocking=True, only_events=only_events)

    for binlogevent in stream:
        if sio.manager.rooms:
            values_key = 'after_values' if isinstance(binlogevent, UpdateRowsEvent) else 'values'
            for row in binlogevent.rows:
                room = binlogevent.table + '/' + str(row[values_key][binlogevent.primary_key])
                sio.emit(room, (row, binlogevent.__class__.__name__), room=room)
            sio.emit(binlogevent.table, (binlogevent.rows, binlogevent.__class__.__name__), room=binlogevent.table)
    stream.close()


if __name__ == '__main__':
    threading.Thread(target=binlog).start()
    host = getenv('FIRESQL_HOST', '')
    port = getenv('FIRESQL_PORT', 8080)
    eventlet.wsgi.server(eventlet.listen((host, port)), app)
