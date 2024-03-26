import datetime


def convert_timestamps(data):
    output = {}
    for key, value in data.items():
        if "timestamp" in key.lower():
            output[key] = datetime.datetime.fromtimestamp(int(value))
        else:
            output[key] = value
    return output
