from sqlalchemy import Table, Column, Integer, String, MetaData

metadata = MetaData()

users = Table(
    "users",  # 👈 must be plural, matches queries
    metadata,
    Column("id", Integer, primary_key=True),
    Column("email", String, unique=True, nullable=False, index=True),
    Column("firstname", String, nullable=True),
    Column("user_images", String, nullable=True),
    Column("graphical_password", String, nullable=True),
    Column("status", String, nullable=True),
)
