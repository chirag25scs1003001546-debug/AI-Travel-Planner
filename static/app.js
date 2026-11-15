const tripForm = document.getElementById("tripForm");
const generateBtn = document.getElementById("generateBtn");
const resultPanel = document.getElementById("resultPanel");
const planOutput = document.getElementById("planOutput");
const modeNote = document.getElementById("modeNote");
const toast = document.getElementById("toast");

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 2600);
}

document.querySelectorAll(".style-option").forEach(option => {
  option.addEventListener("click", () => {
    document.querySelectorAll(".style-option").forEach(item => item.classList.remove("selected"));
    option.classList.add("selected");
    option.querySelector("input").checked = true;
  });
});

function escapeHtml(value) {
  return value.replace(/[&<>"']/g, char => ({
    "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#039;"
  }[char]));
}

// Small Markdown renderer for model output. Raw HTML is escaped before formatting.
function renderMarkdown(markdown) {
  let html = escapeHtml(markdown);
  html = html.replace(/^### (.*)$/gm, "<h3>$1</h3>")
    .replace(/^## (.*)$/gm, "<h2>$1</h2>")
    .replace(/^# (.*)$/gm, "<h2>$1</h2>")
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.*?)\*/g, "<em>$1</em>")
    .replace(/^&gt; (.*)$/gm, "<blockquote>$1</blockquote>")
    .replace(/^\|(.+)\|$/gm, line => {
      const cells = line.split("|").slice(1,-1).map(c => c.trim());
      if (cells.every(c => /^:?-{3,}:?$/.test(c))) return "";
      return "<tr>" + cells.map(c => `<td>${c}</td>`).join("") + "</tr>";
    })
    .replace(/^- (.*)$/gm, "<li>$1</li>")
    .replace(/(<li>.*<\/li>\n?)+/gs, match => `<ul>${match}</ul>`)
    .replace(/\n/g, "<br>");
  html = html.replace(/(<tr>.*?<\/tr>)(<br>)*(?=<tr>)/gs, "$1");
  return html;
}

tripForm.addEventListener("submit", async event => {
  event.preventDefault();
  const destination = document.getElementById("destination").value.trim();
  if (!destination) return;
  const payload = {
    destination,
    budget: document.getElementById("budget").value || "Not specified",
    currency: document.getElementById("currency").value,
    days: document.getElementById("days").value,
    travelers: document.getElementById("travelers").value,
    startDate: document.getElementById("startDate").value || "Not specified",
    style: document.querySelector('input[name="style"]:checked').value
  };
  generateBtn.disabled = true;
  generateBtn.innerHTML = "✦ Creating your itinerary...";
  resultPanel.classList.remove("hidden");
  planOutput.textContent = "Your AI travel plan is being prepared...";
  modeNote.textContent = "Connecting to your travel assistant…";
  resultPanel.scrollIntoView({behavior:"smooth", block:"start"});
  try {
    const response = await fetch("/api/plan", {
      method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(payload)
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Could not create your plan.");
    planOutput.innerHTML = renderMarkdown(data.plan);
    modeNote.textContent = data.mode === "ai"
      ? "✦ AI-generated plan. Verify time-sensitive details before travelling."
      : "Demo mode: add your Gemini API key in .env to activate destination-specific AI generation.";
    document.getElementById("resultMeta").textContent =
      `${payload.destination} · ${payload.days} days · ${payload.travelers} traveler(s)`;
  } catch (error) {
    planOutput.textContent = error.message;
    modeNote.textContent = "Something went wrong.";
  } finally {
    generateBtn.disabled = false;
    generateBtn.innerHTML = '<span>✦</span> Generate my trip <span class="arrow">→</span>';
  }
});

document.querySelectorAll(".destination-card").forEach(card => {
  card.addEventListener("click", () => {
    document.getElementById("destination").value = card.dataset.place;
    document.getElementById("planner").scrollIntoView({behavior:"smooth"});
    showToast(`${card.dataset.place} added to your trip`);
  });
});

document.getElementById("copyBtn").addEventListener("click", async () => {
  const text = planOutput.innerText;
  try {
    await navigator.clipboard.writeText(text);
    showToast("Your travel plan was copied!");
  } catch {
    showToast("Please select and copy the plan manually.");
  }
});

const chatForm = document.getElementById("chatForm");
const chatMessages = document.getElementById("chatMessages");
function addMessage(text, who) {
  const bubble = document.createElement("div");
  bubble.className = `chat-bubble ${who}`;
  bubble.textContent = text;
  chatMessages.appendChild(bubble);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}
chatForm.addEventListener("submit", async event => {
  event.preventDefault();
  const input = document.getElementById("chatInput");
  const message = input.value.trim();
  if (!message) return;
  addMessage(message, "user");
  input.value = "";
  const waiting = document.createElement("div");
  waiting.className = "chat-bubble bot";
  waiting.textContent = "Thinking of the best answer…";
  chatMessages.appendChild(waiting);
  try {
    const response = await fetch("/api/chat", {
      method:"POST", headers:{"Content-Type":"application/json"},
      body:JSON.stringify({message, destination:document.getElementById("destination").value || "your trip"})
    });
    const data = await response.json();
    waiting.textContent = data.reply || data.error || "Please try again.";
  } catch {
    waiting.textContent = "I couldn't connect just now. Please try again.";
  }
  chatMessages.scrollTop = chatMessages.scrollHeight;
});

document.getElementById("menuBtn").addEventListener("click", () => {
  document.querySelector(".topbar nav").classList.toggle("open");
});
