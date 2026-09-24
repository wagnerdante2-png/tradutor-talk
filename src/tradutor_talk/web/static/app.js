const labTokenPanel = document.getElementById("labTokenPanel");
const labTokenInput = document.getElementById("labToken");
const unlockLabButton = document.getElementById("unlockLab");
const geminiKeyPanel = document.getElementById("geminiKeyPanel");
const geminiKeyInput = document.getElementById("geminiKey");
const saveGeminiKeyButton = document.getElementById("saveGeminiKey");
const remoteButton = document.getElementById("remoteButton");
const localButton = document.getElementById("localButton");
const stopButton = document.getElementById("stopButton");
const localLanguage = document.getElementById("localLanguage");
const remoteLanguage = document.getElementById("remoteLanguage");
const backendBadge = document.getElementById("backendBadge");
const statusText = document.getElementById("statusText");
const statusDetail = document.getElementById("statusDetail");
const progressBar = document.getElementById("progressBar");
const originalText = document.getElementById("originalText");
const translatedText = document.getElementById("translatedText");
const connectionMetric = document.getElementById("connectionMetric");
const firstAudioMetric = document.getElementById("firstAudioMetric");
const directionMetric = document.getElementById("directionMetric");
const liveMeterBar = document.getElementById("liveMeterBar");
const securityInfo = document.getElementById("securityInfo");

const GEMINI_WS_BASE = "wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContentConstrained";
const INPUT_RATE = 16000;
const OUTPUT_RATE = 24000;
const CHUNK_SAMPLES = 1600;

let labToken = sessionStorage.getItem("tradutorTalkLabToken") || "";
let labAuthenticated = false;
let geminiConfigured = false;
let websocket = null;
let micStream = null;
let captureContext = null;
let playbackContext = null;
let processor = null;
let sourceNode = null;
let silentGain = null;
let pendingPcm = new Int16Array(0);
let activeDirection = null;
let activeButton = null;
let sessionStartedAt = 0;
let firstAudioAt = 0;
let nextPlaybackTime = 0;
let stopping = false;
let quietTimer = null;
let activePlaybackSources = 0;

function setStatus(title, detail = "", progress = 0) {
  statusText.textContent = title;
  statusDetail.textContent = detail;
  progressBar.style.width = String(progress) + "%";
}

function canStart() {
  return labAuthenticated && geminiConfigured && websocket === null;
}

function updateControls() {
  const ready = canStart();
  remoteButton.disabled = !ready;
  localButton.disabled = !ready;
  stopButton.disabled = websocket === null;
  localLanguage.disabled = websocket !== null;
  remoteLanguage.disabled = websocket !== null;
}

async function api(path, options = {}) {
  const requestOptions = {...options};
  requestOptions.headers = new Headers(requestOptions.headers || {});
  if (labToken) requestOptions.headers.set("X-Tradutor-Token", labToken);

  const response = await fetch(path, requestOptions);
  let payload = {};
  try {
    payload = await response.json();
  } catch (_) {}

  if (!response.ok) {
    throw new Error(payload.detail || ("HTTP " + response.status));
  }
  return payload;
}

async function refreshHealth() {
  if (!labToken) {
    labAuthenticated = false;
    geminiConfigured = false;
    backendBadge.textContent = "Aguardando token";
    backendBadge.className = "badge";
    labTokenPanel.classList.remove("hidden");
    geminiKeyPanel.classList.add("hidden");
    securityInfo.textContent = "API bloqueada";
    updateControls();
    return;
  }

  try {
    const health = await api("/api/health");
    labAuthenticated = true;
    geminiConfigured = Boolean(health.gemini_key_configured);
    backendBadge.textContent = "Codespace online · Gemini Live";
    backendBadge.className = "badge ok";
    labTokenPanel.classList.add("hidden");
    geminiKeyPanel.classList.toggle("hidden", geminiConfigured);
    securityInfo.textContent = geminiConfigured ? "Gemini configurado" : "Aguardando Gemini key";
    if (!geminiConfigured) {
      setStatus("Laboratório desbloqueado", "Informe a GEMINI_API_KEY para habilitar o Live Translate.", 0);
    } else if (!websocket) {
      setStatus("Pronto para tradução ao vivo", "Escolha a direção e clique em iniciar.", 0);
    }
    updateControls();
  } catch (_) {
    labAuthenticated = false;
    geminiConfigured = false;
    backendBadge.textContent = "Token inválido";
    backendBadge.className = "badge bad";
    labTokenPanel.classList.remove("hidden");
    geminiKeyPanel.classList.add("hidden");
    securityInfo.textContent = "API bloqueada";
    setStatus("Token do laboratório inválido", "Copie novamente o token do Codespace.", 0);
    updateControls();
  }
}

