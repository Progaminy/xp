import subprocess
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

class MeuServidor(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Bateria
            bat = subprocess.run(['termux-battery-status'], capture_output=True, text=True)
            dados_bat = json.loads(bat.stdout)

            # Localização (GPS)
            loc = subprocess.run(['termux-location'], capture_output=True, text=True)
            dados_loc = json.loads(loc.stdout)

            html = f"""
            <!DOCTYPE html>
            <html>
            <head><meta charset='utf-8'><title>Painel Pessoal</title></head>
            <body>
                <h1>🖥️ Painel do Servidor</h1>
                <h2>🔋 Bateria</h2>
                <p>Porcentagem: {dados_bat['percentage']}%</p>
                <p>Status: {dados_bat['status']}</p>
                <p>Temperatura: {dados_bat['temperature']}°C</p>
                <h2>📍 Localização</h2>
                <p>Latitude: {dados_loc.get('latitude', 'N/D')}</p>
                <p>Longitude: {dados_loc.get('longitude', 'N/D')}</p>
            </body>
            </html>
            """
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode('utf-8'))

    def log_message(self, format, *args):
        return

servidor = HTTPServer(('', 8080), MeuServidor)
print('Servidor rodando em http://0.0.0.0:8080')
try:
    servidor.serve_forever()
except KeyboardInterrupt:
    print("\nServidor encerrado.")