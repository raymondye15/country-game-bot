# -*- coding: utf-8 -*-
"""MongoDB (Atlas free M0) data layer via motor."""
import os
from motor.motor_asyncio import AsyncIOMotorClient

_client = None
db = None

def init_db():
    global _client, db
    uri = os.environ["MONGODB_URI"]
    _client = AsyncIOMotorClient(uri)
    db = _client[os.environ.get("MONGODB_DB", "country_game")]
    return db

async def ensure_indexes():
    await db.countries.create_index("user_id", unique=True)
    await db.countries.create_index("name_lower", unique=True, sparse=True)
    await db.countries.create_index([("planet", 1), ("continent", 1)])
    await db.trade_offers.create_index("seller_id")
    await db.wars.create_index([("attacker_id", 1), ("defender_id", 1)])
    await db.groups.create_index("chat_id", unique=True)
    await db.requests.create_index([("to_id", 1), ("kind", 1)])

# ---- countries ----
async def get_country(user_id: int):
    return await db.countries.find_one({"user_id": user_id})

async def get_country_by_name(name: str):
    return await db.countries.find_one({"name_lower": name.strip().lower()})

async def save_country(country: dict):
    await db.countries.replace_one({"user_id": country["user_id"]}, country, upsert=True)

async def delete_country(user_id: int):
    await db.countries.delete_one({"user_id": user_id})
    await db.trade_offers.delete_many({"seller_id": user_id})
    await db.requests.delete_many({"$or": [{"from_id": user_id}, {"to_id": user_id}]})

async def planet_country_count(planet: str) -> int:
    return await db.countries.count_documents({"planet": planet, "alive": True})

async def continent_countries(planet: str, continent: str, exclude_user: int):
    cur = db.countries.find({"planet": planet, "continent": continent, "alive": True, "user_id": {"$ne": exclude_user}})
    return [c async for c in cur]

async def all_alive_countries():
    cur = db.countries.find({"alive": True})
    return [c async for c in cur]

async def top_countries(field: str, limit: int = 10):
    cur = db.countries.find({"alive": True}).sort(field, -1).limit(limit)
    return [c async for c in cur]

# ---- groups (>=3 distinct humans rule) ----
async def register_group_human(chat_id: int, user_id: int) -> int:
    await db.groups.update_one({"chat_id": chat_id}, {"$addToSet": {"humans": user_id}}, upsert=True)
    g = await db.groups.find_one({"chat_id": chat_id})
    return len(g.get("humans", []))

async def group_human_count(chat_id: int) -> int:
    g = await db.groups.find_one({"chat_id": chat_id})
    return len(g.get("humans", [])) if g else 0

# ---- requests (neighbor / alliance / nap) ----
async def create_request(kind: str, from_id: int, to_id: int):
    await db.requests.delete_many({"kind": kind, "from_id": from_id, "to_id": to_id})
    await db.requests.insert_one({"kind": kind, "from_id": from_id, "to_id": to_id})

async def pop_request(kind: str, from_id: int, to_id: int):
    r = await db.requests.find_one_and_delete({"kind": kind, "from_id": from_id, "to_id": to_id})
    return r is not None
