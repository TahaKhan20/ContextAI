const API = "http://127.0.0.1:8000";

const filesInput = document.getElementById("pdfs");
const messages = document.getElementById("messages");
const questionBox = document.getElementById("question");
const sendBtn = document.getElementById("sendBtn");
const fileContainer = document.getElementById("selectedFiles");
let sessionId = null;
let isNewSession = false;


async function createSession() {

    sessionId = null;
    isNewSession = true;

    clearChat();

}

async function loadHistory() {

    const response = await fetch(
        `${API}/sessions`
    );

    const sessions = await response.json();

    const history =
        document.getElementById("history");

    history.innerHTML = "";

    sessions
    .filter(session => session.messages && session.messages.length > 0)
    .forEach(session => {

    history.innerHTML += `
    <div
        class="history-item ${session.id === sessionId ? "active" : ""}"
        data-id="${session.id}"
        onclick="openSession('${session.id}')"
    >
        <div class="history-title">
            ${session.title}
        </div>

        <div class="history-actions">

            <button
                onclick="event.stopPropagation(); editSession('${session.id}', this)">
                ✏️
            </button>

            <button
                onclick="event.stopPropagation(); deleteSession('${session.id}')">
                🗑
            </button>

        </div>
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

    if (sessions.length === 0) {

        clearChat();
        isNewSession = true;
        sessionId = null;

    }
    else{

        await openSession(sessions[0].id);

    }

};

document
.getElementById("newChatBtn")
.onclick = createSession;

async function editSession(id, btn) {

    const item = btn.closest(".history-item");
    const title = item.querySelector(".history-title");
    const actions = item.querySelector(".history-actions");

    const oldTitle = title.textContent;

    title.innerHTML = `
        <input
            class="rename-input"
            value="${oldTitle}"
        >
    `;

    const input = title.querySelector("input");

    actions.innerHTML = `
        <button onclick="saveRename('${id}', this)">✔</button>
        <button onclick="cancelRename(this, '${oldTitle.replace(/'/g, "\\'")}')">✖</button>
    `;

    input.focus();
    input.select();

    input.onkeydown = e => {
        if (e.key === "Enter")
            saveRename(id, actions.children[0]);

        if (e.key === "Escape")
            cancelRename(actions.children[1], oldTitle);
    };

}

async function saveRename(id, btn) {

    const item = btn.closest(".history-item");
    const input = item.querySelector(".rename-input");

    const title = input.value.trim();

    if (!title) {
        cancelRename(btn, "");
        return;
    }

    await fetch(`${API}/sessions/${id}`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ title })
    });

    await loadHistory();

}

function cancelRename(btn, oldTitle) {

    const item = btn.closest(".history-item");

    item.querySelector(".history-title").textContent = oldTitle;

    const id = item.dataset.id;

    item.querySelector(".history-actions").innerHTML = `
        <button onclick="editSession('${id}', this)">✏️</button>
        <button onclick="deleteSession('${id}')">🗑</button>
    `;

}


async function deleteSession(id){

    if(!confirm("Are you sure you want to delete this chat?"))
        return;

    await fetch(`${API}/sessions/${id}`,{

        method:"DELETE"

    });

    if(sessionId === id){

        sessionId = null;
        isNewSession = true;
        clearChat();

    }

    await loadHistory();

}

function clearChat(){

    messages.innerHTML = `

                    <div
                id="welcomeScreen"
                class="welcome"
            >

                <div class="logo">

                    <img
                        src="favicon.svg"
                        alt="ContextAI"
                    >

                </div>

                <h1>Welcome to ContextAI</h1>

                <p>
                    Upload one or more PDF documents and chat with them using AI.
                    ContextAI retrieves the most relevant information from your
                    documents and answers with accurate, source-backed responses.
                </p>

                <div class="features">

                    <div class="feature">
                        📄 Multiple PDF Support
                    </div>

                    <div class="feature">
                        🔍 Semantic Search
                    </div>

                    <div class="feature">
                        📚 Source Citations
                    </div>

                    <div class="feature">
                        ⚡ Fast AI Responses
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

    if (isNewSession || sessionId === null) {

        const response = await fetch(`${API}/sessions`, {
            method: "POST"
        });

        const session = await response.json();
        
        sessionId = session;
        isNewSession = false;

        await loadHistory();

    }

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

        await loadHistory();
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

function addUserMessage(text){

    const div = document.createElement("div");

    div.className = "user";
    div.textContent = text;

    messages.appendChild(div);

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

const sidebar = document.getElementById("sidebar");

const toggle = document.getElementById("sidebarToggle");

toggle.onclick = () => {

    if(window.innerWidth <= 900){

        sidebar.classList.toggle("show");

    }

    else{

        sidebar.classList.toggle("hidden");

        document
            .querySelector(".app")
            .classList.toggle("sidebar-hidden");

    }

};

