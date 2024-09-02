from flask import Flask, render_template
import requests
import pymssql
import paramiko

app = Flask(__name__)

# Configura tu bucket y objeto aquí
bucket_name = 'webserverpe'
object_key = 'doc1.html'
s3_base_url = f'https://{bucket_name}.s3.us-east-1.amazonaws.com/{object_key}'

rds_endpoint = 'database-1.c4dyhdtxg4qb.us-east-1.rds.amazonaws.com'
rds_port = '1433'
rds_username = 'admin'
rds_password = 'Mauricio153.'
rds_database = 'databasepe'

ec2_username = 'ec2-user' 
ec2_host = 'ec2-52-87-243-50.compute-1.amazonaws.com' 
ssh_private_key_path = 'monitos.pem' 
docker_container_name = 'backend'

worker_endpoint = 'http://ip172-18-0-24-craf1eqim2rg00dvbji0-5000.direct.labs.play-with-docker.com/'
backend_endpoint = 'http://52.87.243.50:8000/api'
front_endpoint = 'http://ip172-18-0-21-craf1eqim2rg00dvbji0-7000.direct.labs.play-with-docker.com/index.php'

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

        # Obtener el uso de CPU (solo porcentaje)
        stdin, stdout, stderr = ssh.exec_command("top -bn1 | grep 'Cpu(s)' | awk '{print $2 + $4}'")
        cpu_usage = stdout.read().decode().strip()
        if cpu_usage:
            metrics['cpu'] = f"{cpu_usage}%"

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


def check_docker_container_metrics():
    container_metrics = {
        'cpu': 'Unavailable',
        'memory': 'Unavailable',
        'disk': 'Unavailable'
    }

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ec2_host, username=ec2_username, key_filename=ssh_private_key_path)

        # Verificar si el contenedor está en ejecución antes de obtener las métricas
        stdin, stdout, stderr = ssh.exec_command(f"docker ps --filter 'name={docker_container_name}' --format '{{{{.Names}}}}'")
        docker_status = stdout.read().decode().strip()
        if docker_container_name not in docker_status:
            container_metrics['cpu'] = 'Container not running'
            container_metrics['memory'] = 'Container not running'
            container_metrics['disk'] = 'Container not running'
        else:
            # Obtener el uso de CPU y memoria del contenedor
            stdin, stdout, stderr = ssh.exec_command(f"docker stats {docker_container_name} --no-stream --format '{{{{.CPUPerc}}}},{{{{.MemUsage}}}}'")
            stats_output = stdout.read().decode().strip()
            if stats_output:
                cpu_usage, memory_usage = stats_output.split(',')
                container_metrics['cpu'] = f'CPU Usage: {cpu_usage.strip()}'
                container_metrics['memory'] = f'Memory Usage: {memory_usage.strip()}'
            else:
                container_metrics['cpu'] = 'Failed to retrieve CPU usage'
                container_metrics['memory'] = 'Failed to retrieve memory usage'

            # Obtener el uso de almacenamiento del contenedor
            stdin, stdout, stderr = ssh.exec_command(f"docker ps -s --filter 'name={docker_container_name}' --format '{{{{.Size}}}}'")
            disk_output = stdout.read().decode().strip()
            if disk_output:
                container_metrics['disk'] = f'Storage Usage: {disk_output}'
            else:
                container_metrics['disk'] = 'Failed to retrieve disk usage'

        ssh.close()
    except Exception as e:
        container_metrics['error'] = f'Error fetching container metrics: {str(e)}'

    return container_metrics

def check_endpoint(url, service_name):
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return f'{service_name} Endpoint: Disponible'
        else:
            return f'{service_name} Endpoint: No Disponible'
    except requests.RequestException:
        return f'{service_name} Endpoint: No Disponible'


@app.route('/')
def index():
    s3_status = check_s3_status()
    rds_status = check_rds_status()
    ec2_metrics = check_ec2_metrics()
    docker_metrics = check_docker_container_metrics()
    worker_status = check_endpoint(worker_endpoint, "Worker (Modelo Python)")
    backend_status = check_endpoint(backend_endpoint, "API Dotnet")
    front_status = check_endpoint(front_endpoint, "Front PHP 😬")

    return render_template('index.html', 
                           s3_status=s3_status, 
                           rds_status=rds_status, 
                           ec2_metrics=ec2_metrics, 
                           docker_metrics=docker_metrics, 
                           worker_status=worker_status, 
                           backend_status=backend_status, 
                           front_status=front_status)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

