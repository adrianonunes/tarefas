from flask import Flask, render_template, request, redirect, url_for
import pyodbc
from datetime import datetime

app = Flask(__name__)

# Configuração da conexão com o banco de dados
dsn = 'loja'
conn = pyodbc.connect(f'DSN={dsn};UID=root;PWD=001002003')

@app.route('/')
def index():
    cursor = conn.cursor()
    cursor.execute("SELECT ID, Titulo, Descricao, Status FROM Tarefas WHERE Status='ABERTO' OR Status='PENDENTE'")
    tarefas = cursor.fetchall()
    tarefas = [{'ID': row[0], 'Titulo': row[1], 'Descricao': row[2], 'Status': row[3]} for row in tarefas]
    return render_template('index.html', tarefas=tarefas)

@app.route('/criar', methods=['POST'])
def criar_tarefa():
    titulo = request.form['titulo']
    descricao = request.form['descricao']
    nome_do_operador = request.form['nome_do_operador']
    loja = request.form['loja']
    data = datetime.now().strftime('%Y-%m-%d')
    hora = datetime.now().strftime('%H:%M:%S')
    status = 'PENDENTE'

    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Tarefas (Titulo, Descricao, Data, Hora, Status, NomeDoOperador, Loja)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (titulo, descricao, data, hora, status, nome_do_operador, loja))
    conn.commit()

    return redirect(url_for('index'))

@app.route('/em_processo/<int:tarefa_id>', methods=['POST'])
def em_processo_tarefa(tarefa_id):
    quem_assumiu = request.form['quem_assumiu']
    data_hora_em_processo = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    cursor = conn.cursor()
    cursor.execute("""
        UPDATE Tarefas
        SET Status = 'PROCESSO', DataHoraEmProcesso = ?, QuemAssumiu = ?
        WHERE ID = ?
    """, (data_hora_em_processo, quem_assumiu, tarefa_id))
    conn.commit()

    return redirect(url_for('index'))

@app.route('/concluir/<int:tarefa_id>')
def concluir_tarefa(tarefa_id):
    data_hora_conclusao = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    cursor = conn.cursor()
    cursor.execute("""
        UPDATE Tarefas
        SET Status = 'CONCLUIDO', DataHoraConclusao = ?
        WHERE ID = ?
    """, (data_hora_conclusao, tarefa_id))
    conn.commit()

    return redirect(url_for('index'))

@app.route('/processo')
def tarefas_em_processo():
    cursor = conn.cursor()
    cursor.execute("SELECT ID, Titulo, Descricao, Status FROM Tarefas WHERE Status='PROCESSO'")
    tarefas = cursor.fetchall()
    tarefas = [{'ID': row[0], 'Titulo': row[1], 'Descricao': row[2], 'Status': row[3]} for row in tarefas]
    return render_template('index.html', tarefas=tarefas)

@app.route('/pendentes')
def tarefas_pendentes():
    cursor = conn.cursor()
    cursor.execute("SELECT ID, Titulo, Descricao, Status FROM Tarefas WHERE Status='PENDENTE'")
    tarefas = cursor.fetchall()
    tarefas = [{'ID': row[0], 'Titulo': row[1], 'Descricao': row[2], 'Status': row[3]} for row in tarefas]
    return render_template('index.html', tarefas=tarefas)

if __name__ == '__main__':
    app.run(debug=True)
