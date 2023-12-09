from flask import jsonify, request, abort
from flask_cors import cross_origin
from flask_restx import Namespace, Resource, fields

from config.local_settings import admin_api_key
from utils.common_utils import load_config

ns = Namespace(
    "Configs", description="Configuration endpoints", decorators=[cross_origin()]
)

update_configuration_model = ns.model(
    "Configuration",
    {
        "binanceDeposit": fields.String(
            description="PartyB binance deposits", required=False
        ),
    },
)


@ns.route("/update_configuration")
class UpdateConfiguration(Resource):
    @ns.expect(update_configuration_model)
    def post(self):
        params = request.get_json()
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            abort(401, "Unauthorized")
        if auth_header != admin_api_key:
            abort(403, "Forbidden")

        config = load_config()
        if "binanceDeposit" in params:
            config.binanceDeposit = params["binanceDeposit"]
        config.upsert()
        return jsonify(message="Updated successfully")


@ns.route("/get_configuration")
class GetConfiguration(Resource):
    def get(self):
        config = load_config()
        return jsonify(
            {
                "binanceDeposit": config.binanceDeposit,
                "decimals": config.decimals,
                "lastSnapshotTimestamp": config.lastSnapshotTimestamp,
            }
        )
