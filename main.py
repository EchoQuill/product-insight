import utils.amazon_fetcher as amazon_fetcher
import utils.log as log
import logging
import sys
import sqlite3
import json
import time
import random
from flask import Flask, jsonify, render_template, request


"""
url = "https://www.amazon.in/dp/B07JQFQK7S"
dict_data = basic.fetch_start_pg(url)
print(dict_data)
"""

config = None


"""FLASK APP"""

app = Flask(__name__)
website_logs = []
config_updated = None

with open("config.json", "r") as config_file:
    config = json.load(config_file)

def get_from_db(command):
    with sqlite3.connect("utils/data/db.sqlite") as conn:
        conn.row_factory = sqlite3.Row 
        cur = conn.cursor()

        cur.execute("PRAGMA journal_mode;")
        mode = cur.fetchone()[0]
        if mode.lower() != 'wal':
            cur.execute("PRAGMA journal_mode=WAL;")

        cur.execute(command)

        item = cur.fetchall()
        return item    



@app.route("/")
def home():
    return render_template("index.html")



def web_start():
    flaskLog = logging.getLogger("werkzeug")
    flaskLog.disabled = True
    cli = sys.modules["flask.cli"]
    cli.show_server_banner = lambda *x: None
    app.run(
        debug=True,
        use_reloader=False,
        port=config["website"]["port"],
        host="0.0.0.0" if config["website"]["hostMode"] else None
    )

def generate_really_random_and_top_secret_uuid():
    # Insane code right? ;>

    """
    Since we are going to be hosting this, we can't rely on time.time()
    as the time used in hosts `may` be changing or random and so on. can't predict it!

    I decided to use `time.monotonic()` but that is session sepecific only
    solution i could think of was to have a random key to ensure that the code knows incase of restarts
    which is common to happen with free hosts every now and then.
    """

    rand_key_1 = random.choice(["cat", "echo", "dawn", "dusk", "dim", "sch", "in"])
    rand_key_2 = random.choice(["dog", "quill", "morning", "night", "bright", "hcs", "ni"])
    rand_num = str(random.randint(100,1000000))
    const_phrase = "-Amzn-Scrapper-Proj"

    uuid = rand_key_1 + rand_key_2 + rand_num + const_phrase

    return uuid

# --------

"""Database Management"""

def update_database(db_path="utils/amazon_db.sqlite"):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    base_url = config["base_url"]

    for dp_code in config["urls_dp_code"]:
        url = base_url+dp_code
        result_dict = amazon_fetcher.fetch_start_pg(url)

        c.execute(
            """
            UPDATE amazon_fetches SET image_url = ?, image_alt = ?, rating = ?, price_cut = ?, price = ?, last_fetched = ?, uuid = ? 
            WHERE dp_key = ?
            """,
            (result_dict["image"]["url"], result_dict["image"]["alt"], result_dict["rating"], result_dict["pricecut"], result_dict["price"], time.monotonic(), UUID, dp_code)
        )

        # My eyes hurt looking at this lol
        c.execute(
            """
            UPDATE star_info
            SET total_rating = ?, 
                one = ?, two = ?, three = ?, four = ?, five = ?,
                one_percentage = ?, two_percentage = ?, three_percentage = ?, four_percentage = ?, five_percentage = ?
            WHERE dp_key = ?
            """,
            (
                result_dict["stars"]["total_rating"],
                result_dict["stars"]["1"]["stars"],
                result_dict["stars"]["2"]["stars"],
                result_dict["stars"]["3"]["stars"],
                result_dict["stars"]["4"]["stars"],
                result_dict["stars"]["5"]["stars"],
                result_dict["stars"]["1"]["percentage"],
                result_dict["stars"]["2"]["percentage"],
                result_dict["stars"]["3"]["percentage"],
                result_dict["stars"]["4"]["percentage"],
                result_dict["stars"]["5"]["percentage"],
                dp_code
            )
        )

        for item in result_dict["reviews"]:
            c.execute(
                """
                INSERT OR IGNORE INTO reviews
                (dp_key, user, text)
                VALUES
                (?, ?, ?)
                """,
                (dp_code, item["user"], item["text"])
            )
            
    conn.commit()
    conn.close()
    log.customPrint(f"Database have been updated with latest fetched data!", "soft_purple")

def populate_database(db_path="utils/amazon_db.sqlite"):
    log.customPrint("Populating database...", "plum")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    for dp_code in config["urls_dp_code"]:
        c.execute("INSERT OR IGNORE INTO amazon_fetches (dp_key, image_url, image_alt, rating, price_cut, price, last_fetched, uuid) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (dp_code, None, None, 0, None, None, None, None))
        c.execute("INSERT OR IGNORE INTO star_info (dp_key, one, two, three, four, five) VALUES (?, ?, ?, ?, ?, ?)", (dp_code, 0, 0, 0, 0, 0))

    conn.commit()
    conn.close()
    log.customPrint(f"Populated database! - {db_path}", "lilac")
        


def create_database(db_path="utils/amazon_db.sqlite"):
    log.customPrint("Creating database...", "plum")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    """Amazon basic data fetches"""
    c.execute("""
        CREATE TABLE IF NOT EXISTS amazon_fetches (
            dp_key TEXT PRIMARY KEY,
            image_url TEXT,
            image_alt TEXT,
            rating REAL,
            price_cut TEXT,
            price REAL,
            last_fetched REAL,
            uuid TEXT
        )
    """)

    """Amazon review fetches"""
    c.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dp_key TEXT,
            user TEXT,
            text TEXT,
            UNIQUE(dp_key, user, text),
            FOREIGN KEY(dp_key) REFERENCES amazon_fetches(dp_key)
        )
    """)

    """Amazon stars fetches"""
    # If needed, we will calculate percentage seperately!
    c.execute("""
        CREATE TABLE IF NOT EXISTS star_info (
            dp_key TEXT PRIMARY KEY,
            total_rating INTEGER,
            one INTEGER,
            two INTEGER,
            three INTEGER,
            four INTEGER,
            five INTEGER,
            one_percentage REAL,
            two_percentage REAL,
            three_percentage REAL,
            four_percentage REAL,
            five_percentage REAL
        )
    """)

    # Note: `FOREIGN KEY(dp_key) REFERENCES amazon_fetches(dp_key)` Ensures
    # dp_key is one that is used in amazon_fetches
    # Not that it matters, just being safe!

    # Switch to WAL mode
    c.execute("PRAGMA journal_mode=WAL;")

    conn.commit()
    conn.close()

    log.customPrint(f"Ensured database is created! - {db_path}", "lilac")

# ---------------

if __name__ == "__main__":
    UUID = generate_really_random_and_top_secret_uuid()

    # Create a database
    create_database()
    populate_database()
    update_database()
    # start site
    web_start()


    #print(amazon_fetcher.fetch_start_pg("https://www.amazon.in/dp/9386473429"))
    
