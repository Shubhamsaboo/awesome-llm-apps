"use strict";

const STORAGE_KEY = "savedSentences";
const form = document.querySelector("#note-form");
const input = document.querySelector("#note-input");
const saveButton = document.querySelector("#save-button");
const status = document.querySelector("#status");
const retryButton = document.querySelector("#retry-button");
const list = document.querySelector("#note-list");
const count = document.querySelector("#note-count");
const emptyState = document.querySelector("#empty-state");

let notes = [];
let ready = false;
let busy = false;

function showStatus(message, tone = "success") {
  status.textContent = message;
  status.dataset.tone = tone;
}

function setBusy(value) {
  busy = value;
  input.disabled = value || !ready;
  saveButton.disabled = value || !ready;
  retryButton.disabled = value;
  list.querySelectorAll("button").forEach((button) => {
    button.disabled = value || !ready;
  });
}

function renderNotes() {
  list.replaceChildren();
  count.textContent = `${notes.length} 句`;
  emptyState.hidden = notes.length > 0;

  notes.forEach((note, index) => {
    const item = document.createElement("li");
    item.className = "note";

    const content = document.createElement("p");
    content.className = "note-text";
    content.textContent = note.text;

    const actions = document.createElement("div");
    actions.className = "note-actions";
    const copyButton = document.createElement("button");
    copyButton.type = "button";
    copyButton.className = "text-button";
    copyButton.textContent = "复制";
    copyButton.setAttribute("aria-label", `复制第 ${index + 1} 句`);
    copyButton.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(note.text);
        showStatus("已复制，可以粘贴到别处了。");
      } catch {
        showStatus("复制失败，请选中文字后手动复制。", "error");
      }
    });

    const deleteButton = document.createElement("button");
    deleteButton.type = "button";
    deleteButton.className = "text-button delete-button";
    deleteButton.textContent = "删除";
    deleteButton.setAttribute("aria-label", `删除第 ${index + 1} 句`);
    deleteButton.addEventListener("click", async () => {
      if (busy || !ready) return;
      const saved = await persistNotes(notes.filter((entry) => entry.id !== note.id));
      if (saved) {
        showStatus("已删除这句话。");
        const nextButton = list.children[index]?.querySelector("button")
          || list.lastElementChild?.querySelector("button");
        (nextButton || input).focus();
      }
    });

    actions.append(copyButton, deleteButton);
    item.append(content, actions);
    list.append(item);
  });
}

async function persistNotes(nextNotes) {
  setBusy(true);
  try {
    await chrome.storage.local.set({ [STORAGE_KEY]: nextNotes });
    notes = nextNotes;
    renderNotes();
    return true;
  } catch {
    showStatus("保存失败，原有句子仍保留，请稍后重试。", "error");
    return false;
  } finally {
    setBusy(false);
  }
}

async function loadNotes() {
  setBusy(true);
  retryButton.hidden = true;
  showStatus("正在读取已保存的句子……");
  try {
    const stored = await chrome.storage.local.get(STORAGE_KEY);
    const value = stored[STORAGE_KEY] ?? [];
    if (!Array.isArray(value) || !value.every((note) =>
      note && typeof note.id === "string" && typeof note.text === "string")) {
      throw new Error("Unrecognized saved data");
    }
    notes = value;
    ready = true;
    renderNotes();
    showStatus(notes.length ? "句子都在，想用时可以复制。" : "保存后，下次打开还能看到。");
  } catch {
    ready = false;
    retryButton.hidden = false;
    showStatus("暂时读不到已保存的句子，请重新读取。", "error");
  } finally {
    setBusy(false);
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (busy || !ready) return;
  const text = input.value.trim();
  if (!text) {
    showStatus("先写下一句话再保存吧。", "error");
    input.focus();
    return;
  }
  const saved = await persistNotes([{ id: crypto.randomUUID(), text }, ...notes]);
  if (saved) {
    input.value = "";
    showStatus("已保存，下次打开还能看到。");
  }
  input.focus();
});

retryButton.addEventListener("click", loadNotes);
loadNotes();
