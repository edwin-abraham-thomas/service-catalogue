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
    <title>Kubernetes LoadBalancer Services</title>
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
    <h1>Kubernetes LoadBalancer Services</h1>
    
    <button class="refresh-btn" onclick="window.location.reload()">Refresh</button>
    
    {% if services %}
    <ul class="service-list">
        {% for service in services %}
        <li class="service-item">
            <span class="service-name">{{ service.name }}</span>
            <span class="service-namespace">({{ service.namespace }})</span>
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
                    'url': f"http://localserver.local:{port.port}"
                }
                loadbalancer_services.append(service_data)
    
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