from email.mime.text import MIMEText
import json
import smtplib
import logging
import psycopg2

def load_config(config_path):
    with open(config_path, 'r') as file:
        config = json.load(file)
    return config

def send_notification(subject, body, to_email):
    config = load_config('../config/config.json')
    email_config = config.get('email_notifications', {})
    if not email_config.get('enabled', False):
        return

    smtp_server = email_config['smtp_server']
    smtp_port = email_config['smtp_port']
    email_from = email_config['email_from']
    email_password = email_config.get('email_password')  # Store this securely

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = email_from
    msg['To'] = to_email

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(email_from, email_password)
        server.sendmail(email_from, [to_email], msg.as_string())

def create_logger(log_filename):
    logging.basicConfig(filename=log_filename, level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')
    return logging.getLogger()

def save_to_db(data, config):
    conn = None
    try:
        conn = psycopg2.connect(
            host=config['db_config']['host'],
            database=config['db_config']['database'],
            user=config['db_config']['user'],
            password=config['db_config']['password'],
            port=config['db_config']['port']
        )
        cursor = conn.cursor()
        for row in data:
            cursor.execute(
                """
                INSERT INTO scraped_data (title, download_link, size, creation_date)
                VALUES (%s, %s, %s, %s)
                """,
                (row[0], row[1], row[2], row[3])
            )
        conn.commit()
        cursor.close()
    except Exception as e:
        logging.error(f"Error saving data to the database: {e}")
    finally:
        if conn:
            conn.close()
