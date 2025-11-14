const form = document.getElementById("prompt-form");
const promptInput = document.getElementById("prompt");
const generateButton = document.getElementById("generate-button");
const statusBox = document.getElementById("status");
const resultSection = document.getElementById("result");
const videoElement = document.getElementById("result-video");
const downloadLink = document.getElementById("download-link");
const resetButton = document.getElementById("reset-button");
const conceptText = document.getElementById("concept-text");
const scriptText = document.getElementById("script-text");
const captionsList = document.getElementById("captions-list");
const metadataList = document.getElementById("metadata");

let activeObjectUrl = null;

function showStatus(message, variant = "info") {
  if (!message) {
    statusBox.textContent = "";
    statusBox.className = "status";
    return;
  }

  statusBox.textContent = message;
  statusBox.className = `status show ${variant}`;
}

function setLoading(isLoading) {
  generateButton.disabled = isLoading;
  generateButton.textContent = isLoading ? "Generating…" : "Generate Video";
  showStatus(isLoading ? "Running the workflow…" : "", "info");
}

function base64ToBlob(base64, mimeType) {
  const byteCharacters = atob(base64);
  const byteArrays = [];
  const sliceSize = 1024;

  for (let offset = 0; offset < byteCharacters.length; offset += sliceSize) {
    const slice = byteCharacters.slice(offset, offset + sliceSize);
    const byteNumbers = new Array(slice.length);
    for (let i = 0; i < slice.length; i += 1) {
      byteNumbers[i] = slice.charCodeAt(i);
    }
    byteArrays.push(new Uint8Array(byteNumbers));
  }

  return new Blob(byteArrays, { type: mimeType });
}

function clearResult() {
  if (activeObjectUrl) {
    URL.revokeObjectURL(activeObjectUrl);
    activeObjectUrl = null;
  }

  videoElement.removeAttribute("src");
  downloadLink.href = "#";
  captionsList.innerHTML = "";
  metadataList.innerHTML = "";
  conceptText.textContent = "";
  scriptText.textContent = "";
  resultSection.hidden = true;
}

function renderMetadata(metadata) {
  metadataList.innerHTML = "";
  if (!metadata || typeof metadata !== "object") {
    return;
  }

  Object.entries(metadata).forEach(([key, value]) => {
    const dt = document.createElement("dt");
    dt.textContent = key.replace(/_/g, " ");

    const dd = document.createElement("dd");
    let displayValue = value;
    if (typeof value === "string") {
      try {
        const parsed = JSON.parse(value);
        displayValue = JSON.stringify(parsed, null, 2);
      } catch (error) {
        displayValue = value;
      }
    } else if (typeof value === "object") {
      displayValue = JSON.stringify(value, null, 2);
    }

    dd.textContent = displayValue;
    metadataList.appendChild(dt);
    metadataList.appendChild(dd);
  });
}

function renderResult(data) {
  if (!data || !data.video || !data.video.base64) {
    throw new Error("Response missing video payload");
  }

  const blob = base64ToBlob(data.video.base64, data.video.mime_type || "video/mp4");
  const objectUrl = URL.createObjectURL(blob);
  activeObjectUrl = objectUrl;

  videoElement.src = objectUrl;
  videoElement.load();
  downloadLink.href = objectUrl;
  downloadLink.download = data.video.filename || "final_video.mp4";

  conceptText.textContent = data.final_concept || "";
  scriptText.textContent = data.script_text || "";

  captionsList.innerHTML = "";
  (data.captions || []).forEach((caption) => {
    const li = document.createElement("li");
    li.textContent = caption;
    captionsList.appendChild(li);
  });

  renderMetadata(data.metadata);

  resultSection.hidden = false;
  showStatus("Workflow complete! Scroll down to preview the video.", "success");
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearResult();

  const prompt = promptInput.value.trim();
  if (!prompt) {
    showStatus("Please provide a prompt with 1-3 sentences.", "error");
    return;
  }

  setLoading(true);

  try {
    const response = await fetch("/.netlify/functions/run_workflow", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt }),
    });

    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "The workflow failed.");
    }

    renderResult(payload);
  } catch (error) {
    console.error(error);
    showStatus(error.message || "Something went wrong.", "error");
  } finally {
    setLoading(false);
  }
});

resetButton.addEventListener("click", () => {
  clearResult();
  promptInput.focus();
  showStatus("", "info");
});

window.addEventListener("beforeunload", () => {
  if (activeObjectUrl) {
    URL.revokeObjectURL(activeObjectUrl);
  }
});
