from dataclasses import dataclass, field
from typing import Optional, Callable, Any, List, Dict

from config.settings import Context
from context.graphql_client import Where
from services.config_service import load_config
from utils.model_utils import tag_tenant_to_field, get_model_fields
from utils.time_utils import convert_timestamps


@dataclass
class SubgraphSynchronizerConfig:
    method_name: str
    pagination_field: str
    catch_up_field: str
    ignore_columns: List[str] = field(default_factory=lambda: ["tenant"])
    tenant_needed_fields: Optional[List[str]] = field(default_factory=list)
    name_maps: Optional[Dict[str, str]] = field(default_factory=dict)
    converter: Optional[Callable[[Any], Any]] = convert_timestamps


class SubgraphSynchronizer:
    def __init__(self, context: Context, model):
        self.context = context
        self.model = model
        self.config: SubgraphSynchronizerConfig = model.__subgraph_synchronizer_config__

    def create_function(self, session, data):
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

    def sync(self, session):
        runtime_config = load_config(session, self.context)
        fields = []
        for f in get_model_fields(self.model):
            if f in self.config.ignore_columns:
                continue
            if f in self.config.name_maps:
                fields.append(self.config.name_maps[f])
            else:
                fields.append(f)

        out = self.context.utils.gc.load_all(
            session,
            lambda data: self.create_function(session, data),
            model=self.model,
            method=self.config.method_name,
            fields=fields,
            pagination_field_name=self.config.pagination_field,
            additional_conditions=[
                Where(
                    self.config.catch_up_field,
                    "gte",
                    str(int(runtime_config.lastSnapshotTimestamp.timestamp())),
                ),
                Where(
                    self.config.pagination_field,
                    "lte",
                    str(int(runtime_config.nextSnapshotTimestamp.timestamp())),
                ),
            ],
            include_database_data=False,
            context=self.context,
        )
        for o in out:
            pass
