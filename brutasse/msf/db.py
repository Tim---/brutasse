#!/usr/bin/env python3

import yaml
from pathlib import Path
from sqlalchemy import create_engine, URL, ForeignKey
from sqlalchemy.orm import Session, DeclarativeBase, Mapped, relationship, mapped_column
from sqlalchemy.dialects.postgresql import INET


class Base(DeclarativeBase):
    pass


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


msfdb = Metasploit()
