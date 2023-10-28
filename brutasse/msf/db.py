#!/usr/bin/env python3

import yaml
from pathlib import Path
from sqlalchemy import create_engine, URL, ForeignKey, select, ScalarResult
from sqlalchemy.orm import Session, DeclarativeBase, Mapped, relationship, mapped_column
from sqlalchemy.dialects.postgresql import INET
from typing import Type, TypeVar, Any


class Base(DeclarativeBase):
    pass


T = TypeVar('T', bound=Base)


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()

    hosts: Mapped[list["Host"]] = relationship(back_populates="workspace")


class Host(Base):
    __tablename__ = "hosts"

    id: Mapped[int] = mapped_column(primary_key=True)
    address: Mapped[str] = mapped_column(INET)
    workspace_id: Mapped[int] = mapped_column(ForeignKey('workspaces.id'))

    workspace: Mapped["Workspace"] = relationship(back_populates="hosts")
    services: Mapped[list["Service"]] = relationship(back_populates="host")


class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True)
    host_id: Mapped[int] = mapped_column(ForeignKey('hosts.id'))
    name: Mapped[str] = mapped_column()
    proto: Mapped[str] = mapped_column()
    port: Mapped[int] = mapped_column()
    state: Mapped[str] = mapped_column()

    host: Mapped["Host"] = relationship(back_populates="services")


class Metasploit:
    def __init__(self, workspace_name: str = 'default'):
        url = self.get_db_url()

        self.engine = create_engine(url)

        with self.session() as session:
            workspace = session.query(Workspace).filter_by(
                name=workspace_name).first()
            assert workspace
            self.workspace_id = workspace.id

    def session(self) -> Session:
        return Session(self.engine)

    def get_db_url(self) -> URL:
        lookup_paths = [
            Path.home() / '.msf4/database.yml',
            Path.home() / 'snap/metasploit-framework/common/.msf4/database.yml',
        ]

        for path in lookup_paths:
            if path.is_file():
                break
        else:
            raise FileNotFoundError('database.yml not found')

        with path.open('rb') as fd:
            config = yaml.safe_load(fd)
            prod = config['production']

        return URL.create(
            prod['adapter'],
            username=prod['username'],
            password=prod['password'],
            host=prod['host'],
            port=prod['port'],
            database=prod['database'],
        )

    def get_or_create(self, session: Session, model: Type[T], **kwargs: Any) -> T:
        instance = session.query(model).filter_by(**kwargs).first()
        if not instance:
            instance = model(**kwargs)
            session.add(instance)
        return instance

    def get_or_create_host(self, session: Session, address: str) -> Host:
        return self.get_or_create(session, Host, address=address, workspace_id=self.workspace_id)

    def get_or_create_service(self, session: Session, host: Host, proto: str, port: int) -> Service:
        # Note: do we care about hosts.service_count ?
        return self.get_or_create(session, Service, host=host, proto=proto, port=port)

    def get_services_by_port(self, session: Session, proto: str, port: int) -> ScalarResult[Service]:
        stmt = (
            select(Service)
            .where(Service.proto == proto)
            .where(Service.port == port)
        )
        return session.execute(stmt).scalars()
