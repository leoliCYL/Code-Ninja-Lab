from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.getenv('VITE_MONGO_URI'))
db = client.test

db.currentusers.update_one(
    {"pin": "4115"},
    {"$set": {
        "pin": "4115",
        "username": "Player",
        "gameId": "https://jscneg.github.io/SBYATG/"
    }},
    upsert=True
)

print("PIN 4115 seeded successfully.")
