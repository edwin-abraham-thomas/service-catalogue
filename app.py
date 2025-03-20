#!/usr/bin/env python3
import kubernetes
from kubernetes import client, config
import os
from flask import Flask, render_template_string, jsonify

app = Flask(__name__)

# HTML template for the web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Kubernetes Service Catalog</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            color: #333;
        }
        h1 {
            color: #2c3e50;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 10px;
        }
        .service-list {
            list-style-type: none;
            padding: 0;
        }
        .service-item {
            background-color: #f9f9f9;
            border-left: 4px solid #3498db;
            margin-bottom: 10px;
            padding: 15px;
            border-radius: 0 4px 4px 0;
        }
        .service-name {
            color: #2980b9;
            font-weight: bold;
        }
        .service-namespace {
            color: #7f8c8d;
            font-size: 0.9em;
        }
        .service-url {
            display: block;
            margin-top: 5px;
            color: #27ae60;
            text-decoration: none;
            font-family: monospace;
            font-size: 1.1em;
        }
        .service-url:hover {
            text-decoration: underline;
        }
        .port-number {
            background-color: #eaf2f8;
            border-radius: 3px;
            padding: 2px 5px;
            margin-left: 5px;
            font-size: 0.85em;
            color: #2471a3;
        }
        .refresh-btn {
            background-color: #3498db;
            color: white;
            border: none;
            padding: 10px 15px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 1em;
        }
        .refresh-btn:hover {
            background-color: #2980b9;
        }
        .no-services {
            color: #e74c3c;
            font-style: italic;
        }
    </style>
</head>
<body>
    <h1>Kubernetes Service Catalog</h1>
    
    <button class="refresh-btn" onclick="window.location.reload()">Refresh</button>
    
    {% if services %}
    <ul class="service-list">
        {% for service in services %}
        <li class="service-item">
            <span class="service-name">{{ service.name }}</span>
            <span class="service-namespace">({{ service.namespace }})</span>
            <span class="port-number">Port: {{ service.port }}</span>
            <a href="{{ service.url }}" target="_blank" class="service-url">{{ service.url }}</a>
        </li>
        {% endfor %}
    </ul>
    {% else %}
    <p class="no-services">No LoadBalancer services found.</p>
    {% endif %}
</body>
</html>
"""

def get_loadbalancer_services():
    """Get all LoadBalancer services in the cluster and format their URLs."""
    # Try to load in-cluster config first, fall back to kubeconfig if needed
    try:
        config.load_incluster_config()
    except kubernetes.config.config_exception.ConfigException:
        config.load_kube_config()
    
    v1 = client.CoreV1Api()
    services = v1.list_service_for_all_namespaces()
    
    loadbalancer_services = []
    for svc in services.items:
        if svc.spec.type == "LoadBalancer":
            for port in svc.spec.ports:
                service_data = {
                    'name': svc.metadata.name,
                    'namespace': svc.metadata.namespace,
                    'port': port.port,
                    'url': f"http://localserver.local:{port.port}"
                }
                loadbalancer_services.append(service_data)
    
    # Sort services by port number in descending order
    loadbalancer_services.sort(key=lambda x: x['port'], reverse=True)
    
    return loadbalancer_services

@app.route('/')
def index():
    """Render the web interface."""
    services = get_loadbalancer_services()
    return render_template_string(HTML_TEMPLATE, services=services)

@app.route('/api/services')
def api_services():
    """Return service data as JSON for API access."""
    services = get_loadbalancer_services()
    return jsonify(services)

if __name__ == '__main__':
    # Get port from environment variable or use 8080 as default
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)