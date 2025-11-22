import asyncio
import logging
import time
from typing import Optional

from open_webui.env import SRC_LOG_LEVELS
from open_webui.internal.db import Base, JSONField, get_db
from open_webui.models.users import UserModel, Users
from pydantic import BaseModel, ConfigDict
from sqlalchemy import BigInteger, Boolean, Column, Index, String, Text

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MODELS"])

####################
# Functions DB Schema
####################


class Function(Base):
    __tablename__ = "function"

    id = Column(String, primary_key=True)
    user_id = Column(String)
    name = Column(Text)
    type = Column(Text)
    content = Column(Text)
    meta = Column(JSONField)
    valves = Column(JSONField)
    is_active = Column(Boolean)
    is_global = Column(Boolean)
    updated_at = Column(BigInteger)
    created_at = Column(BigInteger)

    __table_args__ = (Index("is_global_idx", "is_global"),)


class FunctionMeta(BaseModel):
    description: Optional[str] = None
    manifest: Optional[dict] = {}
    model_config = ConfigDict(extra="allow")


class FunctionModel(BaseModel):
    id: str
    user_id: str
    name: str
    type: str
    content: str
    meta: FunctionMeta
    is_active: bool = False
    is_global: bool = False
    updated_at: int  # timestamp in epoch
    created_at: int  # timestamp in epoch

    model_config = ConfigDict(from_attributes=True)


class FunctionWithValvesModel(BaseModel):
    id: str
    user_id: str
    name: str
    type: str
    content: str
    meta: FunctionMeta
    valves: Optional[dict] = None
    is_active: bool = False
    is_global: bool = False
    updated_at: int  # timestamp in epoch
    created_at: int  # timestamp in epoch

    model_config = ConfigDict(from_attributes=True)


####################
# Forms
####################


class FunctionUserResponse(FunctionModel):
    user: Optional[UserModel] = None


class FunctionResponse(BaseModel):
    id: str
    user_id: str
    type: str
    name: str
    meta: FunctionMeta
    is_active: bool
    is_global: bool
    updated_at: int  # timestamp in epoch
    created_at: int  # timestamp in epoch


class FunctionForm(BaseModel):
    id: str
    name: str
    content: str
    meta: FunctionMeta


class FunctionValves(BaseModel):
    valves: Optional[dict] = None


