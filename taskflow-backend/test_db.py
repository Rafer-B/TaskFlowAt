from app.database import testar_ligacao

try:
    resultado = testar_ligacao()
    print("Ligação ao PostgreSQL estabelecida!")
    print("Base de dados:", resultado[0])
    print("Versão:", resultado[1])
except Exception as erro:
    print("Não foi possível ligar ao PostgreSQL.")
    print(type(erro).__name__, erro)