from sqlalchemy import inspect


def get_model_fields(model):
    return [c.key for c in inspect(model).mapper.column_attrs]


def tag_tenant_to_field(data, tenant: str, field: str):
    data[field] = f"{tenant}_{data[field]}"
    return data
