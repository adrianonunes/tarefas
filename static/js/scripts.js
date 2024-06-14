document.addEventListener('DOMContentLoaded', function() {
    // Abrir modal de criar tarefa
    document.getElementById('criar-tarefa-btn').addEventListener('click', function() {
        document.getElementById('modalCriarTarefa').style.display = 'block';
        // Fazer requisição AJAX para a rota /usuarios
        fetch('/usuarios')
            .then(response => response.json())
            .then(data => {
                // Limpar o conteúdo atual do select
                let select = document.getElementById('destinado');
                select.innerHTML = '<option value="">Selecione um Destinatário</option>';

                // Preencher o select com os dados recebidos
                data.forEach(function(usuario) {
                    let option = document.createElement('option');
                    option.value = usuario;
                    option.textContent = usuario;
                    select.appendChild(option);
                });
            })
            .catch(error => console.error('Erro ao carregar os usuários:', error));
    });


    // Abrir modal de assumir tarefa
    document.querySelectorAll('.em-processo-btn').forEach(function(button) {
        button.addEventListener('click', function() {
            const tarefaId = button.getAttribute('data-id');
            const formEmProcesso = document.getElementById('formEmProcesso');
            formEmProcesso.action = `/em_processo/${tarefaId}`;
            document.getElementById('modalEmProcesso').style.display = 'block';
        });
    });

    // Fechar modais
    document.querySelectorAll('.close').forEach(function(closeBtn) {
        closeBtn.closest('.modal').style.display = 'none';

        closeBtn.addEventListener('click', function() {
        });
    });
    

    // Fechar modal se clicar fora do conteúdo
    window.onclick = function(event) {
        if (event.target.classList.contains('modal')) {
            event.target.style.display = 'none';
        }
    };
});
