const API = "http://127.0.0.1:8000";

const filesInput = document.getElementById("pdfs");
const messages = document.getElementById("messages");
const questionBox = document.getElementById("question");
const sendBtn = document.getElementById("sendBtn");
const fileContainer = document.getElementById("selectedFiles");
let sessionId = null;

async function createSession() {

    const response = await fetch(
        `${API}/sessions`,
        {
            method: "POST"
        }
    );

    const session = await response.json();

    sessionId = session.id;

    clearChat();
    await loadHistory();


}

async function loadHistory() {

    const response = await fetch(
        `${API}/sessions`
    );

    const sessions = await response.json();

    const history =
        document.getElementById("history");

    history.innerHTML = "";

    sessions.forEach(session => {

        history.innerHTML += `
            <div
                class="history-item ${session.id===sessionId ? "active" : ""}"
                onclick="openSession('${session.id}')"
            >
                ${session.title}
            </div>
            `;

    });

}

async function openSession(id) {

    sessionId = id;

    const response = await fetch(
        `${API}/sessions/${id}`
    );

    const session =
        await response.json();

    messages.innerHTML="";

    if(session.messages.length===0){
        clearChat();
        return;
    }
    session.messages.forEach(message => {

        if(message.role==="user"){

            addUserMessage(
                message.content
            );

        }

        else{

            addAssistantMessage(
                message.content,
                []
            );

        }

    });

}

window.onload = async () => {

    await loadHistory();

    const response = await fetch(
        `${API}/sessions`
    );

    const sessions =
        await response.json();

    if(sessions.length===0){

        await createSession();

    }

    else{

        await openSession(
            sessions[0].id
        );

    }

};

document
.getElementById("newChatBtn")
.onclick = createSession;

function clearChat(){

    messages.innerHTML = `

        <div id="welcomeScreen" class="welcome">

            <div class="logo">
                📚
            </div>

            <h1>Welcome to ContextAI</h1>

            <p>
                Chat with your own PDF documents using AI.
                Upload one or more PDFs, ask questions in natural language,
                and receive answers with references to the original pages.
            </p>

            <div class="features">

                <div class="feature">
                    📄 Upload multiple PDFs
                </div>

                <div class="feature">
                    🔍 AI-powered document search
                </div>

                <div class="feature">
                    📚 Source citations
                </div>

                <div class="feature">
                    ⚡ Fast semantic retrieval
                </div>

            </div>

        </div>

    `;

}
// --------------------
// Selected Files
// --------------------

filesInput.onchange = () => {

    fileContainer.innerHTML = "";

    for (const file of filesInput.files) {

        fileContainer.innerHTML += `
            <div class="file-chip">
                📄 ${file.name}
            </div>
        `;
    }

};

// --------------------
// Send Message
// --------------------

async function sendMessage() {

    const question = questionBox.value.trim();

    if (!question) return;
    removeWelcomeScreen();
    
    sendBtn.disabled = true;

    addUserMessage(question);

    questionBox.value = "";

    showLoader("Uploading documents...");

    try {

        const files = filesInput.files;

        // --------------------
        // Upload + Index
        // --------------------

        if (files.length > 0) {

            const form = new FormData();

            for (const file of files) {
                form.append("files", file);
            }

            const upload = await fetch(
                `${API}/upload/${sessionId}`,
                {
                    method: "POST",
                    body: form
                }
            );

            if (!upload.ok)
                throw new Error("Failed to upload PDFs.");

            updateLoader("Building search index...");

            const index = await fetch(
                `${API}/index/${sessionId}`,
                {
                    method: "POST"
                }
            );

            if (!index.ok)
                throw new Error("Failed to build index.");

            // Clear selected files

            filesInput.value = "";
            fileContainer.innerHTML = "";

        }

        // --------------------
        // Chat
        // --------------------

        updateLoader("Searching documents...");

        const response = await fetch(
            `${API}/chat/${sessionId}`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    question
                })
            }
        );

        if (!response.ok)
            throw new Error("Failed to generate answer.");

        updateLoader("Generating answer...");

        const data = await response.json();

        hideLoader();

        addAssistantMessage(
            data.answer,
            data.sources
        );

    }

    catch (err) {

        hideLoader();

        addAssistantMessage(
            `❌ ${err.message}`,
            []
        );

    }

    finally {

        sendBtn.disabled = false;

    }

}

// --------------------
// Chat Messages
// --------------------

function addUserMessage(text) {

    const div=document.createElement("div");
    div.className="user";
    div.textContent=text;
    messages.appendChild(div);
    
    messages.innerHTML += `

        <div class="user">

            ${text}

        </div>

    `;

    scrollToBottom();
    

}

function addAssistantMessage(answer, sources) {

    let html = `
        <div class="assistant markdown-body">

        ${marked.parse(answer)}
        `;

        if(sources.length){

            html += `<div class="sources">`;

            for (const source of sources) {

                html += `

                    <div>

                        📄 <strong>${source.source}</strong>

                        • Page ${source.page}

                </div>

            `;

        }

        html+="</div>";
    }

    html += "</div>";

    messages.innerHTML += html;

    scrollToBottom();

}

// --------------------
// Loader
// --------------------

function showLoader(text) {

    messages.innerHTML += `

        <div
            class="assistant"
            id="loader"
        >

            <div id="loaderText">

                ${text}

            </div>

            <div class="loader">

                <span></span>

                <span></span>

                <span></span>

            </div>

        </div>

    `;

    scrollToBottom();

}

function updateLoader(text) {

    const loaderText =
        document.getElementById("loaderText");

    if (loaderText)
        loaderText.textContent = text;

}

function hideLoader() {

    document
        .getElementById("loader")
        ?.remove();

}

// --------------------
// Utilities
// --------------------

function scrollToBottom() {

    messages.scrollTop =
        messages.scrollHeight;

}

function removeWelcomeScreen(){

    const welcome =
        document.getElementById("welcomeScreen");

    if(welcome){

        welcome.remove();

    }

}