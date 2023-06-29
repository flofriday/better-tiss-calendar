// Should we use typescript or a svelte for just this single page?

const verifyBtn = document.getElementById("verify");
const copyBtn = document.getElementById("copy");
const urlText = document.getElementById("original_url");
const betterText = document.getElementById("better_url");
const betterTextPlaceholder = document.getElementById("better_url_placeholder");
const errorText = document.getElementById("error_message");

urlText.onchange = () => {
  disableBetterUrl();
};

urlText.onkeydown = () => {
  disableBetterUrl();
};

verifyBtn.onclick = async () => {
  await verify(urlText.value);
};

async function verify(url) {
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
  errorText.classList.add("hidden");
  betterText.classList.add("hidden");
  betterTextPlaceholder.classList.remove("hidden");
  copyBtn.disabled = true;
}

function setErrorMessage(message) {
  errorText.classList.remove("hidden");
  errorText.innerText = "🔥 " + message;
}

function setBetterUrl(originalUrl) {
  errorText.classList.add("hidden");
  betterText.classList.remove("hidden");
  betterTextPlaceholder.classList.add("hidden");
  copyBtn.disabled = false;

  const tmpurl = new URL(originalUrl);
  const searchParams = new URLSearchParams(tmpurl.search);
  const token = searchParams.get("token");
  const locale = searchParams.get("locale");

  const domain = window.location.origin;
  const better_url = `${domain}/personal.ics?token=${encodeURIComponent(
    token
  )}&locale=${encodeURIComponent(locale)}`;

  betterText.innerText = better_url;
}
