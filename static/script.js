document.addEventListener('DOMContentLoaded', function() {
    // Função para enviar a pergunta ao servidor
    function enviarPergunta() {
        let pergunta = document.getElementById('input-pergunta').value;

        if (pergunta.trim() === '') {
            alert('Por favor, insira uma pergunta.');
            return;
        }

        fetch('/pergunta', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ pergunta: pergunta }),
        })
        .then(response => response.json())
        .then(data => {
            let chatWindow = document.getElementById('chat-window');

            // Exibe a pergunta do usuário no chat
            chatWindow.innerHTML += `
                <p class="user-message">
                    <strong>Você:</strong> ${pergunta}
                </p>
            `;

            // Formatação da resposta do chatbot (transformando as quebras de linha em <br>)
            let respostaFormatada = data.resposta.replace(/\n/g, '<br>');

            // Exibe a resposta do chatbot no chat
            chatWindow.innerHTML += `
                <p class="bot-response">
                    <strong>Chatbot:</strong><br>${respostaFormatada}
                </p>
            `;

            // Rola o chat para o final automaticamente
            chatWindow.scrollTop = chatWindow.scrollHeight;

            // Limpa o campo de input
            document.getElementById('input-pergunta').value = '';
        })
        .catch(error => console.error('Erro ao processar a pergunta:', error));
    }

    // Função para enviar o feedback (positivo ou negativo)
    function enviarFeedback(positivo) {
        fetch('/feedback', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ positivo: positivo }),
        })
        .then(response => console.log('Feedback enviado'))
        .catch(error => console.error('Erro ao enviar feedback:', error));
    }

    // Ações nos eventos do teclado e dos botões
    document.getElementById('input-pergunta').addEventListener('keydown', function(event) {
        if (event.key === 'Enter') {
            enviarPergunta();
        }
    });

    document.querySelector('button').addEventListener('click', enviarPergunta);

    document.querySelectorAll('.feedback-buttons button').forEach(button => {
        button.addEventListener('click', function() {
            const positivo = this.innerText === '👍';
            enviarFeedback(positivo);
        });
    });
});