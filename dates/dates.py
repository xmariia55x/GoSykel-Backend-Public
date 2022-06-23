from datetime import datetime

def date_to_timestamp(date, time):
    date_aux = datetime.strptime(date + " " + time, '%d-%m-%Y %H:%M')
    return datetime.timestamp(date_aux)

def timestamp_to_date(stamp):
    date_aux = datetime.fromtimestamp(stamp)
    date = datetime.strftime(date_aux, '%d-%m-%Y')
    time = datetime.strftime(date_aux, '%H:%M')
    return date, time
