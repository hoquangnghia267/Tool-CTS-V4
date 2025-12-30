import configparser
import time
import mysql.connector  


def get_database_config(section_name, config_file="database_config.ini"):
    config = configparser.ConfigParser()
    config.read(config_file)
    return config[section_name]

def connect_to_database(config, max_retries=3, retry_delay=5):
    retries = 0
    conn = None
    host = config["host"]
    user = config["user"]
    password = config["password"]
    database = config["database"]

    while retries < max_retries:
        try:
            conn = mysql.connector.connect(host=host, user=user, password=password, database=database)
            if conn.is_connected():
                print("Connected to the database!")
                return conn
        except mysql.connector.Error as e:
            print(f"Failed to connect to the database: {e}")
            retries += 1
            time.sleep(retry_delay)

    print(f"Unable to connect to the database after {max_retries} retries.")
    return None