unlockLabButton.addEventListener("click", async () => {
  const value = labTokenInput.value.trim();
  if (!value) return;
  labToken = value;
  sessionStorage.setItem("tradutorTalkLabToken", value);
  labTokenInput.value = "";
  await refreshHealth();
});

saveGeminiKeyButton.addEventListener("click", async () => {
  const value = geminiKeyInput.value.trim();
  if (!value) return;

  saveGeminiKeyButton.disabled = true;
  try {
    await api("/api/gemini-key", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({api_key: value})
    });
    geminiKeyInput.value = "";
    geminiConfigured = true;
    setStatus("Gemini configurado", "A chave ficou somente na memória do Codespace.", 0);
    await refreshHealth();
  } catch (error) {
    setStatus("Falha ao configurar Gemini", error.message, 0);
  } finally {
    saveGeminiKeyButton.disabled = false;
  }
});

function appendTranscript(element, text) {
  if (!text) return;
  if (element.textContent === "—") element.textContent = "";
  element.textContent += text;
}

function base64ToInt16(base64) {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i);
  return new Int16Array(bytes.buffer, bytes.byteOffset, Math.floor(bytes.byteLength / 2));
}

function int16ToBase64(samples) {
  const bytes = new Uint8Array(samples.buffer, samples.byteOffset, samples.byteLength);
  let binary = "";
  const step = 0x8000;
  for (let offset = 0; offset < bytes.length; offset += step) {
    binary += String.fromCharCode(...bytes.subarray(offset, Math.min(offset + step, bytes.length)));
  }
  return btoa(binary);
}

function downsampleTo16k(input, inputRate) {
  if (inputRate === INPUT_RATE) {
    const out = new Int16Array(input.length);
    for (let i = 0; i < input.length; i += 1) {
      const value = Math.max(-1, Math.min(1, input[i]));
      out[i] = value < 0 ? value * 0x8000 : value * 0x7fff;
    }
    return out;
  }

  const ratio = inputRate / INPUT_RATE;
  const outputLength = Math.floor(input.length / ratio);
  const out = new Int16Array(outputLength);

  for (let i = 0; i < outputLength; i += 1) {
    const start = Math.floor(i * ratio);
    const end = Math.max(start + 1, Math.floor((i + 1) * ratio));
    let sum = 0;
    let count = 0;
    for (let j = start; j < end && j < input.length; j += 1) {
      sum += input[j];
      count += 1;
    }
    const value = Math.max(-1, Math.min(1, count ? sum / count : 0));
    out[i] = value < 0 ? value * 0x8000 : value * 0x7fff;
  }
  return out;
}

function appendPendingPcm(chunk) {
  const merged = new Int16Array(pendingPcm.length + chunk.length);
  merged.set(pendingPcm, 0);
  merged.set(chunk, pendingPcm.length);
  pendingPcm = merged;

  while (pendingPcm.length >= CHUNK_SAMPLES) {
    const frame = pendingPcm.slice(0, CHUNK_SAMPLES);
    pendingPcm = pendingPcm.slice(CHUNK_SAMPLES);
    sendPcmFrame(frame);
  }
}

function sendPcmFrame(frame) {
  if (!websocket || websocket.readyState !== WebSocket.OPEN || stopping) return;
  websocket.send(JSON.stringify({
    realtimeInput: {
      audio: {
        data: int16ToBase64(frame),
        mimeType: "audio/pcm;rate=16000"
      }
    }
  }));
}

