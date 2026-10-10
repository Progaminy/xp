"""Compatibilidade: o servidor antigo agora inicia o painel autenticado."""
try:
    from .admin import main
except ImportError:
    from admin import main

if __name__ == "__main__":
    main()
