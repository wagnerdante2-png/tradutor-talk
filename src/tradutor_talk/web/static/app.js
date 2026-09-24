const remoteButton = document.getElementById("remoteButton");
const localButton = document.getElementById("localButton");
const resetButton = document.getElementById("resetButton");
const saveKeyButton = document.getElementById("saveKey");
const apiKeyInput = document.getElementById("apiKey");
const keyPanel = document.getElementById("keyPanel");
const backendBadge = document.getElementById("backendBadge");
const localLanguage = document.getElementById("localLanguage");
const remoteLanguage = document.getElementById("remoteLanguage");
const statusText = document.getElementById("statusText");
const statusDetail = document.getElementById("statusDetail");
const progressBar = document.getElementById("progressBar");
const originalText = document.getElementById("originalText");
const translatedText = document.getElementById("translatedText");
const sttMetric = document.getElementById("sttMetric");
const translationMetric = document.getElementById("translationMetric");
const ttsMetric = document.getElementById("ttsMetric");
const totalMetric = document.getElementById("totalMetric");
const translatedAudio = document.getElementById("translatedAudio");
const contextInfo = document.getElementById("contextInfo");

let stream = null;
let recorder = null;
let chunks = [];
let activeDirection = null;
let activeButton = null;
let currentUtteranceId = null;
let lastAudioUrl = null;

function setStatus(title, detail, progress) {
  statusText.textContent = title;
  statusDetail.textContent = detail || "";
  progressBar.style.width = String(progress || 0) + "%";
}

function setButtonsDisabled(disabled) {
  remoteButton.disabled = disabled;
  localButton.disabled = disabled;
}

function formatMs(value) {
  if (value === undefined || value === null) return "—";
  return Math.round(value) + " ms";
}

async function api(path, options) {
  const response = await fetch(path, options || {});
  let payload = {};
  try {
    payload = await response.json();
  } catch (_) {
    payload = {};
  }
  if (!response.ok) {
    throw new Error(payload.detail || ("HTTP " + response.status));
  }
  return payload;
}

async function refreshHealth() {
  try {
    const health = await api("/api/health");
    backendBadge.textContent = "Codespace online · " + health.state;
    backendBadge.className = "badge ok";
    keyPanel.classList.toggle("hidden", health.api_key_configured);
    contextInfo.textContent = "Contexto: " + health.context_turns + " turnos";
  } catch (error) {
    backendBadge.textContent = "Backend indisponível";
    backendBadge.className = "badge bad";
    setStatus("Backend indisponível", error.message, 0);
  }
}

saveKeyButton.addEventListener("click", async () => {
  const value = apiKeyInput.value.trim();
  if (!value) return;
  saveKeyButton.disabled = true;
  try {
    await api("/api/session-key", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({api_key: value})
    });
    apiKeyInput.value = "";
    keyPanel.classList.add("hidden");
    setStatus("Chave carregada", "Ela existe somente na memória desta sessão do Codespace.", 0);
    await refreshHealth();
  } catch (error) {
    setStatus("Não foi possível carregar a chave", error.message, 0);
  } finally {
    saveKeyButton.disabled = false;
  }
});

async function startRecording(direction, button) {
  if (recorder) return;

  try {
    stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true
      }
    });

    chunks = [];
    const options = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
      ? {mimeType: "audio/webm;codecs=opus"}
      : undefined;
    recorder = options ? new MediaRecorder(stream, options) : new MediaRecorder(stream);
    activeDirection = direction;
    activeButton = button;

    recorder.addEventListener("dataavailable", event => {
      if (event.data && event.data.size) chunks.push(event.data);
    });

    recorder.start(250);
    setButtonsDisabled(true);
    button.disabled = false;
    button.classList.add("recording");
    button.textContent = "Parar e traduzir";
    setStatus(
      direction === "remote_to_local" ? "Ouvindo o interlocutor" : "Ouvindo você",
      "Fale normalmente e clique em parar ao terminar a frase.",
      18
    );
  } catch (error) {
    setStatus("Microfone indisponível", error.message, 0);
    cleanupRecorder();
  }
}

function cleanupRecorder() {
  if (stream) {
    stream.getTracks().forEach(track => track.stop());
  }
  stream = null;
  recorder = null;
  chunks = [];
  if (activeButton) {
    activeButton.classList.remove("recording");
    activeButton.textContent = "Iniciar gravação";
  }
  activeButton = null;
  activeDirection = null;
  setButtonsDisabled(false);
}

function writeString(view, offset, value) {
  for (let i = 0; i < value.length; i += 1) {
    view.setUint8(offset + i, value.charCodeAt(i));
  }
}

function encodeWav(samples, sampleRate) {
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);

  writeString(view, 0, "RIFF");
  view.setUint32(4, 36 + samples.length * 2, true);
  writeString(view, 8, "WAVE");
  writeString(view, 12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  writeString(view, 36, "data");
  view.setUint32(40, samples.length * 2, true);

  let offset = 44;
  for (let i = 0; i < samples.length; i += 1) {
    const clamped = Math.max(-1, Math.min(1, samples[i]));
    view.setInt16(offset, clamped < 0 ? clamped * 0x8000 : clamped * 0x7fff, true);
    offset += 2;
  }
  return buffer;
}