async function startMicrophone() {
  micStream = await navigator.mediaDevices.getUserMedia({
    audio: {
      channelCount: 1,
      echoCancellation: true,
      noiseSuppression: true,
      autoGainControl: true
    }
  });

  const AudioContextClass = window.AudioContext || window.webkitAudioContext;
  captureContext = new AudioContextClass();
  await captureContext.resume();

  sourceNode = captureContext.createMediaStreamSource(micStream);
  processor = captureContext.createScriptProcessor(4096, 1, 1);
  silentGain = captureContext.createGain();
  silentGain.gain.value = 0;

  processor.onaudioprocess = event => {
    const input = event.inputBuffer.getChannelData(0);
    appendPendingPcm(downsampleTo16k(input, captureContext.sampleRate));

    let peak = 0;
    for (let i = 0; i < input.length; i += 1) peak = Math.max(peak, Math.abs(input[i]));
    liveMeterBar.style.width = Math.min(100, Math.round(peak * 180)) + "%";
  };

  sourceNode.connect(processor);
  processor.connect(silentGain);
  silentGain.connect(captureContext.destination);
}

async function stopMicrophone() {
  if (processor) processor.disconnect();
  if (sourceNode) sourceNode.disconnect();
  if (silentGain) silentGain.disconnect();
  if (micStream) micStream.getTracks().forEach(track => track.stop());
  if (captureContext) await captureContext.close();

  processor = null;
  sourceNode = null;
  silentGain = null;
  micStream = null;
  captureContext = null;
  pendingPcm = new Int16Array(0);
  liveMeterBar.style.width = "0%";
}

async function ensurePlaybackContext() {
  if (!playbackContext) {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    playbackContext = new AudioContextClass();
  }
  await playbackContext.resume();
}

async function queueTranslatedAudio(base64) {
  await ensurePlaybackContext();
  const samples = base64ToInt16(base64);
  const buffer = playbackContext.createBuffer(1, samples.length, OUTPUT_RATE);
  const channel = buffer.getChannelData(0);

  for (let i = 0; i < samples.length; i += 1) {
    channel[i] = samples[i] / 32768;
  }

  const source = playbackContext.createBufferSource();
  source.buffer = buffer;
  source.connect(playbackContext.destination);

  const now = playbackContext.currentTime;
  if (nextPlaybackTime < now + 0.025) nextPlaybackTime = now + 0.025;
  source.start(nextPlaybackTime);
  nextPlaybackTime += buffer.duration;
  activePlaybackSources += 1;

  source.onended = () => {
    activePlaybackSources = Math.max(0, activePlaybackSources - 1);
    if (stopping) scheduleFinalClose();
  };

  if (!firstAudioAt) {
    firstAudioAt = performance.now();
    firstAudioMetric.textContent = Math.round(firstAudioAt - sessionStartedAt) + " ms";
  }
}

function touchQuietTimer() {
  if (quietTimer) clearTimeout(quietTimer);
  if (stopping) scheduleFinalClose();
}

function scheduleFinalClose() {
  if (quietTimer) clearTimeout(quietTimer);
  const remainingPlayback = playbackContext
    ? Math.max(0, nextPlaybackTime - playbackContext.currentTime)
    : 0;
  const delay = Math.max(700, remainingPlayback * 1000 + 350);
  quietTimer = setTimeout(() => finalizeSession(), delay);
}

function handleGeminiMessage(event) {
  const message = JSON.parse(event.data);

  if (message.setupComplete) {
    connectionMetric.textContent = Math.round(performance.now() - sessionStartedAt) + " ms";
    setStatus("Tradução ao vivo ativa", "Fale normalmente. A voz traduzida deve começar a tocar enquanto você fala.", 100);
    startMicrophone().catch(error => {
      setStatus("Microfone indisponível", error.message, 0);
      finalizeSession();
    });
    return;
  }

  const content = message.serverContent;
  if (!content) return;

  if (content.inputTranscription?.text) {
    appendTranscript(originalText, content.inputTranscription.text);
    touchQuietTimer();
  }
  if (content.outputTranscription?.text) {
    appendTranscript(translatedText, content.outputTranscription.text);
    touchQuietTimer();
  }

  if (content.modelTurn?.parts) {
    for (const part of content.modelTurn.parts) {
      if (part.inlineData?.data) {
        queueTranslatedAudio(part.inlineData.data).catch(error => {
          setStatus("Falha na reprodução", error.message, 0);
        });
        touchQuietTimer();
      }
    }
  }

  if (content.turnComplete && stopping) scheduleFinalClose();
}

async function requestEphemeralToken(targetLanguageCode) {
  const params = new URLSearchParams({target_language_code: targetLanguageCode});
  return api("/api/gemini-live-token?" + params.toString(), {method: "POST"});
}

