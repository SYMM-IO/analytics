import datetime
from typing import List

import requests
from sqlalchemy import select, delete
from sqlalchemy.orm import Session


def is_int(s):
    try:
        int(s)
        return True
    except Exception:
        return False


class Where:
    def __init__(self, field: str, operator: str | None, value: str):
        self.field = field
        self.operator = operator
        self.value = value

    def is_empty(self):
        return self.field == "" or self.value == ""

    def __str__(self):
        if self.is_empty():
            return ""
        else:
            return f"{self.field}{f'_{self.operator}' if self.operator else ''}: {self.value}"


def aggregate_wheres(wheres: List[Where]):
    filtered_dict = {}
    for where in wheres:
        key = f"{where.field}-{where.operator}"
        if key in filtered_dict:
            if where.value > filtered_dict[key].value:
                filtered_dict[key] = where
        else:
            filtered_dict[key] = where
    return list(filtered_dict.values())


class GraphQlClient:
    def __init__(self, endpoint: str, proxies: dict = None):
        self.endpoint = endpoint
        self.proxies = proxies

    def load(
        self,
        create_function,
        method: str,
        fields: List[str],
        first: int,
        wheres: List[Where] = None,
        order_by: str = None,
        context=None,
    ):
        if wheres is None:
            wheres = []
        wheres = aggregate_wheres([w for w in wheres if not w.is_empty()])
        where_str = ""
        if len(wheres) > 0:
            where_str += "where: "
            where_str += f"{{ {', '.join([str(w) for w in wheres])}  }}"

        log_prefix = f"{context.tenant}: " if context else ""
        print(f"{log_prefix}Loading a page of {method} with condition: {where_str}")

        query = f"""
            query q {{
                {method}(
                    first: {first},
                    {f'orderBy: {order_by}' if order_by else ''}
                    {where_str}
                    ) {{ """
        for f in fields:
            query += f"\n\t\t\t{f}"

        query += """
                    }
                }
        """
        subgraph_query = {"query": query}
        response = requests.post(self.endpoint, json=subgraph_query, proxies=self.proxies)
        items = []
        if response:
            if "data" in response.json():
                for data in response.json()["data"][method]:
                    items.append(create_function(data))
            elif "errors" in response.json():
                raise Exception(f"{log_prefix}Failed to load data from subgraph " + str(response.json()))

        return items

    def load_all(
        self,
        session: Session,
        create_function,
        model,
        method: str,
        fields: List[str],
        pagination_field_name: str,
        pagination_field_name_std: str = None,
        pagination_value=None,
        additional_conditions: List[Where] = None,
        page_limit: int = None,
        include_database_data=True,
        context=None,
    ):
        from app.models import BaseModel

        model: BaseModel

        if not pagination_field_name_std:
            pagination_field_name_std = pagination_field_name

        if not additional_conditions:
            additional_conditions = []

        limit = 1000
        org_pagination_value = pagination_value

        pagination_field = getattr(model, pagination_field_name_std)

        if include_database_data:
            found_items = session.scalar(select(model).order_by(pagination_field.desc()).limit(1))
            if found_items:
                found_pagination_value = getattr(found_items[0], pagination_field_name_std)
                if isinstance(found_pagination_value, int) or is_int(found_pagination_value):
                    pagination_value = max(
                        int(found_pagination_value),
                        int(pagination_value) if pagination_value else 0,
                    )
                elif isinstance(found_pagination_value, datetime.datetime):
                    if pagination_value:
                        if not isinstance(pagination_value, datetime.datetime):
                            raise Exception("Invalid last where value")
                        pagination_value = found_pagination_value if found_pagination_value > pagination_value else pagination_value
                else:
                    raise Exception("Unsupported pagination field")

                session.execute(delete(model).where(pagination_field == pagination_value))

            if org_pagination_value:
                yield session.scalars(select(model).where(pagination_field > org_pagination_value).order_by(pagination_field.asc()))
            else:
                yield session.scalars(select(model).order_by(pagination_field.asc()))

        result = set()
        while page_limit is None or page_limit > 0:
            if page_limit is not None:
                page_limit -= 1
            formatted_pv = None
            if isinstance(pagination_value, datetime.datetime):
                formatted_pv = str(int(pagination_value.timestamp()))
            elif pagination_value:
                formatted_pv = str(pagination_value)
            temp = self.load(
                create_function,
                method,
                fields,
                limit,
                ([Where(pagination_field_name, "gte", formatted_pv)] if formatted_pv else []) + additional_conditions,
                pagination_field_name,
                context=context,
            )
            is_done = False
            if len(temp) > 0:
                yield [d for d in temp if d not in result]
                result.update(temp)
                for item in reversed(temp):
                    if item:
                        pagination_value = getattr(temp[-1], pagination_field_name_std)
                        break
                    else:
                        is_done = True
            if is_done or len(temp) < limit:
                break
