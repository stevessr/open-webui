from typing import Any, Dict
from urllib.parse import quote

from open_webui.models.users import UserModel


def include_user_info_headers(headers: Dict[str, Any], user: UserModel) -> Dict[str, Any]:
    return {
        **headers,
        "X-OpenWebUI-User-Name": quote(user.name, safe=" "),
        "X-OpenWebUI-User-Id": user.id,
        "X-OpenWebUI-User-Email": user.email,
        "X-OpenWebUI-User-Role": user.role,
    }
