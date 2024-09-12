// Should we use typescript or a svelte for just this single page?

const verifyBtn = document.getElementById("verify");
const copyBtn = document.getElementById("copy");
const urlText = document.getElementById("original_url");
const betterText = document.getElementById("better_url");
const betterTextPlaceholder = document.getElementById("better_url_placeholder");
const errorText = document.getElementById("error_message");
const copyText = document.getElementById("copy_feedback");
const googleCheck = document.getElementById("is_google");
const noShorthandCheck = document.getElementById("no_shorthand");
const previewTitle = document.getElementById("preview-title");
const previewLectureName = document.getElementById("preview-lecturename");
const importTip = document.getElementById("import-tip");

let isDisabled = true;
let currentUrl = "";

window.onload = () => {
  copyBtn.disabled = true;
};

urlText.onchange = () => {
  disableBetterUrl();
};

urlText.onkeydown = () => {
  disableBetterUrl();
};

verifyBtn.onclick = async () => {
  await verify();
};

googleCheck.onchange = () => {
  if (isDisabled) return;
  setBetterUrl(currentUrl);
};

noShorthandCheck.onchange = () => {
  if (noShorthandCheck.checked) {
    previewTitle.innerText = "Einführung in die Programmierung 1 VU";
  } else {
    previewTitle.innerText = "EP1 VU";
  }
  previewLectureName.hidden = noShorthandCheck.checked;

  if (isDisabled) return;
  setBetterUrl(currentUrl);
};

copyBtn.onclick = () => {
  if (copyBtn.disabled) return;

  text = betterText.innerText;
  navigator.clipboard.writeText(text);

  copyText.classList.remove("flyaway");
  setTimeout(function () {
    copyText.classList.add("flyaway");
  }, 1);
};

async function verify(url) {
  url = urlText.value
    .trim()
    .replace(/Download$/, "")
    .trim();

  urlText.value = url;
  currentUrl = url;
  try {
    const response = await fetch(`/verify?url=${encodeURIComponent(url)}`);
    if (response.ok) {
      setBetterUrl(url);
    } else {
      let message = await response.text();
      if (message.trim().length > 0) {
        setErrorMessage(message);
      } else {
        setErrorMessage("Server returned: " + response.statusText);
      }
    }
  } catch (error) {
    setErrorMessage("Could not connect to the server: " + error);
  }
}

function disableBetterUrl() {
  isDisabled = true;
  errorText.classList.add("invisible");
  betterText.classList.add("hidden");
  betterTextPlaceholder.classList.remove("hidden");
  importTip.classList.add("invisible");
  copyBtn.disabled = true;
}

function setErrorMessage(message) {
  errorText.classList.remove("invisible");
  errorText.innerText = "🔥 " + message;
}

function setBetterUrl(originalUrl) {
  isDisabled = false;
  errorText.classList.add("invisible");
  betterText.classList.remove("hidden");
  betterTextPlaceholder.classList.add("hidden");
  importTip.classList.remove("invisible");
  copyBtn.disabled = false;

  const tmpurl = new URL(originalUrl);
  const searchParams = new URLSearchParams(tmpurl.search);
  const token = searchParams.get("token");
  const locale = searchParams.get("locale");

  const domain = window.location.origin;
  let betterUrl = `${domain}/personal.ics?token=${encodeURIComponent(
    token,
  )}&locale=${encodeURIComponent(locale)}`;
  if (googleCheck.checked) {
    betterUrl += "&google";
  }
  if (noShorthandCheck.checked) {
    betterUrl += "&noshorthand";
  }

  betterText.innerText = betterUrl;
}
