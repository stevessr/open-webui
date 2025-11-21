import json
import logging
import time
from typing import Optional
import uuid
import asyncio

from open_webui.internal.db import Base, get_db
from open_webui.env import SRC_LOG_LEVELS

from open_webui.models.files import FileMetadataResponse
from open_webui.models.groups import Groups
from open_webui.models.users import Users, UserResponse


from pydantic import BaseModel, ConfigDict
from sqlalchemy import BigInteger, Column, String, Text, JSON

from open_webui.utils.access_control import has_access

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MODELS"])

####################
# Knowledge DB Schema
####################


class Knowledge(Base):
    __tablename__ = "knowledge"

    id = Column(Text, unique=True, primary_key=True)
    user_id = Column(Text)

    name = Column(Text)
    description = Column(Text)

    data = Column(JSON, nullable=True)
    meta = Column(JSON, nullable=True)

    access_control = Column(JSON, nullable=True)  # Controls data access levels.
    # Defines access control rules for this entry.
    # - `None`: Public access, available to all users with the "user" role.
    # - `{}`: Private access, restricted exclusively to the owner.
    # - Custom permissions: Specific access control for reading and writing;
    #   Can specify group or user-level restrictions:
    #   {
    #      "read": {
    #          "group_ids": ["group_id1", "group_id2"],
    #          "user_ids":  ["user_id1", "user_id2"]
    #      },
    #      "write": {
    #          "group_ids": ["group_id1", "group_id2"],
    #          "user_ids":  ["user_id1", "user_id2"]
    #      }
    #   }

    created_at = Column(BigInteger)
    updated_at = Column(BigInteger)


class KnowledgeModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str

    name: str
    description: str

    data: Optional[dict] = None
    meta: Optional[dict] = None

    access_control: Optional[dict] = None

    created_at: int  # timestamp in epoch
    updated_at: int  # timestamp in epoch


####################
# Forms
####################


class KnowledgeUserModel(KnowledgeModel):
    user: Optional[UserResponse] = None


class KnowledgeResponse(KnowledgeModel):
    files: Optional[list[FileMetadataResponse | dict]] = None


class KnowledgeUserResponse(KnowledgeUserModel):
    files: Optional[list[FileMetadataResponse | dict]] = None


class KnowledgeForm(BaseModel):
    name: str
    description: str
    data: Optional[dict] = None
    access_control: Optional[dict] = None


class KnowledgeTable:
    async def insert_new_knowledge(
        self, user_id: str, form_data: KnowledgeForm
    ) -> Optional[KnowledgeModel]:
        with get_db() as db:
            knowledge = KnowledgeModel(
                **{
                    **form_data.model_dump(),
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "created_at": int(time.time()),
                    "updated_at": int(time.time()),
                }
            )

            try:
                result = Knowledge(**knowledge.model_dump())
                await asyncio.to_thread(db.add, result)
                await asyncio.to_thread(db.commit)
                await asyncio.to_thread(db.refresh, result)
                if result:
                    return KnowledgeModel.model_validate(result)
                else:
                    return None
            except Exception:
                return None

    async def get_knowledge_bases(self) -> list[KnowledgeUserModel]:
        with get_db() as db:
            all_knowledge = await asyncio.to_thread(
                db.query(Knowledge).order_by(Knowledge.updated_at.desc()).all
            )

            user_ids = list(set(knowledge.user_id for knowledge in all_knowledge))

            users = await Users.get_users_by_user_ids(user_ids) if user_ids else []
            users_dict = {user.id: user for user in users}

            knowledge_bases = []
            for knowledge in all_knowledge:
                user = users_dict.get(knowledge.user_id)
                knowledge_bases.append(
                    KnowledgeUserModel.model_validate(
                        {
                            **KnowledgeModel.model_validate(knowledge).model_dump(),
                            "user": user.model_dump() if user else None,
                        }
                    )
                )
            return knowledge_bases

    async def check_access_by_user_id(self, id, user_id, permission="write") -> bool:
        knowledge = await self.get_knowledge_by_id(id)
        if not knowledge:
            return False
        if knowledge.user_id == user_id:
            return True
        user_group_ids = {group.id for group in await Groups.get_groups_by_member_id(user_id)}
        return has_access(user_id, permission, knowledge.access_control, user_group_ids)

    async def get_knowledge_bases_by_user_id(
        self, user_id: str, permission: str = "write"
    ) -> list[KnowledgeUserModel]:
        knowledge_bases = await self.get_knowledge_bases()
        user_group_ids = {group.id for group in await Groups.get_groups_by_member_id(user_id)}
        return [
            knowledge_base
            for knowledge_base in knowledge_bases
            if knowledge_base.user_id == user_id
            or has_access(
                user_id, permission, knowledge_base.access_control, user_group_ids
            )
        ]

    async def get_knowledge_by_id(self, id: str) -> Optional[KnowledgeModel]:
        try:
            with get_db() as db:
                knowledge = await asyncio.to_thread(db.query(Knowledge).filter_by(id=id).first)
                return KnowledgeModel.model_validate(knowledge) if knowledge else None
        except Exception:
            return None

    async def update_knowledge_by_id(
        self, id: str, form_data: KnowledgeForm, overwrite: bool = False
    ) -> Optional[KnowledgeModel]:
        try:
            with get_db() as db:
                knowledge = await self.get_knowledge_by_id(id=id)
                await asyncio.to_thread(db.query(Knowledge).filter_by(id=id).update,
                    {
                        **form_data.model_dump(),
                        "updated_at": int(time.time()),
                    }
                )
                await asyncio.to_thread(db.commit)
                return await self.get_knowledge_by_id(id=id)
        except Exception as e:
            log.exception(e)
            return None

    async def update_knowledge_data_by_id(
        self, id: str, data: dict
    ) -> Optional[KnowledgeModel]:
        try:
            with get_db() as db:
                knowledge = await self.get_knowledge_by_id(id=id)
                await asyncio.to_thread(db.query(Knowledge).filter_by(id=id).update,
                    {
                        "data": data,
                        "updated_at": int(time.time()),
                    }
                )
                await asyncio.to_thread(db.commit)
                return await self.get_knowledge_by_id(id=id)
        except Exception as e:
            log.exception(e)
            return None

    async def delete_knowledge_by_id(self, id: str) -> bool:
        try:
            with get_db() as db:
                await asyncio.to_thread(db.query(Knowledge).filter_by(id=id).delete)
                await asyncio.to_thread(db.commit)
                return True
        except Exception:
            return False

    async def delete_all_knowledge(self) -> bool:
        with get_db() as db:
            try:
                await asyncio.to_thread(db.query(Knowledge).delete)
                await asyncio.to_thread(db.commit)

                return True
            except Exception:
                return False


Knowledges = KnowledgeTable()
