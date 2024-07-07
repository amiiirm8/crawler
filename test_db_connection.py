import psycopg2
import logging
import sys
import os

# Add the parent directory of 'scripts' to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import load_config  # Now it should find utils

# Load configuration
config = load_config('../config/config.json')  # Adjusted path

# Setup logging with a default filename if 'log_filename' is not present
log_filename = config.get('log_filename', 'crawler.log')
logging.basicConfig(filename=log_filename, level=logging.INFO)
logger = logging.getLogger()

# Database connection function
def connect_db():
    try:
        conn = psycopg2.connect(
            host=config['db_config']['host'],
            database=config['db_config']['database'],
            user=config['db_config']['user'],
            password=config['db_config']['password'],
            port=config['db_config']['port']
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

# Test database connection and table creation
def test_db():
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS test_table (id SERIAL PRIMARY KEY, name TEXT);")
            conn.commit()
            cursor.close()
            logger.info("Database connection and table creation successful.")
            print("Database connection and table creation successful.")
        except Exception as e:
            logger.error(f"Error creating table: {e}")
            print(f"Error creating table: {e}")
        finally:
            conn.close()
    else:
        logger.error("Failed to connect to the database.")
        print("Failed to connect to the database.")

if __name__ == "__main__":
    test_db()
