from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import pyodbc
from datetime import datetime
from werkzeug.utils import secure_filename
import os
import base64
from PIL import Image

app = Flask(__name__)
app.secret_key = 'chave_secreta_aqui'  # Defina uma chave secreta
# Define o diretório de upload de imagens como um caminho absoluto
UPLOAD_FOLDER = os.path.join(app.root_path, 'static/imagens')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}

# Verificar se a extensão do arquivo é permitida
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Verifica e cria o diretório de upload se ele não existir
#if not os.path.exists(UPLOAD_FOLDER):
#    os.makedirs(UPLOAD_FOLDER)

# Configuração da conexão com o banco de dados
dsn = 'loja'
user = 'root'
password = '001002003'

def create_connection():
    conn = pyodbc.connect(f'DSN={dsn};UID={user};PWD={password}')
    return conn

#dsn = 'local'
#conn = pyodbc.connect(f'DSN={dsn};UID=root;PWD=2103MEIR')


def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            #flash('Você precisa estar logado para acessar esta página.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Rota para página de criação de usuário com ícone
# Rota para gravar a imagem no usuário
@app.route('/gravar_imagem_no_usuario', methods=['POST'])
def gravar_imagem_no_usuario():
    if request.method == 'POST':
        # Receber o arquivo de imagem do formulário
        icon_file = request.files['icon']
        conn =create_connection()    
        # Verificar se foi enviado um arquivo
        if icon_file:
            # Receber o nome de usuário da sessão
            username = session['user']            
            filename = secure_filename(icon_file.filename)
            file_ext = os.path.splitext(filename)[1]  # Isso irá obter a extensão do arquivo            
            # Construir o novo nome do arquivo usando o nome de usuário
            new_filename = f"{username}.png"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
            # Redimensionar a imagem para 48x48 pixels
            image = Image.open(icon_file)
            image = image.resize((96, 96))
            print(filepath)
            image.save(filepath, format='PNG')
            
            cursor = conn.cursor()
            cursor.execute("UPDATE usuarios SET icon = ? WHERE usuario = ?", (new_filename, username))
            conn.commit()
            cursor.close()
            conn.close()

            return redirect(url_for('index'))

    
    # Se for método GET, renderize uma página com um formulário para upload de imagem
    return render_template('imagem_do_perfil.html')


def get_user(usuario):
    conn =create_connection()  
    cursor = conn.cursor()
    cursor.execute(f'SELECT usuario, acesso, nivel, icon FROM usuarios WHERE usuario ="{usuario}"')
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user



@app.route('/usuarios', methods=['GET'])
def get_usuarios():
    conn =create_connection()  
    cursor = conn.cursor()
    cursor.execute("SELECT usuario FROM usuarios WHERE ativo=1")
    rows = cursor.fetchall()
    destinos = [row[0] for row in rows]  # Capturar apenas a coluna 'usuario'
    cursor.close()
    conn.close()
    return jsonify(destinos)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        acesso = request.form['acesso']
        user = get_user(usuario)
        if user and user[1] == acesso:  # Assuming `acesso` is the password field
            session['user'] = user[0]    
            session['icon'] = user[3]  # Nome do arquivo da imagem                      
            return redirect(url_for('index'))        
        else:
            return render_template('login.html', error='Nome ou Senha inválido')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)  # Remove o usuário da sessão
    #flash('Você foi deslogado com sucesso.', 'success')
    return redirect(url_for('login'))


@app.route('/')
@login_required
def index():
    conn =create_connection()  
    cursor = conn.cursor()
    username = session['user']
    cursor.execute("SELECT ID, Titulo, Descricao, Status, QuemAssumiu, NomeDoOperador FROM Tarefas WHERE (Status='ABERTO' OR Status='PENDENTE') and Destinado=?", (username,))
    tarefas = cursor.fetchall()
    tarefas = [{'ID': row[0], 'Titulo': row[1], 'Descricao': row[2], 'Status': row[3], 'QuemAssumiu': row[4], 'Operador': row[5]} for row in tarefas]
    conn.close()
    return render_template('index.html', tarefas=tarefas)


@app.route('/criar', methods=['POST'])
@login_required
def criar_tarefa():
    titulo = request.form['titulo'].upper()
    descricao = request.form['descricao']
    nome_do_operador = request.form['nome_do_operador'].upper()
    loja = request.form['loja'].upper()
    data = datetime.now().strftime('%Y-%m-%d')
    hora = datetime.now().strftime('%H:%M:%S')
    status = 'PENDENTE'
    destinado = request.form['destinado'].upper()
    conn =create_connection()  
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Tarefas (Titulo, Descricao, Data, Hora, Status, NomeDoOperador, Loja, Destinado)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (titulo, descricao, data, hora, status, nome_do_operador, loja, destinado))
    conn.commit()
    conn.close()

    return redirect(url_for('index'))

