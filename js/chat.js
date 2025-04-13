document.addEventListener("DOMContentLoaded", function () {
    const chatBox = document.getElementById("chat-box");
    const chatInput = document.getElementById("chat-input");
    const sendButton = document.getElementById("send-btn");
    const course = document.body.getAttribute("data-course"); // Identify course
    const username = prompt("Enter your name:") || "Anonymous";

    // Fetch and display messages
    async function loadMessages() {
        const response = await fetch(`/get_messages/${course}`);
        const messages = await response.json();
        chatBox.innerHTML = "";

        messages.forEach(msg => {
            const messageElement = document.createElement("p");
            messageElement.innerHTML = `<strong>${msg.username}:</strong> ${msg.message}`;
            chatBox.appendChild(messageElement);
        });

        chatBox.scrollTop = chatBox.scrollHeight;
    }

    sendButton.addEventListener("click", async function () {
        const message = chatInput.value.trim();
        if (message === "") return;

        const response = await fetch("/send_message", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, message, course })
        });

        if (response.ok) {
            chatInput.value = "";
            loadMessages();
        }
    });

    setInterval(loadMessages, 3000); // Refresh messages every 3s
});
