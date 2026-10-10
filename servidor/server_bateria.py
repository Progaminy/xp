"""Compatibilidade: evita servir dados da bateria sem autenticação."""
try:
    from .admin import main
except ImportError:
    from admin import main

if __name__ == "__main__":
    main()
