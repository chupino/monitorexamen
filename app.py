from flask import Flask, render_template
import requests

app = Flask(__name__)

# Configura tu bucket y objeto aquí
bucket_name = 'webserverpe'
object_key = 'doc1.html'
s3_base_url = f'https://{bucket_name}.s3.us-east-1.amazonaws.com/{object_key}'

@app.route('/')
def index():
    try:
        response = requests.head(s3_base_url)
        if response.status_code == 200:
            status = 'accessible'
        else:
            status = 'File not found or inaccessible.'
    except requests.RequestException as e:
        status = f'Error: {str(e)}'
    
    return render_template('index.html', status=status)
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
i
