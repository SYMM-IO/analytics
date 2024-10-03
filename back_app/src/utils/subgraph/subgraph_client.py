import enum
from datetime import datetime
from typing import List, Type

import requests
from sqlalchemy.orm import Session

from src.app import BaseModel
from src.app.models import RuntimeConfiguration
from src.config.settings import Context
from src.services.config_service import load_config
from src.utils.block import Block
from src.utils.model_utils import tag_tenant_to_field, get_model_fields
from src.utils.subgraph.subgraph_client_config import SubgraphClientConfig


class GraphQlCondition:
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


class OrderDirection(enum.Enum):
    ASCENDING = "asc"
    DESCENDING = "desc"


def aggregate_conditions(conditions: List[GraphQlCondition]) -> List[GraphQlCondition]:
    filtered_dict = {}
    for c in conditions:
        key = f"{c.field}-{c.operator}"
        if key in filtered_dict:
            if c.value > filtered_dict[key].value:
                filtered_dict[key] = c
        else:
            filtered_dict[key] = c
    return list(filtered_dict.values())


class SubgraphClient:
    def __init__(self, context: Context, model: Type[BaseModel], proxies: dict = None):
        self.context = context
        self.model: Type[BaseModel] = model
        self.config: SubgraphClientConfig = model.__subgraph_client_config__
        self.proxies = proxies

    def create_function(self, session: Session, data):
        for f in self.config.tenant_needed_fields:
            tag_tenant_to_field(data, self.context.tenant, f)
        for key, value in self.config.name_maps.items():
            data[key] = data[value]
            del data[value]
        data["tenant"] = self.context.tenant
        data = self.config.converter(data)
        obj = self.model(**data)
        obj.upsert(session)
        return obj

    def load(
        self,
        method: str,
        fields: List[str],
        first: int,
        create_function,
        block: Block = None,
        conditions: List[GraphQlCondition] = None,
        order_by: str = None,
        order_direction: OrderDirection = OrderDirection.DESCENDING,
        change_block_gte: int = None,
        log_prefix="",
    ):
        if conditions is None:
            conditions = []
        conditions = aggregate_conditions([w for w in conditions if not w.is_empty()])
        where_str = ""
        if len(conditions) > 0 or change_block_gte:
            where_str += "where: "
            cb_addition = []
            if change_block_gte:
                cb_addition.append(f"_change_block: {{number_gte: {change_block_gte}}}")
            where_str += f"{{ {', '.join(cb_addition + [str(w) for w in conditions])}  }}"

        print(f"|{log_prefix}: Loading a page of {method}----------")
        print(f"|    condition: {where_str}")
        print(f"|    change after block: {change_block_gte}")
        print(f"|    in block: {block.number if block else ''}")

        query = f"""
            query q {{
                {method}(
                    {f'block: {{ number: {block.number} }}' if block else ''}
                    first: {first},
                    {f'orderBy: {order_by}, orderDirection: {order_direction.value}' if order_by else ''}
                    {where_str}
                    ) {{ """
        for f in fields:
            query += f"\n\t\t\t{f}"

        query += """
                    }
                }
        """
        subgraph_query = {"query": query}
        response = requests.post(self.context.subgraph_endpoint, json=subgraph_query, proxies=self.proxies)
        items = []
        if response:
            if "data" in response.json():
                print(f"-------> Loaded {len(response.json()['data'][method])} items ---------")
                for data in response.json()["data"][method]:
                    items.append(create_function(data))
            elif "errors" in response.json():
                raise Exception(f"{log_prefix}: Failed to load data from subgraph " + str(response.json()))
            else:
                raise Exception(response.json())
        else:
            raise Exception(response.text)
        return items

    def load_all(
        self,
        fields: List[str],
        create_function,
        block: Block = None,
        conditions: List[GraphQlCondition] = None,
        page_limit: int = None,
        change_block_gte: int = None,
        log_prefix="",
    ):
        if not conditions:
            conditions = []
        limit = 1000
        pagination_value = None

        result = set()
        while page_limit is None or page_limit > 0:
            if page_limit is not None:
                page_limit -= 1
            if isinstance(pagination_value, datetime):
                formatted_pv = str(int(pagination_value.timestamp()))
            elif pagination_value:
                formatted_pv = str(pagination_value)
            else:
                formatted_pv = None
            pagination_field_name = self.config.name_maps.get(self.config.pagination_field) or self.config.pagination_field
            temp = self.load(
                method=self.config.method_name,
                fields=fields,
                create_function=create_function,
                first=limit,
                conditions=([GraphQlCondition(pagination_field_name, "gte", formatted_pv)] if formatted_pv else []) + conditions,
                log_prefix=log_prefix,
                change_block_gte=change_block_gte,
                block=block,
                order_by=pagination_field_name,
                order_direction=OrderDirection.ASCENDING,
            )
            is_done = False
            if len(temp) > 0:
                yield [d for d in temp if d not in result]
                result.update(temp)
                for item in temp:
                    if item:
                        pagination_value = getattr(temp[-1], self.config.pagination_field)
                        break
                    else:
                        is_done = True
            if is_done or len(temp) < limit:
                break

    def sync(self, session, block: Block, transaction_id):
        runtime_config: RuntimeConfiguration = load_config(session, self.context, transaction_id)
        fields = []
        for f in get_model_fields(self.model):
            if f in self.config.ignore_columns:
                continue
            if f in self.config.name_maps:
                fields.append(self.config.name_maps[f])
            else:
                fields.append(f)

        out = self.load_all(
            fields=fields,
            create_function=lambda data: self.create_function(session, data),
            log_prefix=self.context.tenant,
            change_block_gte=runtime_config.lastSyncBlock,
            block=block,
        )
        for o in out:
            pass
