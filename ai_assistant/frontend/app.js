const statusEl = document.getElementById("status");
const logEl = document.getElementById("log");
const connectBtn = document.getElementById("connect");
const disconnectBtn = document.getElementById("disconnect");
const captureBtn = document.getElementById("capture-scene");
const cameraImg = document.getElementById("camera");
const placeholder = document.getElementById("placeholder");

const BACKEND_URL = "http://localhost:8000";

let pc = null;
let dataChannel = null;
let localStream = null;

function log(msg, obj) {
  const line = document.createElement("div");
  line.textContent = `[${new Date().toLocaleTimeString()}] ${msg}`;
  logEl.appendChild(line);
  if (obj) {
    const pre = document.createElement("pre");
    pre.textContent = JSON.stringify(obj, null, 2);
    logEl.appendChild(pre);
  }
  logEl.scrollTop = logEl.scrollHeight;
}

function setStatus(text) {
  statusEl.textContent = text;
  log(text);
}

async function captureAndDisplayRobotImage() {
  const resp = await fetch(`${BACKEND_URL}/camera/capture`);
  const data = await resp.json();
  if (data.status !== "success") throw new Error(data.message || "capture failed");
  cameraImg.src = `data:image/png;base64,${data.image}`;
  cameraImg.style.display = "block";
  placeholder.style.display = "none";
  return data.image;
}

function sendEvent(ev) {
  if (!dataChannel || dataChannel.readyState !== "open") return;
  dataChannel.send(JSON.stringify(ev));
}

async function sendSceneImageToModel() {
  const base64 = await captureAndDisplayRobotImage();
  const resp = await fetch(`${BACKEND_URL}/analyze_image`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ image: base64 }),
  });
  const data = await resp.json();
  if (data.status !== "success") {
    log("Analysis failed", data);
    return;
  }
  sendEvent({
    type: "conversation.item.create",
    item: { type: "message", role: "user", content: [{ type: "input_text", text: data.description }] },
  });
  sendEvent({ type: "response.create" });
}

async function startMedia() {
  localStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
  await captureAndDisplayRobotImage();
}

async function startRealtime() {
  setStatus("Requesting session...");
  const sessionResp = await fetch(`${BACKEND_URL}/session`, { method: "POST" });
  const { ephemeral_key } = await sessionResp.json();

  await startMedia();
  setStatus("Setting up connection...");
  pc = new RTCPeerConnection();
  const audioElement = document.createElement("audio");
  audioElement.autoplay = true;
  pc.ontrack = (ev) => (audioElement.srcObject = ev.streams[0]);
  for (const t of localStream.getAudioTracks()) pc.addTrack(t, localStream);

  dataChannel = pc.createDataChannel("oai-events");
  dataChannel.onopen = () => {
    setStatus("Connected and ready");
    disconnectBtn.disabled = false;
    captureBtn.disabled = false;
    connectBtn.disabled = true;
  };
  dataChannel.onmessage = (m) => {
    try {
      const d = JSON.parse(m.data);
      if (d.type === "response.function_call_arguments.done") handleFunctionCallEvent(d);
      if (d.type === "response.done") {
        const out = d.response?.output?.[0];
        if (out?.type === "function_call") handleFunctionCallEvent(out);
      }
    } catch (e) {
      console.error(e);
    }
  };

  pc.onicecandidate = async (ev) => {
    if (ev.candidate) return;
    const offer = pc.localDescription;
    setStatus("Connecting to AI...");
    const resp = await fetch("https://api.openai.com/v1/realtime/calls", {
      method: "POST",
      headers: { "Content-Type": "application/sdp", Authorization: `Bearer ${ephemeral_key}` },
      body: offer.sdp,
    });
    const answerSdp = await resp.text();
    await pc.setRemoteDescription({ type: "answer", sdp: answerSdp });
    log("✓ WebRTC connection established!");
  };

  const offer = await pc.createOffer();
  await pc.setLocalDescription(offer);
  log("✓ Local offer created");
}

function stopRealtime() {
  if (pc) pc.close();
  pc = null;
  if (localStream) {
    localStream.getTracks().forEach((t) => t.stop());
    localStream = null;
  }
  cameraImg.style.display = "none";
  placeholder.style.display = "block";
  dataChannel = null;
  disconnectBtn.disabled = true;
  captureBtn.disabled = true;
  connectBtn.disabled = false;
  setStatus("Disconnected");
}

async function handleFunctionCallEvent(ev) {
  const { name, call_id, arguments: argsJson } = ev;
  let args = {};
  try { args = argsJson ? JSON.parse(argsJson) : {}; } catch {}
  log(`Function call: ${name}`, args);

  if (name === "capture_scene") {
    const skip = args.skip_analysis === true;
    await captureAndDisplayRobotImage();
    if (!skip) await sendSceneImageToModel();
    return;
  }

  // Supported robot policy: ACT carrot pick-and-place
  if (name === "run_pick_and_place") {
    const resp = await fetch(`${BACKEND_URL}/robot/run_policy`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ policy_name: name, params: args }),
    });
    const data = await resp.json();
    log(`Policy finished: ${name}`, data);
    try { await captureAndDisplayRobotImage(); } catch (e) {}
    sendEvent({
      type: "conversation.item.create",
      item: { type: "function_call_output", call_id: call_id, output: JSON.stringify(data) },
    });
    sendEvent({ type: "response.create" });
    return;
  }
}

connectBtn.onclick = async () => {
  connectBtn.disabled = true;
  try { await startRealtime(); } catch (e) { setStatus("Error: " + e.message); connectBtn.disabled = false; }
};
disconnectBtn.onclick = () => stopRealtime();
captureBtn.onclick = async () => { try { await sendSceneImageToModel(); } catch (e) { log("Error: " + e.message); } };

log("GPT - ACT Voice Control");
log("Click 'Connect and Start' to begin");