async function recordedBlobToWav(blob) {
  const AudioContextClass = window.AudioContext || window.webkitAudioContext;
  const context = new AudioContextClass();
  try {
    const arrayBuffer = await blob.arrayBuffer();
    const decoded = await context.decodeAudioData(arrayBuffer.slice(0));
    const length = decoded.length;
    const mono = new Float32Array(length);

    for (let channel = 0; channel < decoded.numberOfChannels; channel += 1) {
      const source = decoded.getChannelData(channel);
      for (let i = 0; i < length; i += 1) {
        mono[i] += source[i] / decoded.numberOfChannels;
      }
    }

    return new Blob([encodeWav(mono, decoded.sampleRate)], {type: "audio/wav"});
  } finally {
    await context.close();
  }
}

function base64ToBlob(base64, mediaType) {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i);
  return new Blob([bytes], {type: mediaType || "audio/wav"});
}

async function finishServerPlayback(utteranceId) {
  await api("/api/playback-finished", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({utterance_id: utteranceId})
  });
  currentUtteranceId = null;
  setButtonsDisabled(false);
  setStatus("Pronto para o próximo turno", "O contexto da conversa foi preservado.", 0);
  await refreshHealth();
}

async function failServerPlayback(utteranceId, message) {
  try {
    await api("/api/playback-failed", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({utterance_id: utteranceId})
    });
  } catch (_) {}
  currentUtteranceId = null;
  setButtonsDisabled(false);
  setStatus("Falha na reprodução", message, 0);
}

async function sendTurn(wavBlob, direction) {
  const source = direction === "remote_to_local" ? remoteLanguage.value : localLanguage.value;
  const target = direction === "remote_to_local" ? localLanguage.value : remoteLanguage.value;

  setButtonsDisabled(true);
  setStatus("Processando no Codespace", "STT → tradução → TTS", 54);

  const query = new URLSearchParams({
    direction: direction,
    source_language: source,
    target_language: target
  });

  const result = await api("/api/turn?" + query.toString(), {
    method: "POST",
    headers: {"Content-Type": "audio/wav"},
    body: wavBlob
  });

  currentUtteranceId = result.utterance_id;
  originalText.textContent = result.original_text || "—";
  translatedText.textContent = result.translated_text || "—";
  sttMetric.textContent = formatMs(result.stage_latency_ms.stt);
  translationMetric.textContent = formatMs(result.stage_latency_ms.translation);
  ttsMetric.textContent = formatMs(result.stage_latency_ms.tts);
  totalMetric.textContent = formatMs(result.processing_ms);

  if (lastAudioUrl) URL.revokeObjectURL(lastAudioUrl);
  const outputBlob = base64ToBlob(result.audio_base64, result.audio_media_type);
  lastAudioUrl = URL.createObjectURL(outputBlob);
  translatedAudio.src = lastAudioUrl;

  translatedAudio.onended = () => {
    finishServerPlayback(result.utterance_id).catch(error => {
      setStatus("Erro ao fechar o turno", error.message, 0);
    });
  };
  translatedAudio.onerror = () => {
    failServerPlayback(result.utterance_id, "O navegador não conseguiu reproduzir o WAV traduzido.");
  };

  setStatus("Tradução pronta", "Reproduzindo a voz traduzida…", 88);
  try {
    await translatedAudio.play();
  } catch (_) {
    setStatus(
      "Tradução pronta",
      "O Chrome bloqueou autoplay. Clique em reproduzir no controle de áudio; o turno será fechado ao terminar.",
      88
    );
  }
}

async function stopAndTranslate() {
  if (!recorder || recorder.state === "inactive") return;

  const direction = activeDirection;
  const button = activeButton;

  const stopped = new Promise(resolve => {
    recorder.addEventListener("stop", resolve, {once: true});
  });
  recorder.stop();
  await stopped;

  const blob = new Blob(chunks, {type: recorder.mimeType || "audio/webm"});
  if (stream) stream.getTracks().forEach(track => track.stop());
  stream = null;
  recorder = null;
  chunks = [];

  if (button) {
    button.classList.remove("recording");
    button.textContent = "Iniciar gravação";
  }
  activeButton = null;
  activeDirection = null;

  try {
    setStatus("Preparando áudio", "Convertendo a gravação do navegador para WAV em memória.", 34);
    const wavBlob = await recordedBlobToWav(blob);
    await sendTurn(wavBlob, direction);
  } catch (error) {
    setButtonsDisabled(false);
    setStatus("Falha no turno", error.message, 0);
    await refreshHealth();
  }
}

remoteButton.addEventListener("click", () => {
  if (recorder && activeDirection === "remote_to_local") {
    stopAndTranslate();
  } else {
    startRecording("remote_to_local", remoteButton);
  }
});

localButton.addEventListener("click", () => {
  if (recorder && activeDirection === "local_to_remote") {
    stopAndTranslate();
  } else {
    startRecording("local_to_remote", localButton);
  }
});

resetButton.addEventListener("click", async () => {
  cleanupRecorder();
  try {
    await api("/api/reset", {method: "POST"});
    currentUtteranceId = null;
    originalText.textContent = "—";
    translatedText.textContent = "—";
    sttMetric.textContent = "—";
    translationMetric.textContent = "—";
    ttsMetric.textContent = "—";
    totalMetric.textContent = "—";
    translatedAudio.removeAttribute("src");
    translatedAudio.load();
    setStatus("Sessão resetada", "Contexto limpo. Pronto para uma nova conversa.", 0);
    await refreshHealth();
  } catch (error) {
    setStatus("Falha ao resetar", error.message, 0);
  }
});

window.addEventListener("beforeunload", () => {
  if (stream) stream.getTracks().forEach(track => track.stop());
});

refreshHealth();
