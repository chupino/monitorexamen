from flask import Flask, render_template
import requests
import pymssql

app = Flask(__name__)

# Configura tu bucket y objeto aquí
bucket_name = 'webserverpe'
object_key = 'doc1.html'
s3_base_url = f'https://{bucket_name}.s3.us-east-1.amazonaws.com/{object_key}'

rds_endpoint = 'database-minihub.c4dyhdtxg4qb.us-east-1.rds.amazonaws.com'
rds_port = '1433'
rds_username = 'admin'
rds_password = 'Mauricio153.'
rds_database = 'databasepe'

def check_s3_status():
    try:
        response = requests.head(s3_base_url)
        if response.status_code == 200:
            return 'accessible'
        else:
            return 'File not found or inaccessible.'
    except requests.RequestException as e:
        return f'Error: {str(e)}'

def check_rds_status():
    try:
        conn = pymssql.connect(server=rds_endpoint, user=rds_username, password=rds_password, database=rds_database, timeout=5)
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        result = cursor.fetchone()
        conn.close()
        if result:
            return 'Database is accessible.'
        else:
            return 'Error: Unable to query database.'
    except pymssql.DatabaseError as e:
        return f'Error: {str(e)}'

@app.route('/')
def index():
    s3_status = check_s3_status()
    rds_status = check_rds_status()
    
    return render_template('index.html', s3_status=s3_status, rds_status=rds_status)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
i
