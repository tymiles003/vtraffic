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
        
def situation():
    if not(auth.is_logged_in()):
        db.station.id.readable=False
    grid = SQLFORM.grid(db.station, csv=False, searchable=False)
    return {'grid':grid}
    
    
def meteo():
    db_intime.station._common_filter = lambda query: db_intime.station.stationtype == 'Meteostation'
    return __check_measurementhistory('Meteo')

def environment():
    db_intime.station._common_filter = lambda query: db_intime.station.stationtype == 'Environmentstation'
    return __check_measurementhistory('Environment')
    
def parking():
    db_intime.station._common_filter = lambda query: db_intime.station.stationtype == 'ParkingStation'
    return __check_parkinghistory()

# check for each type if the data is not older than 1day
def __check_measurementhistory(name):
    time_delta = request.now - datetime.timedelta(days=1)
    max_ts = db_intime.measurementhistory.timestamp.max()
    query = (db_intime.measurementhistory.station_id == db_intime.station.id) & \
            (db_intime.measurementhistory.type_id == db_intime.type.id)
    query_having = (max_ts < time_delta)            
    id_list = db_intime(query).select(db_intime.measurementhistory.type_id,db_intime.measurementhistory.station_id, cacheable=True, 
                                      groupby=db_intime.measurementhistory.station_id | db_intime.measurementhistory.type_id, having=query_having).as_list()
    if len(id_list) != 0:
        raise(HTTP(500, '%s logs are older than 1day, %s' % (name, id_list)))
    else:
        return 'ok'

# check for each type if the data is not older than 1day
def __check_parkinghistory():
    time_delta = request.now - datetime.timedelta(days=1)
    max_ts = db_intime.carparkingdynamichistory.lastupdate.max()
    query = (db_intime.carparkingdynamichistory.station_id == db_intime.station.id)
    query_having = (max_ts < time_delta)
    id_list = db_intime(query).select(db_intime.carparkingdynamichistory.station_id, cacheable=True, 
                                      groupby=db_intime.carparkingdynamichistory.station_id, having=query_having).as_list()
    if len(id_list) != 0:
        raise(HTTP(500, '%s logs are older than 1day, %s' % ('Parking', id_list)))
    else:
        return 'ok'

def parking_3rd_parties():
    try:
        from xmlrpclib import ServerProxy
        from applications.vtraffic.modules.tools import TimeoutTransport
        provider = ServerProxy("http://84.18.134.218:7075/RPC2", transport=TimeoutTransport())
        parking_list = provider.pGuide.getElencoIdentificativiParcheggi()
        assert len(parking_list) != 0
        for p in parking_list:
            value = provider.pGuide.getPostiLiberiParcheggio(p)
            assert value != None
        return 'ok'
    except:
        raise(HTTP(500, 'Provider is either unreachable or no data are transferred'))
    
    
    
    
    
    
    
    
    
    
    
    
    
