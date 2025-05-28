from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.sql import text
from database import get_db
from sqlalchemy.orm import Session
from consultas import consulta_get
from fastapi.middleware.cors import CORSMiddleware
from models import PostCliente, Cliente, PostPedido
import bcrypt


# from starlette.middleware.base import BaseHTTPMiddleware

app = FastAPI()

origins = [
    "http://localhost:4200",
    "http://localhost:8000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# class CookieMiddleware(BaseHTTPMiddleware):
#     async def dispatch(self, request: Request, call_next):
#             token = request.cookies.get('BBSSOToken')
#             if token:
#                 response = await call_next(request)
#             else:
#                 response = Response(content="Unauthorized", status_code=401)
#             return response

# app.add_middleware(CookieMiddleware)

@app.get('/user')
def user_logged(id: int, session: Session = Depends(get_db)):
    query = f"""
        SELECT id_cliente, nome, cpf, telefone, email, endereco, data_nascimento, data_cadastro FROM pizzaria.cliente WHERE id_cliente = {id}
    """
    return consulta_get(query, session)

@app.post('/cadastro')
def login(cliente: PostCliente, session: Session = Depends(get_db)):
    
    query = f"""
    SELECT 1 FROM pizzaria.cliente WHERE cpf = '{cliente.cpf}' OR email = '{cliente.email}'
    """
    
    if consulta_get(query, session):
        return {"message": "CPF ou email já cadastrado!"}

    
    hashed = bcrypt.hashpw(cliente.senha.encode('utf-8'), bcrypt.gensalt())
    hashed_senha = hashed.decode('utf-8')
    
    query = """
    INSERT INTO pizzaria.cliente (nome, cpf, telefone, email, endereco, data_cadastro, data_nascimento, senha) 
    VALUES (:post_nome, :post_cpf, :post_telefone, :post_email, :post_endereco, CURRENT_TIMESTAMP, :post_data_nascimento, :post_senha)
    """
    
    params = {
        'post_nome': cliente.nome,
        'post_cpf': cliente.cpf,
        'post_telefone': cliente.telefone,
        'post_email': cliente.email,
        'post_endereco': cliente.endereco,
        'post_data_nascimento': cliente.data_nascimento,
        'post_senha': hashed_senha
    }
    
    session.execute(text(query), params)
    session.commit()
    
    return {"message": "Cliente cadastrado com sucesso!"}


@app.post('/login')
def login_usuario(login: Cliente, session: Session = Depends(get_db)):
    query = "SELECT id_cliente, senha FROM pizzaria.cliente WHERE email = :email"
    result = session.execute(text(query), {"email": login.email}).fetchone()
    if result and bcrypt.checkpw(login.senha.encode('utf-8'), result[1].encode('utf-8')):
        return {"message": "Login realizado com sucesso!", "id_cliente": result[0]}
    else:
        raise HTTPException(status_code=401, detail="E-mail ou senha inválidos!")
    
@app.get('/restaurante')
def get_restaurante(session: Session = Depends(get_db)):
    query = """
        SELECT nome, endereco, telefone, email FROM pizzaria.restaurante
    """
    return consulta_get(query, session)

@app.get('/cardapio')
def get_cardapio(session: Session = Depends(get_db)):
    query = """
        SELECT id_produto, sabor, descricao, preco, foto FROM pizzaria.catalogo
    """
    return consulta_get(query, session)

@app.post('/fazer_pedido')
def fazer_pedido(id_cliente, session: Session = Depends(get_db)):
    # Verificar se o cliente já realizou um pedido
    query_check = """
        SELECT 1 FROM pizzaria.pedido WHERE id_cliente = :id_cliente
    """
    pedido_existente = session.execute(text(query_check), {'id_cliente': id_cliente}).fetchone()
    if pedido_existente:
        raise HTTPException(status_code=400, detail="Cliente já realizou um pedido.")

    # Buscar um funcionário disponível aleatório
    query_func = """
        SELECT id_funcionario FROM pizzaria.funcionario
        WHERE disponibilidade = 1
        ORDER BY RAND()
        LIMIT 1
    """
    func_result = session.execute(text(query_func)).fetchone()
    if not func_result:
        raise HTTPException(status_code=400, detail="Nenhum funcionário disponível no momento.")

    id_funcionario = func_result[0]

    query_func = """
    UPDATE pizzaria.funcionario sET disponibilidade = 0
    WHERE id_funcionario = :id_funcionario
    """
    session.execute(text(query_func), {'id_funcionario': id_funcionario})
    session.commit()
    
    query = """
        INSERT INTO pizzaria.pedido (id_cliente, id_restaurante, id_funcionario, data_pedido) 
        VALUES (:id_cliente, 1, :id_funcionario, CURRENT_TIMESTAMP)
    """
    params = {
        'id_cliente': id_cliente,
        'id_funcionario': id_funcionario,
    }
    
    session.execute(text(query), params)
    session.commit()
    
    return {"message": "Pedido realizado com sucesso!"}

@app.post('/adicionar_item')
def adicionar_item_pedido(post_pedido: PostPedido, session: Session = Depends(get_db)):
    # Buscar o último id_pedido do cliente
    query_last = """
        SELECT id_pedido FROM pizzaria.pedido
        WHERE id_cliente = :id_cliente
        ORDER BY id_pedido DESC
        LIMIT 1
    """
    last_pedido = session.execute(text(query_last), {'id_cliente': post_pedido.id_cliente}).fetchone()
    if not last_pedido:
        raise HTTPException(status_code=404, detail="Nenhum pedido encontrado para este cliente.")

    id_pedido = last_pedido[0]

    # Inserir item no último pedido
    query = """
        INSERT INTO pizzaria.item_pedido (id_pedido, id_produto, quantidade) 
        VALUES (:id_pedido, :id_produto, :quantidade)
    """
    params = {
        'id_pedido': id_pedido,
        'id_produto': post_pedido.id_produto,
        'quantidade': post_pedido.quantidade
    }
    
    session.execute(text(query), params)
    session.commit()
    
    return {"message": "Item adicionado ao pedido com sucesso!", "id_pedido": id_pedido}

@app.get('/pedidos')
def get_pedidos(id_cliente: int, session: Session = Depends(get_db)):
    query = """
        SELECT p.id_pedido, p.data_pedido, p.id_funcionario, i.id_produto, i.quantidade, c.sabor, c.preco, c.foto
        FROM pizzaria.pedido p
        JOIN pizzaria.item_pedido i ON p.id_pedido = i.id_pedido
        JOIN pizzaria.catalogo c ON i.id_produto = c.id_produto
        WHERE p.id_cliente = :id_cliente
        ORDER BY p.id_pedido DESC
    """
    result = session.execute(text(query), {'id_cliente': id_cliente}).fetchall()
    
    if not result:
        raise HTTPException(status_code=404, detail="Nenhum pedido encontrado para este cliente.")
    
    pedidos_dict = {}
    for row in result:
        id_pedido = row[0]
        if id_pedido not in pedidos_dict:
            pedidos_dict[id_pedido] = {
                "id_pedido": id_pedido,
                "data_pedido": row[1],
                "id_funcionario": row[2],
                "sabores": [],
                "total": 0
            }
        subtotal = row[4] * row[6]  # quantidade * preco
        pedidos_dict[id_pedido]["sabores"].append({
            "id_produto": row[3],
            "sabor": row[5],
            "quantidade": row[4],
            "preco_unitario": row[6],
            "subtotal": subtotal,
            "foto": row[7]
        })
        pedidos_dict[id_pedido]["total"] += subtotal

    return {"pedidos": list(pedidos_dict.values())}


@app.get('/qtd_pedidos')
def get_qtd_pedidos(id_cliente: int, session: Session = Depends(get_db)):
    query = """
        SELECT COUNT(*) FROM pizzaria.pedido WHERE id_cliente = :id_cliente
    """
    result = session.execute(text(query), {'id_cliente': id_cliente}).scalar()
    
    if result is None:
        raise HTTPException(status_code=404, detail="Nenhum pedido encontrado para este cliente.")
    
    return result