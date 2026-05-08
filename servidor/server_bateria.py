import subprocess
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

class MeuServidor(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            resultado = subprocess.run(['termux-battery-status'], capture_output=True, text=True)
            dados = json.loads(resultado.stdout)

            html = f"""
            <!DOCTYPE html>
            <html>
            <head><meta charset='utf-8'><title>Painel Pessoal</title></head>
            <body>
                <h1>Painel do Servidor</h1>
                <h2>Bateria</h2>
                <p>Porcentagem: {dados['percentage']}%</p>
                <p>Status: {dados['status']}</p>
                <p>Temperatura: {dados['temperature']}°C</p>
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

if __name__ == '__main__':
    servidor = HTTPServer(('127.0.0.1', 8080), MeuServidor)
    print('Servidor rodando em http://127.0.0.1:8080')
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print('\nServidor encerrado.')
