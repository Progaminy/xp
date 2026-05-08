import subprocess
import json

print("Solicitando permissoes...")
print("-" * 40)

permissoes = [
    {
        "nome": "SMS",
        "comando": ['termux-sms-send', '-n', '+258872599084', 'Teste de permissao']
    },
    {
        "nome": "Localizacao (GPS)",
        "comando": ['termux-location']
    },
    {
        "nome": "Bateria",
        "comando": ['termux-battery-status']
    },
    {
        "nome": "Camera",
        "comando": ['termux-camera-photo', '/dev/null']
    },
    {
        "nome": "Armazenamento",
        "comando": ['termux-setup-storage']
    }
]

for p in permissoes:
    print(f"Pedindo permissao: {p['nome']}...")
    try:
        resultado = subprocess.run(p['comando'], capture_output=True, text=True, timeout=10)
        if resultado.returncode == 0:
            print(f"  {p['nome']}: OK")
        else:
            print(f"  {p['nome']}: ERRO - {resultado.stderr}")
    except subprocess.TimeoutExpired:
        print(f"  {p['nome']}: Aguardando (verifique o pop-up no celular)")
    except Exception as e:
        print(f"  {p['nome']}: FALHA - {e}")
    print()

print("Verificacao de permissoes concluida.")
print("Verifique os pop-ups no seu celular e conceda as permissoes.")
