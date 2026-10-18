from __future__ import annotations

from decimal import Decimal
from typing import Literal

from sqlalchemy import Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.session import Base


class Hurtownia(Base):
    __tablename__ = "hurtownia"

    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
    }

    hurtownia_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    nazwa: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    link: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    produkty: Mapped[list[Produkt]] = relationship(
        back_populates="hurtownia",
        passive_deletes="all",
    )

    linki: Mapped[list[ProductLink]] = relationship(
        back_populates="hurtownia",
        passive_deletes="all",
    )


class ProductLink(Base):
    __tablename__ = "productlinks"

    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
    }

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    hurtownia_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "hurtownia.hurtownia_id",
            name="fk_productlinks_hurtownia",
        ),
        nullable=False,
    )

    link: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    hurtownia: Mapped[Hurtownia] = relationship(
        back_populates="linki",
    )


class Produkt(Base):
    __tablename__ = "produkt"

    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
    }

    produkt_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    hurtownia_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "hurtownia.hurtownia_id",
            name="fk_produkt_hurtownia",
        ),
        nullable=False,
    )

    kod: Mapped[str] = mapped_column(
        String(13),
        nullable=False,
    )

    brutto: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    netto: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    jednostka: Mapped[Literal["kg", "szt"]] = mapped_column(
        Enum(
            "kg",
            "szt",
            native_enum=True,
            validate_strings=True,
        ),
        nullable=False,
    )

    hurtownia: Mapped[Hurtownia] = relationship(
        back_populates="produkty",
    )