@app.route('/em_processo/<int:tarefa_id>', methods=['POST'])
@login_required
def em_processo_tarefa(tarefa_id):
    quem_assumiu = request.form['quem_assumiu'].upper()
    data_hora_em_processo = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn =create_connection()  
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE Tarefas
        SET Status = 'PROCESSO', DataHoraEmProcesso = ?, QuemAssumiu = ?
        WHERE ID = ?
    """, (data_hora_em_processo, quem_assumiu, tarefa_id))
    conn.commit()
    conn.close()

    return redirect(url_for('index'))

@app.route('/concluir/<int:tarefa_id>')
@login_required
def concluir_tarefa(tarefa_id):
    data_hora_conclusao = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    conn =create_connection()  
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE Tarefas
        SET Status = 'CONCLUIDO', DataHoraConclusao = ?
        WHERE ID = ?
    """, (data_hora_conclusao, tarefa_id))
    conn.commit()
    conn.close()

    return redirect(url_for('index'))


@app.route('/colocar_pendente/<int:tarefa_id>')
@login_required
def colocar_pendente(tarefa_id):
    conn =create_connection()  
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE Tarefas
        SET Status = 'PENDENTE', DataHoraConclusao = null
        WHERE ID = ?
    """, (tarefa_id))
    conn.commit()
    conn.close()

    return redirect(url_for('index'))


@app.route('/processo')
@login_required
def tarefas_em_processo():
     # Obtém o usuário logado da sessão
    username = session['user']
    conn =create_connection()  
    cursor = conn.cursor()
    cursor.execute("SELECT ID, Titulo, Descricao, Status, QuemAssumiu, NomeDoOperador FROM Tarefas WHERE Status='PROCESSO' AND QuemAssumiu=?", (username,))
    tarefas = cursor.fetchall()
    tarefas = [{'ID': row[0], 'Titulo': row[1], 'Descricao': row[2], 'Status': row[3], 'QuemAssumiu': row[4], 'Operador': row[5]} for row in tarefas]
    conn.close()
    return render_template('index.html', tarefas=tarefas)

@app.route('/meu_perfil', methods=['GET'])
def meu_perfil():
    return render_template('imagem_do_perfil.html')

@app.route('/aguardando')
@login_required
def tarefas_aguardando():
    conn =create_connection()  
    cursor = conn.cursor()
    username = session['user']
    cursor.execute("SELECT ID, Titulo, Descricao, Status, QuemAssumiu, NomeDoOperador FROM Tarefas WHERE (Status='PROCESSO' OR Status='PENDENTE') and Destinado=?",(username,))
    tarefas = cursor.fetchall()
    tarefas = [{'ID': row[0], 'Titulo': row[1], 'Descricao': row[2], 'Status': row[3], 'QuemAssumiu': row[4], 'Operador': row[5]} for row in tarefas]
    conn.close()
    return render_template('index.html', tarefas=tarefas)


@app.route('/pendentes')
@login_required
def tarefas_pendentes():
    conn =create_connection()  
    cursor = conn.cursor()
    username = session['user']
    cursor.execute("SELECT ID, Titulo, Descricao, Status, QuemAssumiu, NomeDoOperador FROM Tarefas WHERE Status='PENDENTE' and Destinado=? ",(username,))
    tarefas = cursor.fetchall()
    tarefas = [{'ID': row[0], 'Titulo': row[1], 'Descricao': row[2], 'Status': row[3], 'QuemAssumiu': row[4], 'Operador': row[5]} for row in tarefas]
    conn.close()
    return render_template('index.html', tarefas=tarefas)

@app.route('/meuscards')
@login_required
def tarefas_que_gerei():
    conn =create_connection()  
    cursor = conn.cursor()
    username = session['user']
    cursor.execute("SELECT ID, Titulo, Descricao, Status, QuemAssumiu, NomeDoOperador FROM Tarefas WHERE NomeDoOperador=? ",(username,))
    tarefas = cursor.fetchall()
    tarefas = [{'ID': row[0], 'Titulo': row[1], 'Descricao': row[2], 'Status': row[3], 'QuemAssumiu': row[4], 'Operador': row[5]} for row in tarefas]
    conn.close()
    return render_template('index.html', tarefas=tarefas)



if __name__ == '__main__':
   app.run(host='0.0.0.0', port=5001, debug=True)
