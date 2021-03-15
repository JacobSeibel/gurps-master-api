from flask import Flask, request
import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

app = Flask(__name__)

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = os.getenv("DB_PORT")

try:
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, dbname=DB_NAME)
except:
    print("I am unable to connect to the database.")

cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

@app.route('/character')
@app.route('/character/<id>')
def character(id=None):
    if id:
        try:
            cur.execute("""select * from character where id=%s""", id)
        except:
            print("Can't select from character")

        row = cur.fetchall()[0]
        return row
    else:
        try:
            cur.execute("""select * from character""")
        except:
            print("Can't select from character")

        rows = cur.fetchall()
        print(rows)
        return {"characters": rows}
        

if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000)