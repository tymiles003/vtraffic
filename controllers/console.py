import requests
from itertools import groupby

#tests
default_period = 3600
if request.vars.period:
	requested_period = int(request.vars.period) if request.vars.period.isdigit() else default_period
else:
    requested_period = default_period
    
if requested_period > 1000:
    seconds = int(datetime.timedelta(seconds=requested_period).total_seconds())
else:
    seconds = int(datetime.timedelta(days=requested_period).total_seconds())
    
    
# temp fix due to double menu
zero = request.args(0) or 'index'
if request.function != 'wiki' and zero and not(zero.isdigit()):
	from gluon.tools import Wiki
	response.menu += Wiki(auth, migrate=False).menu(function="wiki")

response.flash = ""

baseurl = "http://ipchannels.integreen-life.bz.it"
frontends = {'Meteo':'MeteoFrontEnd', 
             'Vehicle': 'VehicleFrontEnd', 
             'Environment':'EnvironmentFrontEnd', 
             'Parking': 'parkingFrontEnd',
             'Bluetooth':'BluetoothFrontEnd', 
             'Link':'LinkFrontEnd', 
             'Street': 'StreetFrontEnd', 
             'Traffic': 'TrafficFrontEnd'}
 
@auth.requires_login()
def index():
    session.forget(request)
    return response.render('console/index.html', {'frontends':frontends, 'seconds':seconds})

@auth.requires_login()
def get_stations():
    session.forget(request)
    frontend = request.vars.frontend
    if not frontend or frontend not in frontends:
        response.headers['web2py-component-flash'] = 'Select something'
        response.headers['web2py-component-content'] = 'hide'
        return ''
    response.headers['web2py-component-content'] = 'append'
    url = "%s/%s/rest/get-station-details" % (baseurl, frontends[frontend])
    r = requests.get(url) # params=url_vars)
    stations = r.json()
    response.headers['web2py-component-content'] = 'hide'
    response.headers['web2py-component-command'] = "add_after_form(xhr, 'form_frontend');"
    stations.sort(key=lambda v: v['name'])
    return response.render('console/stations_form.html', {'stations':stations, 'frontend':frontend})

@auth.requires_login()
def get_data_types():
    session.forget(request)
    station = request.vars.station
    frontend = request.vars.frontend
    if not (frontend and station) or frontend not in frontends:
        response.headers['web2py-component-flash'] = 'Select something'
        response.headers['web2py-component-content'] = 'hide'
        return ''
    response.headers['web2py-component-content'] = 'hide'
    response.headers['web2py-component-command'] = "append_to_sidebar(xhr, 'sidebar_console');"
    url = "%s/%s/rest/get-data-types" % (baseurl, frontends[frontend])
    r = requests.get(url, params={'station':station})

    data_types = r.json()
    data_types_filtered = data_types
    if frontend.lower() == 'vehicle':
        data_types_filtered = filter(lambda r: 'valid' not in r[0], data_types)
        data_types_filtered = filter(lambda r: 'runtime' not in r[0], data_types_filtered)
        data_types_filtered = filter(lambda r: 'id_' not in r[0], data_types_filtered)
        data_types_filtered = filter(lambda r: 'gps_' not in r[0] or 'speed' in r[0], data_types_filtered)

    data_types_filtered.sort(key=lambda v: (v[0],int(v[3])) if len(v)>3 and v[3].isdigit() else v[0])
    #data_types_filtered = [ [d[0].replace('_', ' '), d[1], d[2]] for d in data_types_filtered ]
    return response.render('console/data_types_legend.html', {'data_types':data_types_filtered, 'frontend':frontend, 'station':station })

@auth.requires_login()
def get_data():
    session.forget(request)
    frontend = request.vars.frontend
    station = request.vars.station 
    data_type = request.vars.data_type
    data_label = request.vars.data_label
    unit = request.vars.unit
    period = request.vars.period
    seconds = request.vars.seconds
    from_epoch = int(request.vars['from'])
    to_epoch = int(request.vars.to)

    url = "%s/%s/rest/get-records-in-timeframe" % (baseurl, frontends[frontend])
    params = {'station':station, 'name':data_type, 'unit':unit, 'from':from_epoch, 'to': to_epoch}
    if period:
        params['period'] = period
    r = requests.get(url, params=params)
    #print r.url
    data = r.json()

    if frontend == "Vehicle":
        #### Take 1 value every 5 or 10
        output = [ [data[i]['timestamp'], "%.2f" % float(data[i]['value'])]  for i in xrange(0, len(data), 10)]
    else:
        #### Average value every 5 seconds
        output = []
        f = lambda row: row['timestamp'] // 5000
        for key, group in groupby(data, f):
            list_ = list(group)
            list_values = [float(e['value']) for e in list_]
            avg_value = reduce(lambda x, y: x + y, list_values) / len(list_values)
            output.append( [key*5000, "%.2f" % avg_value] )

    # the id must be the same of the A element in the data type list
    series = [{'data':output, 'id': IS_SLUG()('type_%s_%s_%s' % (station,data_type,period))[0], 'station_id':'station_iud', 'label': "%s - %s" % (station, data_label)}]
    return response.json({'series': series})

# Return the template of the map
def map():
    return {}
