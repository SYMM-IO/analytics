from sqlalchemy import inspect


def get_model_fields(model):
    return [c.key for c in inspect(model).mapper.column_attrs]


def tag_tenant_to_field(data, tenant: str, field: str):
    data[field] = f"{tenant}_{data[field]}"
    return data


def log_object_properties(obj):
    class_name = obj.__class__.__name__
    properties = [f"{class_name=}"]

    if obj:
        for column in inspect(obj.__class__).mapper.column_attrs:
            property_name = column.key
            property_value = getattr(obj, property_name)
            properties.append(f"{property_name}: {property_value}")

    return properties
