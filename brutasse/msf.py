#!/usr/bin/env python3

from pathlib import Path
from types import TracebackType
from typing import Any, Optional, Self, Type, TypeVar

import yaml
from sqlalchemy import URL, ForeignKey, ScalarResult, create_engine, select
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    joinedload,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    pass


T = TypeVar("T", bound=Base)


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()

    hosts: Mapped[list["Host"]] = relationship(back_populates="workspace")


class Host(Base):
    __tablename__ = "hosts"

    id: Mapped[int] = mapped_column(primary_key=True)
    address: Mapped[str] = mapped_column(INET)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id"))

    workspace: Mapped["Workspace"] = relationship(back_populates="hosts")
    services: Mapped[list["Service"]] = relationship(back_populates="host")


class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True)
    host_id: Mapped[int] = mapped_column(ForeignKey("hosts.id"))
    name: Mapped[str] = mapped_column()
    proto: Mapped[str] = mapped_column()
    port: Mapped[int] = mapped_column()
    state: Mapped[str] = mapped_column()

    host: Mapped["Host"] = relationship(back_populates="services")
    notes: Mapped[list["Note"]] = relationship(back_populates="service")


class Note(Base):
    __tablename__ = "notes"
    id: Mapped[int] = mapped_column(primary_key=True)
    ntype: Mapped[str] = mapped_column()
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"))
    data: Mapped[str] = mapped_column()

    service: Mapped["Service"] = relationship(back_populates="notes")


class Metasploit:
    def __init__(self, workspace_name: str = "default"):
        url = self.get_db_url()

        self.engine = create_engine(url)
        self.workspace_name = workspace_name

    def __enter__(self) -> Self:
        self.session = Session(self.engine)
        workspace = (
            self.session.query(Workspace).filter_by(name=self.workspace_name).first()
        )
        assert workspace
        self.workspace_id = workspace.id
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        self.session.close()

    def commit(self) -> None:
        self.session.commit()

    def get_db_url(self) -> URL:
        lookup_paths = [
            Path.home() / ".msf4/database.yml",
            Path.home() / "snap/metasploit-framework/common/.msf4/database.yml",
        ]

        for path in lookup_paths:
            if path.is_file():
                break
        else:
            raise FileNotFoundError("database.yml not found")

        with path.open("rb") as fd:
            config = yaml.safe_load(fd)
            prod = config["production"]

        return URL.create(
            prod["adapter"],
            username=prod["username"],
            password=prod["password"],
            host=prod["host"],
            port=prod["port"],
            database=prod["database"],
        )

    def get_or_create(self, model: Type[T], **kwargs: Any) -> T:
        instance = self.session.query(model).filter_by(**kwargs).first()
        if not instance:
            instance = model(**kwargs)
            self.session.add(instance)
        return instance

    def get_or_create_host(self, address: str) -> Host:
        return self.get_or_create(Host, address=address, workspace_id=self.workspace_id)

    def get_or_create_service(self, host: Host, proto: str, port: int) -> Service:
        # Note: do we care about hosts.service_count ?
        return self.get_or_create(Service, host=host, proto=proto, port=port)

    def get_services_by_port(self, proto: str, port: int) -> ScalarResult[Service]:
        stmt = (
            select(Service)
            .where(Service.proto == proto)
            .where(Service.port == port)
            .options(joinedload(Service.host))
        )
        return self.session.execute(stmt).scalars()

    def get_or_create_note(self, service: Service, ntype: str) -> Note:
        return self.get_or_create(Note, service=service, ntype=ntype)
