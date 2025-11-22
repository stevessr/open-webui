import asyncio
import logging
import time
from typing import Optional

from open_webui.env import SRC_LOG_LEVELS
from open_webui.internal.db import Base, get_db
from pydantic import BaseModel, ConfigDict
from sqlalchemy import JSON, BigInteger, Column, String, Text

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MODELS"])

####################
# Files DB Schema
####################


class File(Base):
    __tablename__ = "file"
    id = Column(String, primary_key=True)
    user_id = Column(String)
    hash = Column(Text, nullable=True)

    filename = Column(Text)
    path = Column(Text, nullable=True)

    data = Column(JSON, nullable=True)
    meta = Column(JSON, nullable=True)

    access_control = Column(JSON, nullable=True)

    created_at = Column(BigInteger)
    updated_at = Column(BigInteger)


class FileModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    hash: Optional[str] = None

    filename: str
    path: Optional[str] = None

    data: Optional[dict] = None
    meta: Optional[dict] = None

    access_control: Optional[dict] = None

    created_at: Optional[int]  # timestamp in epoch
    updated_at: Optional[int]  # timestamp in epoch


####################
# Forms
####################


class FileMeta(BaseModel):
    name: Optional[str] = None
    content_type: Optional[str] = None
    size: Optional[int] = None

    model_config = ConfigDict(extra="allow")


class FileModelResponse(BaseModel):
    id: str
    user_id: str
    hash: Optional[str] = None

    filename: str
    data: Optional[dict] = None
    meta: FileMeta

    created_at: int  # timestamp in epoch
    updated_at: int  # timestamp in epoch

    model_config = ConfigDict(extra="allow")


class FileMetadataResponse(BaseModel):
    id: str
    hash: Optional[str] = None
    meta: dict
    created_at: int  # timestamp in epoch
    updated_at: int  # timestamp in epoch


class FileForm(BaseModel):
    id: str
    hash: Optional[str] = None
    filename: str
    path: str
    data: dict = {}
    meta: dict = {}
    access_control: Optional[dict] = None


class FilesTable:
    async def insert_new_file(self, user_id: str, form_data: FileForm) -> Optional[FileModel]:
        with get_db() as db:
            file = FileModel(
                **{
                    **form_data.model_dump(),
                    "user_id": user_id,
                    "created_at": int(time.time()),
                    "updated_at": int(time.time()),
                }
            )

            try:
                result = File(**file.model_dump())
                await asyncio.to_thread(db.add, result)
                await asyncio.to_thread(db.commit)
                await asyncio.to_thread(db.refresh, result)
                if result:
                    return FileModel.model_validate(result)
                else:
                    return None
            except Exception as e:
                log.exception(f"Error inserting a new file: {e}")
                return None

    async def get_file_by_id(self, id: str) -> Optional[FileModel]:
        with get_db() as db:
            try:
                file = await asyncio.to_thread(db.get, File, id)
                return FileModel.model_validate(file)
            except Exception:
                return None

    async def get_file_by_id_and_user_id(self, id: str, user_id: str) -> Optional[FileModel]:
        with get_db() as db:
            try:
                file = await asyncio.to_thread(db.query(File).filter_by(id=id, user_id=user_id).first)
                if file:
                    return FileModel.model_validate(file)
                else:
                    return None
            except Exception:
                return None

    async def get_file_metadata_by_id(self, id: str) -> Optional[FileMetadataResponse]:
        with get_db() as db:
            try:
                file = await asyncio.to_thread(db.get, File, id)
                return FileMetadataResponse(
                    id=file.id,
                    hash=file.hash,
                    meta=file.meta,
                    created_at=file.created_at,
                    updated_at=file.updated_at,
                )
            except Exception:
                return None

    async def get_files(self) -> list[FileModel]:
        with get_db() as db:
            files = await asyncio.to_thread(db.query(File).all)
            return [FileModel.model_validate(file) for file in files]

    async def check_access_by_user_id(self, id, user_id, permission="write") -> bool:
        file = await self.get_file_by_id(id)
        if not file:
            return False
        if file.user_id == user_id:
            return True
        # Implement additional access control logic here as needed
        return False

    async def get_files_by_ids(self, ids: list[str]) -> list[FileModel]:
        with get_db() as db:
            files = await asyncio.to_thread(db.query(File).filter(File.id.in_(ids)).order_by(File.updated_at.desc()).all)
            return [FileModel.model_validate(file) for file in files]

    async def get_file_metadatas_by_ids(self, ids: list[str]) -> list[FileMetadataResponse]:
        with get_db() as db:
            files = await asyncio.to_thread(db.query(File.id, File.hash, File.meta, File.created_at, File.updated_at).filter(File.id.in_(ids)).order_by(File.updated_at.desc()).all)
            return [
                FileMetadataResponse(
                    id=file.id,
                    hash=file.hash,
                    meta=file.meta,
                    created_at=file.created_at,
                    updated_at=file.updated_at,
                )
                for file in files
            ]

    async def get_files_by_user_id(self, user_id: str) -> list[FileModel]:
        with get_db() as db:
            files = await asyncio.to_thread(db.query(File).filter_by(user_id=user_id).all)
            return [FileModel.model_validate(file) for file in files]

    async def update_file_hash_by_id(self, id: str, hash: str) -> Optional[FileModel]:
        with get_db() as db:
            try:
                file = await asyncio.to_thread(db.query(File).filter_by(id=id).first)
                file.hash = hash
                await asyncio.to_thread(db.commit)

                return FileModel.model_validate(file)
            except Exception:
                return None

    async def update_file_data_by_id(self, id: str, data: dict) -> Optional[FileModel]:
        with get_db() as db:
            try:
                file = await asyncio.to_thread(db.query(File).filter_by(id=id).first)
                file.data = {**(file.data if file.data else {}), **data}
                await asyncio.to_thread(db.commit)
                return FileModel.model_validate(file)
            except Exception:
                return None

    async def update_file_metadata_by_id(self, id: str, meta: dict) -> Optional[FileModel]:
        with get_db() as db:
            try:
                file = await asyncio.to_thread(db.query(File).filter_by(id=id).first)
                file.meta = {**(file.meta if file.meta else {}), **meta}
                await asyncio.to_thread(db.commit)
                return FileModel.model_validate(file)
            except Exception:
                return None

    async def delete_file_by_id(self, id: str) -> bool:
        with get_db() as db:
            try:
                await asyncio.to_thread(db.query(File).filter_by(id=id).delete)
                await asyncio.to_thread(db.commit)

                return True
            except Exception:
                return False

    async def delete_all_files(self) -> bool:
        with get_db() as db:
            try:
                await asyncio.to_thread(db.query(File).delete)
                await asyncio.to_thread(db.commit)

                return True
            except Exception:
                return False


Files = FilesTable()
