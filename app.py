from flask import Flask, render_template
import requests
import pymssql
import paramiko

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

ec2_username = 'ec2-user' 
ec2_host = '52.87.243.50' 
ssh_private_key_path = '.monitos.pem' 
docker_container_name = 'backend'

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
def check_ec2_metrics():
    metrics = {
        'cpu': 'Unavailable',
        'ram': 'Unavailable',
        'disk': 'Unavailable',
        'docker': 'Unavailable'
    }

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ec2_host, username=ec2_username, key_filename=ssh_private_key_path)

        # Obtener el uso de CPU
        stdin, stdout, stderr = ssh.exec_command("top -bn1 | grep 'Cpu(s)'")
        cpu_usage = stdout.read().decode().strip()
        if cpu_usage:
            metrics['cpu'] = cpu_usage

        # Obtener el uso de RAM
        stdin, stdout, stderr = ssh.exec_command("free -m | awk 'NR==2{printf \"Memory Usage: %s/%sMB (%.2f%%)\", $3,$2,$3*100/$2 }'")
        ram_usage = stdout.read().decode().strip()
        if ram_usage:
            metrics['ram'] = ram_usage

        # Obtener el uso de disco
        stdin, stdout, stderr = ssh.exec_command("df -h --total | grep 'total'")
        disk_usage = stdout.read().decode().strip()
        if disk_usage:
            metrics['disk'] = disk_usage

        # Verificar el estado del contenedor Docker
        stdin, stdout, stderr = ssh.exec_command(f"docker ps --filter 'name={docker_container_name}' --format '{{{{.Names}}}}'")
        docker_status = stdout.read().decode().strip()
        if docker_container_name in docker_status:
            metrics['docker'] = 'Docker container is running.'
        else:
            metrics['docker'] = 'Docker container is not running.'

        ssh.close()
    except Exception as e:
        metrics['error'] = f'Error connecting to EC2: {str(e)}'

    return metrics

@app.route('/')
def index():
    s3_status = check_s3_status()
    rds_status = check_rds_status()
    ec2_metrics = check_ec2_metrics()

    return render_template('index.html', s3_status=s3_status, rds_status=rds_status, ec2_metrics=ec2_metrics)
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
i