async function startLive(direction, button) {
  if (!canStart()) return;

  activeDirection = direction;
  activeButton = button;
  stopping = false;
  firstAudioAt = 0;
  nextPlaybackTime = 0;
  activePlaybackSources = 0;
  originalText.textContent = "—";
  translatedText.textContent = "—";
  connectionMetric.textContent = "—";
  firstAudioMetric.textContent = "—";

  const target = direction === "remote_to_local"
    ? localLanguage.value
    : remoteLanguage.value;

  directionMetric.textContent = direction === "remote_to_local"
    ? remoteLanguage.value + " → " + localLanguage.value
    : localLanguage.value + " → " + remoteLanguage.value;

  remoteButton.disabled = true;
  localButton.disabled = true;
  stopButton.disabled = false;
  button.classList.add("recording");
  button.textContent = "Ao vivo…";
  setStatus("Preparando Gemini Live", "Gerando token efêmero restrito para " + target + "…", 25);

  try {
    const tokenResponse = await requestEphemeralToken(target);
    sessionStartedAt = performance.now();
    await ensurePlaybackContext();

    const url = GEMINI_WS_BASE + "?access_token=" + encodeURIComponent(tokenResponse.token);
    websocket = new WebSocket(url);

    websocket.onopen = () => {
      websocket.send(JSON.stringify({
        setup: {
          model: "models/" + tokenResponse.model,
          generationConfig: {
            responseModalities: ["AUDIO"],
            inputAudioTranscription: {},
            outputAudioTranscription: {},
            translationConfig: {
              targetLanguageCode: target,
              echoTargetLanguage: true
            }
          }
        }
      }));
      setStatus("Conectando ao intérprete", "WebSocket aberto; aguardando confirmação do Gemini.", 55);
      updateControls();
    };

    websocket.onmessage = handleGeminiMessage;
    websocket.onerror = () => {
      setStatus("Falha no Gemini Live", "A conexão WebSocket encontrou um erro.", 0);
    };
    websocket.onclose = event => {
      if (!stopping && event.code !== 1000) {
        setStatus("Gemini Live desconectado", event.reason || ("WebSocket " + event.code), 0);
      }
      cleanupAfterClose();
    };

    updateControls();
  } catch (error) {
    setStatus("Não foi possível iniciar", error.message, 0);
    activeButton?.classList.remove("recording");
    if (activeButton) activeButton.textContent = "Iniciar tradução ao vivo";
    activeButton = null;
    activeDirection = null;
    websocket = null;
    updateControls();
  }
}

async function stopLive() {
  if (!websocket) return;
  stopping = true;
  stopButton.disabled = true;
  setStatus("Finalizando", "Encerrando o microfone e aguardando o último áudio traduzido.", 75);

  await stopMicrophone();

  if (websocket.readyState === WebSocket.OPEN) {
    websocket.send(JSON.stringify({
      realtimeInput: {
        audioStreamEnd: true
      }
    }));
  }
  scheduleFinalClose();
}

function finalizeSession() {
  if (quietTimer) {
    clearTimeout(quietTimer);
    quietTimer = null;
  }
  if (websocket && websocket.readyState <= WebSocket.OPEN) {
    websocket.close(1000, "turn finished");
  } else {
    cleanupAfterClose();
  }
}

function cleanupAfterClose() {
  stopMicrophone().catch(() => {});
  websocket = null;
  stopping = false;
  if (activeButton) {
    activeButton.classList.remove("recording");
    activeButton.textContent = "Iniciar tradução ao vivo";
  }
  activeButton = null;
  activeDirection = null;
  stopButton.disabled = true;
  setStatus("Pronto para o próximo lado", "Você pode iniciar a tradução na direção oposta.", 0);
  updateControls();
}

remoteButton.addEventListener("click", () => startLive("remote_to_local", remoteButton));
localButton.addEventListener("click", () => startLive("local_to_remote", localButton));
stopButton.addEventListener("click", () => stopLive());

window.addEventListener("beforeunload", () => {
  if (websocket) websocket.close();
  if (micStream) micStream.getTracks().forEach(track => track.stop());
});

fetch("/api/public-health")
  .then(response => {
    if (!response.ok) throw new Error("backend unavailable");
    return response.json();
  })
  .then(() => refreshHealth())
  .catch(() => {
    backendBadge.textContent = "Backend indisponível";
    backendBadge.className = "badge bad";
    setStatus("Backend indisponível", "O servidor do Codespace não respondeu.", 0);
  });
