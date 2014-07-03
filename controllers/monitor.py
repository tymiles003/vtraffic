import datetime
from datetime import timedelta

session.forget()
def box():
    if not(request.vars.id) or not(request.vars.id.isdigit()): return 'specificare id (integer)'
    station_id = int(request.vars.id)
    station = db(db.station.id == station_id).select(limitby=(0,1)).first()
    if not(station):
        raise(HTTP(500, "requested station doesn't exist"))
    station.update_record(last_check_on=request.now)
    time_delta = request.now - datetime.timedelta(days=1)
    query = (db.record.station_id == station_id) & (db.record.gathered_on > time_delta)
    empty = db(query).isempty()
    if empty:
        raise(HTTP(500, 'no logs'))
    else:
        return 'ok'        

def scheduler():
    query = (db.scheduler_task.status == 'FAILED')
    empty = db(query).isempty()
    if not(empty):
        raise(HTTP(500, 'task failed'))
    else:
        return 'ok'
