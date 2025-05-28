COMO RODAR ESSE APLICATIVO

instalar python

ativar ambiente virtual na pasta
python -m venv venv
venv/Scripts/activate

instalar dependencias
pip install -r requirements.txt

rodar aplicativo
fastapi run main.py

configurar .env (credenciais padrões do mysql)
DB2_HOST=localhost
DB2_DB=pizzaria
DB2_PORT=3306
DB2_USER=root
DB2_PASS=root