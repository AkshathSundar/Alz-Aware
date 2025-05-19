const chatHeader = document.getElementById('chat-header');
const chatBody = document.getElementById('chat-body');
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');

function toggleChat() {
    if (chatBody.style.display === 'none') {
        chatBody.style.display = 'block';
    } else {
        chatBody.style.display = 'none';
    }
}

async function sendMessage() {
    const message = chatInput.value.trim();
    if (!message) return;

    appendMessage('You', message);
    chatInput.value = '';

    const response = await fetch('/api/ask_bot', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ message })
    });

    if (response.ok) {
        const data = await response.json();
        appendMessage('Bot', data.reply);
    } else {
        appendMessage('Bot', 'Sorry, I could not process your message.');
    }
}

function appendMessage(sender, text) {
    const msgDiv = document.createElement('div');
    msgDiv.innerHTML = `<b>${sender}:</b> ${text}`;
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}
