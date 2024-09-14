import datetime


def convert_timestamps(data):
    output = {}
    for key, value in data.items():
        if "timestamp" in key.lower() and value:
            output[key] = datetime.datetime.fromtimestamp(int(value))
        else:
            output[key] = value
    return output
