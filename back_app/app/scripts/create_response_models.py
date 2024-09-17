import sys
from inspect import getmembers, isclass

from app.models import *  # noqa: F403

map_type = {
    "INTEGER": "int",
    "NUMERIC": "int",
    "FLOAT": "float",
    "BOOLEAN": "bool",
    "VARCHAR": "str",
    "TEXT": "str",
    "JSON": "str",
    "DATETIME": "datetime",
    datetime: "datetime",  # noqa: F405
    int: "int",
    str: "str",
    bool: "bool",
    float: "float",
}
with open("app/generated_response_models.py", "w") as f:
    f.write("from datetime import datetime\nfrom pydantic import BaseModel\n\n\n")
    my_models = [model[1] for model in getmembers(sys.modules[__name__], isclass) if issubclass(model[1], BaseModel) and model[0] != "BaseModel"]  # noqa: F405
    for model in my_models:
        f.write("class " + str(model).replace("<class 'app.models.", "").replace("'>", "") + "Model(BaseModel):\n")
        if "__table__" in getmembers(model)[3][1]:
            columns = getmembers(model)[3][1]["__table__"].columns
            for column in columns:
                if str(column.type).startswith("NUMERIC"):
                    f.write("\t" + str(column.key) + ": " + map_type.get("NUMERIC") + "\n")
                else:
                    f.write("\t" + str(column.key) + ": " + map_type.get(str(column.type)) + "\n")
        else:
            attrs = model.__annotations__
            for k in attrs:
                print(k)
                f.write("\t" + k + ": " + map_type.get(str(attrs[k])) + "\n")
        f.write("\n\n")
