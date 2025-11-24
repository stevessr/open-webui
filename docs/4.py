"""
title: Grok filter
licence: MIT
Credit: https://github.com/OVINC-CN/OpenWebUIPlugin.git
"""

from pydantic import BaseModel, Field


class Filter:
    class Valves(BaseModel):
        priority: int = Field(default=0, description="filter priority")

    class UserValves(BaseModel):
        web_search: bool = Field(default=False, description="Enable web search")
        x_search: bool = Field(default=False, description="Enable X search")
        code_interpreter: bool = Field(
            default=True, description="Enable code interpreter"
        )
        file_search: str = Field(
            default="", description="Enable file search 使用逗号分割多个文件"
        )
        mcp: str = Field(
            default="", description="Enable MCP list 使用逗号分割多个 url"
        )

    def __init__(self):
        self.valves = self.Valves()
        self.uservalves = self.UserValves()
        self.toggle = True
        self.icon = (
            "data:image/svg+xml;base64,PHN2ZyBkYXRhLXYtMmJjNjQ2MGU9IiIgdmlld0JveD0iMCAwIDQ4IDQ4IiBmaWxsPSJub25lIiB4bW"
            "xucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHN0cm9rZT0iY3VycmVudENvbG9yIiBjbGFzcz0iYXJjby1pY29uIGFyY28taW"
            "Nvbi1jb2RlIiBzdHJva2Utd2lkdGg9IjQiIHN0cm9rZS1saW5lY2FwPSJidXR0IiBzdHJva2UtbGluZWpvaW49Im1pdGVyIiBmaWx0ZX"
            "I9ImNvZGUiIHN0eWxlPSJmb250LXNpemU6IDMycHg7Ij48cGF0aCBkPSJNMTYuNzM0IDEyLjY4NiA1LjQyIDI0bDExLjMxNCAxMS4zMT"
            "RtMTQuNTIxLTIyLjYyOEw0Mi41NyAyNCAzMS4yNTUgMzUuMzE0TTI3LjIgNi4yOGwtNi4yNTEgMzUuNDUzIj48L3BhdGg+PC9zdmc+"
        )

    def inlet(self, body: dict, __user__: dict = None) -> dict:
        self.uservalves = __user__.get("valves") if __user__ else self.UserValves()
        if not body.get("tools"):
            body["tools"] = []
        if self.uservalves.web_search:
            body["tools"].append(
                {
                    "type": "web_search",
                }
            )

        if self.uservalves.x_search:
            body["tools"].append(
                {
                    "type": "x_search",
                }
            )

        if self.uservalves.code_interpreter:
            body["tools"].append(
                {
                    "type": "code_interpreter",
                }
            )

        if self.uservalves.file_search != "":
            body["tools"].append(
                {
                    "type": "file_search",
                    "files": [
                        files for files in self.uservalves.file_search.split(",")
                    ],
                }
            )

        if self.uservalves.mcp != "":
            for mcp_item in self.uservalves.mcp.split(","):
                body["tools"].append(
                    {
                        "type": "mcp",
                        "item": mcp_item,
                    }
                )
        return body
