from datetime import datetime

from fastapi import FastAPI
from pydantic import BaseModel

from src.app.server import app


def generate_typescript_types(app: FastAPI, output_file: str):
    type_definitions = []
    response_models = {route.response_model for route in app.routes if hasattr(route, "response_model")}
    for model in list(response_models):
        if not isinstance(model, type):
            response_models.remove(model)
            response_models.add(model.__args__[0])
    for model in response_models:
        if isinstance(model, type) and issubclass(model, BaseModel):
            type_def = generate_type_definition(model)
            type_definitions.append(type_def)

    with open(output_file, "w") as f:
        f.write("\n\n".join(type_definitions))


def generate_type_definition(model: type) -> str:
    fields = model.__fields__
    properties = []

    for name, field in fields.items():
        property_type = get_typescript_type(field.annotation)
        properties.append(f"  {name}: {property_type};")

    return f"export interface {model.__name__} {{\n" + "\n".join(properties) + "\n}"


def get_typescript_type(python_type) -> str:
    type_mapping = {
        int: "number",
        float: "number",
        str: "string",
        bool: "boolean",
        list: "any[]",
        dict: "{ [key: string]: any }",
        datetime: "number",
    }

    return type_mapping.get(python_type, "any")


if __name__ == "__main__":
    generate_typescript_types(app, "types/generated_types.ts")
