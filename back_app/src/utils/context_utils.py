from src.config.local_settings import contexts
from src.config.settings import Context


def get_context(name: str) -> Context | None:
    for context in contexts:
        if context.tenant == name:
            return context
    return None