class FunctionsTable:
    async def insert_new_function(
        self, user_id: str, type: str, form_data: FunctionForm
    ) -> Optional[FunctionModel]:
        function = FunctionModel(
            **{
                **form_data.model_dump(),
                "user_id": user_id,
                "type": type,
                "updated_at": int(time.time()),
                "created_at": int(time.time()),
            }
        )

        try:
            with get_db() as db:
                result = Function(**function.model_dump())
                await asyncio.to_thread(db.add, result)
                await asyncio.to_thread(db.commit)
                await asyncio.to_thread(db.refresh, result)
                if result:
                    return FunctionModel.model_validate(result)
                else:
                    return None
        except Exception as e:
            log.exception(f"Error creating a new function: {e}")
            return None

    async def sync_functions(
        self, user_id: str, functions: list[FunctionWithValvesModel]
    ) -> list[FunctionWithValvesModel]:
        # Synchronize functions for a user by updating existing ones, inserting new ones, and removing those that are no longer present.
        try:
            with get_db() as db:
                # Get existing functions
                existing_functions = await asyncio.to_thread(db.query(Function).all)
                existing_ids = {func.id for func in existing_functions}

                # Prepare a set of new function IDs
                new_function_ids = {func.id for func in functions}

                # Update or insert functions
                for func in functions:
                    if func.id in existing_ids:
                        await asyncio.to_thread(db.query(Function).filter_by(id=func.id).update,
                            {
                                **func.model_dump(),
                                "user_id": user_id,
                                "updated_at": int(time.time()),
                            }
                        )
                    else:
                        new_func = Function(
                            **{
                                **func.model_dump(),
                                "user_id": user_id,
                                "updated_at": int(time.time()),
                            }
                        )
                        await asyncio.to_thread(db.add, new_func)

                # Remove functions that are no longer present
                for func in existing_functions:
                    if func.id not in new_function_ids:
                        await asyncio.to_thread(db.delete, func)

                await asyncio.to_thread(db.commit)

                return [
                    FunctionModel.model_validate(func)
                    for func in await asyncio.to_thread(db.query(Function).all)
                ]
        except Exception as e:
            log.exception(f"Error syncing functions for user {user_id}: {e}")
            return []

    async def get_function_by_id(self, id: str) -> Optional[FunctionModel]:
        try:
            with get_db() as db:
                function = await asyncio.to_thread(db.get, Function, id)
                return FunctionModel.model_validate(function)
        except Exception:
            return None

    async def get_functions(
        self, active_only=False, include_valves=False
    ) -> list[FunctionModel | FunctionWithValvesModel]:
        with get_db() as db:
            if active_only:
                functions = await asyncio.to_thread(db.query(Function).filter_by(is_active=True).all)

            else:
                functions = await asyncio.to_thread(db.query(Function).all)

            if include_valves:
                return [
                    FunctionWithValvesModel.model_validate(function)
                    for function in functions
                ]
            else:
                return [
                    FunctionModel.model_validate(function) for function in functions
                ]

    async def get_function_list(self) -> list[FunctionUserResponse]:
        with get_db() as db:
            functions = await asyncio.to_thread(db.query(Function).order_by(Function.updated_at.desc()).all)
            user_ids = list(set(func.user_id for func in functions))

            users = await Users.get_users_by_user_ids(user_ids) if user_ids else []
            users_dict = {user.id: user for user in users}

            return [
                FunctionUserResponse.model_validate(
                    {
                        **FunctionModel.model_validate(func).model_dump(),
                        "user": (
                            users_dict.get(func.user_id).model_dump()
                            if func.user_id in users_dict
                            else None
                        ),
                    }
                )
                for func in functions
            ]

    async def get_functions_by_type(
        self, type: str, active_only=False
    ) -> list[FunctionModel]:
        with get_db() as db:
            if active_only:
                functions = await asyncio.to_thread(
                    db.query(Function).filter_by(type=type, is_active=True).all
                )
            else:
                functions = await asyncio.to_thread(
                    db.query(Function).filter_by(type=type).all
                )
            return [FunctionModel.model_validate(function) for function in functions]

    async def get_global_filter_functions(self) -> list[FunctionModel]:
        with get_db() as db:
            functions = await asyncio.to_thread(
                db.query(Function)
                .filter_by(type="filter", is_active=True, is_global=True)
                .all
            )
            return [FunctionModel.model_validate(function) for function in functions]

    async def get_global_action_functions(self) -> list[FunctionModel]:
        with get_db() as db:
            functions = await asyncio.to_thread(
                db.query(Function)
                .filter_by(type="action", is_active=True, is_global=True)
                .all
            )
            return [FunctionModel.model_validate(function) for function in functions]

    async def get_function_valves_by_id(self, id: str) -> Optional[dict]:
        with get_db() as db:
            try:
                function = await asyncio.to_thread(db.get, Function, id)
                return function.valves if function.valves else {}
            except Exception as e:
                log.exception(f"Error getting function valves by id {id}: {e}")
                return None

    async def update_function_valves_by_id(
        self, id: str, valves: dict
    ) -> Optional[FunctionValves]:
        with get_db() as db:
            try:
                function = await asyncio.to_thread(db.get, Function, id)
                function.valves = valves
                function.updated_at = int(time.time())
                await asyncio.to_thread(db.commit)
                await asyncio.to_thread(db.refresh, function)
                return await self.get_function_by_id(id)
            except Exception:
                return None

    async def update_function_metadata_by_id(
        self, id: str, metadata: dict
    ) -> Optional[FunctionModel]:
        with get_db() as db:
            try:
                function = await asyncio.to_thread(db.get, Function, id)

                if function:
                    if function.meta:
                        function.meta = {**function.meta, **metadata}
                    else:
                        function.meta = metadata

                    function.updated_at = int(time.time())
                    await asyncio.to_thread(db.commit)
                    await asyncio.to_thread(db.refresh, function)
                    return await self.get_function_by_id(id)
                else:
                    return None
            except Exception as e:
                log.exception(f"Error updating function metadata by id {id}: {e}")
                return None

    async def get_user_valves_by_id_and_user_id(
        self, id: str, user_id: str
    ) -> Optional[dict]:
        try:
            user = await Users.get_user_by_id(user_id)
            user_settings = user.settings.model_dump() if user.settings else {}

            # Check if user has "functions" and "valves" settings
            if "functions" not in user_settings:
                user_settings["functions"] = {}
            if "valves" not in user_settings["functions"]:
                user_settings["functions"]["valves"] = {}

            return user_settings["functions"]["valves"].get(id, {})
        except Exception:
            log.exception(f"Error getting user values by id {id} and user id {user_id}")
            return None

    async def update_user_valves_by_id_and_user_id(
        self, id: str, user_id: str, valves: dict
    ) -> Optional[dict]:
        try:
            user = await Users.get_user_by_id(user_id)
            user_settings = user.settings.model_dump() if user.settings else {}

            # Check if user has "functions" and "valves" settings
            if "functions" not in user_settings:
                user_settings["functions"] = {}
            if "valves" not in user_settings["functions"]:
                user_settings["functions"]["valves"] = {}

            user_settings["functions"]["valves"][id] = valves

            # Update the user settings in the database
            await Users.update_user_by_id(user_id, {"settings": user_settings})

            return user_settings["functions"]["valves"][id]
        except Exception as e:
            log.exception(
                f"Error updating user valves by id {id} and user_id {user_id}: {e}"
            )
            return None

    async def update_function_by_id(self, id: str, updated: dict) -> Optional[FunctionModel]:
        with get_db() as db:
            try:
                await asyncio.to_thread(db.query(Function).filter_by(id=id).update,
                    {
                        **updated,
                        "updated_at": int(time.time()),
                    }
                )
                await asyncio.to_thread(db.commit)
                return await self.get_function_by_id(id)
            except Exception:
                return None

    async def deactivate_all_functions(self) -> Optional[bool]:
        with get_db() as db:
            try:
                await asyncio.to_thread(db.query(Function).update,
                    {
                        "is_active": False,
                        "updated_at": int(time.time()),
                    }
                )
                await asyncio.to_thread(db.commit)
                return True
            except Exception:
                return None

    async def delete_function_by_id(self, id: str) -> bool:
        with get_db() as db:
            try:
                await asyncio.to_thread(db.query(Function).filter_by(id=id).delete)
                await asyncio.to_thread(db.commit)

                return True
            except Exception:
                return False


Functions = FunctionsTable()
