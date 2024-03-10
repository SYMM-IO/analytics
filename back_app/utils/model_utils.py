from sqlalchemy import inspect


def get_model_fields(model):
    return [c.key for c in inspect(model).mapper.column_attrs]
    # fields = []
    # for attr_name, attr_value in inspect.getmembers(model):
    #     if not inspect.isfunction(attr_value) and not attr_name.startswith("_") and not inspect.ismethod(attr_value) and attr_name not in ["registry",
    #                                                                                                                                        "metadata"]:
    #         fields.append(attr_name)
    # return fields


def tag_tenant_to_field(data, tenant: str, field: str):
    data[field] = f"{tenant}_{data[field]}"
    return data
