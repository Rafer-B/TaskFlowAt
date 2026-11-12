"""Script simples para testar e apresentar a ligação PostgreSQL configurada."""

from app.database import testar_ligacao

__test__ = False

try:
    # Mantém o diagnóstico utilizável na linha de comandos sem traceback longo.
    resultado = testar_ligacao()
    print("Ligação ao PostgreSQL estabelecida!")
    print("Base de dados:", resultado[0])
    print("Versão:", resultado[1])
except Exception as erro:
    print("Não foi possível ligar ao PostgreSQL.")
    print(type(erro).__name__, erro)