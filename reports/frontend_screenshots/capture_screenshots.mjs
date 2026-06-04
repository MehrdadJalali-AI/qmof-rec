import { spawn } from "node:child_process";
import fs from "node:fs/promises";
import http from "node:http";
import path from "node:path";

const root = "/Users/mehrdadjalali/Documents/SRH_Research/QMOF-Rec/qmof-rec";
const outDir = path.join(root, "manuscript/figures");
const chrome =
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const userDataDir = "/private/tmp/qmof-rec-chrome-profile";
const port = 9223;
const width = 1440;
const height = 900;

function getJson(url) {
  return new Promise((resolve, reject) => {
    http
      .get(url, (res) => {
        let body = "";
        res.on("data", (chunk) => {
          body += chunk;
        });
        res.on("end", () => {
          try {
            resolve(JSON.parse(body));
          } catch (error) {
            reject(error);
          }
        });
      })
      .on("error", reject);
  });
}

function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function waitForEndpoint() {
  for (let i = 0; i < 50; i += 1) {
    try {
      return await getJson(`http://127.0.0.1:${port}/json/version`);
    } catch {
      await wait(200);
    }
  }
  throw new Error("Chrome debugging endpoint did not start.");
}

async function cdpConnect(webSocketDebuggerUrl) {
  const ws = new WebSocket(webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {
    ws.addEventListener("open", resolve, { once: true });
    ws.addEventListener("error", reject, { once: true });
  });

  let id = 0;
  const pending = new Map();

  ws.addEventListener("message", (event) => {
    const message = JSON.parse(event.data);
    if (message.id && pending.has(message.id)) {
      const { resolve, reject } = pending.get(message.id);
      pending.delete(message.id);
      if (message.error) {
        reject(new Error(message.error.message));
      } else {
        resolve(message.result);
      }
    }
  });

  function send(method, params = {}) {
    id += 1;
    ws.send(JSON.stringify({ id, method, params }));
    return new Promise((resolve, reject) => {
      pending.set(id, { resolve, reject });
    });
  }

  return { send, close: () => ws.close() };
}

async function saveScreenshot(cdp, filename) {
  await wait(700);
  const { data } = await cdp.send("Page.captureScreenshot", {
    format: "png",
    fromSurface: true,
  });
  await fs.writeFile(path.join(outDir, filename), Buffer.from(data, "base64"));
}

async function clickButton(cdp, label) {
  const expression = `
    (() => {
      const buttons = [...document.querySelectorAll("button")];
      const button = buttons.find((item) => item.textContent.trim().includes(${JSON.stringify(label)}));
      if (!button) return false;
      button.click();
      return true;
    })()
  `;
  const result = await cdp.send("Runtime.evaluate", {
    expression,
    awaitPromise: true,
    returnByValue: true,
  });
  if (!result.result.value) {
    throw new Error(`Could not find button: ${label}`);
  }
}

async function fillRecommendationQuery(cdp) {
  const expression = `
    (() => {
      const textarea = [...document.querySelectorAll("textarea")]
        .find((item) => item.placeholder.includes("CO2 adsorption"));
      if (!textarea) return false;
      textarea.focus();
      textarea.value = "stable porous MOFs for CO2 adsorption";
      textarea.dispatchEvent(new Event("input", { bubbles: true }));
      return true;
    })()
  `;
  await cdp.send("Runtime.evaluate", {
    expression,
    awaitPromise: true,
    returnByValue: true,
  });
}

await fs.mkdir(outDir, { recursive: true });

const child = spawn(chrome, [
  "--headless=new",
  "--disable-gpu",
  "--no-first-run",
  "--no-default-browser-check",
  `--remote-debugging-port=${port}`,
  `--user-data-dir=${userDataDir}`,
  `--window-size=${width},${height}`,
  "http://127.0.0.1:5173/",
]);

try {
  await waitForEndpoint();
  const pages = await getJson(`http://127.0.0.1:${port}/json`);
  const page = pages.find((item) => item.type === "page");
  const cdp = await cdpConnect(page.webSocketDebuggerUrl);

  await cdp.send("Page.enable");
  await cdp.send("Runtime.enable");
  await cdp.send("Emulation.setDeviceMetricsOverride", {
    width,
    height,
    deviceScaleFactor: 1,
    mobile: false,
  });
  await cdp.send("Page.navigate", { url: "http://127.0.0.1:5173/" });
  await wait(1800);
  await saveScreenshot(cdp, "qmof_rec_ui_dashboard.png");

  await clickButton(cdp, "Chat");
  await saveScreenshot(cdp, "qmof_rec_ui_chat.png");

  await clickButton(cdp, "Research");
  await fillRecommendationQuery(cdp);
  await saveScreenshot(cdp, "qmof_rec_ui_recommendations.png");

  await clickButton(cdp, "Analytics");
  await saveScreenshot(cdp, "qmof_rec_ui_feedback.png");

  cdp.close();
} finally {
  child.kill();
}
