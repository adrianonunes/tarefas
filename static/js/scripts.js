// scripts.js
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.em-processo-btn').forEach(function(button) {
        button.addEventListener('click', function() {
            var tarefaId = this.getAttribute('data-id');
            document.getElementById('formEmProcesso').action = '/em_processo/' + tarefaId;
            document.getElementById('tarefaId').value = tarefaId;
        });
    });
    document.getElementById('criar-tarefa-btn').addEventListener('click', function() {
        $('#modalCriarTarefa').modal('show');
    });
});
