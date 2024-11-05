import enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Type, Dict, Optional

import requests
from sqlalchemy.orm import Session

from src.app import BaseModel
from src.app.models import RuntimeConfiguration
from src.config.settings import Context
from src.services.config_service import load_config
from src.utils.block import Block
from src.utils.model_utils import tag_tenant_to_field, get_model_fields


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


@dataclass
class LoadParams:
    fields: List[str]
    conditions: List[GraphQlCondition]
    formatted_pv: Optional[str] = field(init=False, repr=True)
    order_by: Optional[str] = field(init=False, repr=True)


class SubgraphClient:
    def __init__(self, context: Context, proxies: dict = None):
        self.context = context
        self.proxies = proxies

    def create_function(self, model: Type[BaseModel], data, session: Session = None):
        config = model.__subgraph_client_config__
        for f in config.tenant_needed_fields:
            tag_tenant_to_field(data, self.context.tenant, f)
        for key, value in config.name_maps.items():
            data[key] = data[value]
            del data[value]
        if session:
            data["tenant"] = self.context.tenant
        data = config.converter(data)
        obj = model(**data)
        if session:
            obj.upsert(session)
        return obj

    def load(
        self,
        load_params_map: Dict[Type[BaseModel], LoadParams],
        first: int,
        create_function,
        block: Block = None,
        order_direction: OrderDirection = OrderDirection.DESCENDING,
        change_block_gte: int = None,
        log_prefix="",
    ):
        query = "query q {"
        for model, params in load_params_map.items():
            method = model.__subgraph_client_config__.method_name
            condition = aggregate_conditions([w for w in params.conditions if not w.is_empty()])
            where_str = ""
            if len(condition) > 0 or change_block_gte:
                where_str += "where: "
                cb_addition = []
                if change_block_gte:
                    cb_addition.append(f"_change_block: {{number_gte: {change_block_gte}}}")
                where_str += f"{{ {', '.join(cb_addition + [str(w) for w in condition])}  }}"

            print(f"|{log_prefix}: Loading a page of {method}----------")
            print(f"|    condition: {where_str}")
            print(f"|    change after block: {change_block_gte}")
            print(f"|    in block: {block.number if block else ''}")

            query += f"""
                    {method}(
                        {f'block: {{ number: {block.number} }}' if block else ''}
                        first: {first},
                        {f'orderBy: {params.order_by}, orderDirection: {order_direction.value}' if params.order_by else ''}
                        {where_str}
                        ) {{ """
            for f in params.fields:
                query += f"\n\t\t\t{f}"

            query += """
                        }
            """
        query += """
                }
        """
        subgraph_query = {"query": query}
        response = requests.post(self.context.subgraph_endpoint, json=subgraph_query, proxies=self.proxies)
        items = dict()
        if response:
            if "data" in response.json():
                for model in load_params_map:
                    method = model.__subgraph_client_config__.method_name
                    items[model] = []
                    print(f"-------> Loaded {len(response.json()['data'][method])} items ---------")
                    for data in response.json()["data"][method]:
                        items[model].append(create_function(model, data))
            elif "errors" in response.json():
                raise Exception(f"{log_prefix}: Failed to load data from subgraph " + str(response.json()))
            else:
                raise Exception(response.json())
        else:
            raise Exception(response.text)
        return items

    def load_all(
        self,
        load_params_map: Dict[Type[BaseModel], LoadParams],
        create_function,
        block: Block = None,
        page_limit: int = None,
        change_block_gte: int = None,
        log_prefix="",
    ):
        limit = 1000
        pagination_values = {model: None for model in load_params_map}
        result = set()
        while page_limit is None or page_limit > 0:
            if page_limit is not None:
                page_limit -= 1
            for model, params in load_params_map.items():
                if isinstance(pagination_values[model], datetime):
                    params.formatted_pv = str(int(pagination_values[model].timestamp()))
                elif pagination_values[model]:
                    params.formatted_pv = str(pagination_values[model])
                else:
                    params.formatted_pv = None
            for model, params in load_params_map.items():
                config = model.__subgraph_client_config__
                params.order_by = config.name_maps.get(config.pagination_field) or config.pagination_field
                params.conditions = (
                    [GraphQlCondition(params.order_by, "gte", params.formatted_pv)] if params.formatted_pv else []
                ) + params.conditions
            items = self.load(
                load_params_map=load_params_map,
                create_function=create_function,
                first=limit,
                log_prefix=log_prefix,
                change_block_gte=change_block_gte,
                block=block,
                order_direction=OrderDirection.ASCENDING,
            )
            is_done = True
            for model in pagination_values:
                config = model.__subgraph_client_config__
                temp = items[model]
                is_done = is_done and len(temp) < limit
                if len(temp) > 0:
                    yield [d for d in temp if d not in result]
                    result.update(temp)
                    for item in temp:
                        if item:
                            pagination_values[model] = getattr(temp[-1], config.pagination_field)
                            break
            if is_done:
                break

    def sync(self, session, block: Block, transaction_id, models: List[Type[BaseModel]] = None):
        runtime_config: RuntimeConfiguration = load_config(session, self.context, transaction_id)
        load_params_map = dict()
        for model in models:
            config = model.__subgraph_client_config__
            fields = []
            for f in get_model_fields(model):
                if f in config.ignore_columns:
                    continue
                if f in config.name_maps:
                    fields.append(config.name_maps[f])
                else:
                    fields.append(f)
            load_params_map[model] = LoadParams(fields=fields, conditions=[])

        out = self.load_all(
            load_params_map=load_params_map,
            create_function=lambda model, data: self.create_function(model, data, session=session),
            block=block,
            change_block_gte=runtime_config.lastSyncBlock,
            log_prefix=self.context.tenant,
        )
        for o in out:
            pass
