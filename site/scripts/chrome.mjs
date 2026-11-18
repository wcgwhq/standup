// One headless Chrome or Chromium, driven over the DevTools protocol with Node's own WebSocket
// (Node 22+), so rendering many pages needs no dependency and no browser start per page.
//
//   const chrome = await launchChrome();           // null when no browser is installed
//   const tab = await chrome.tab(1200, 630);
//   await tab.goto(pathToFileURL('scripts/og-template.html').href);
//   await tab.evaluate('document.fonts.ready.then(() => true)'); // awaits a returned promise
//   writeFileSync('card.png', await tab.screenshot({ format: 'png' }));
//   await chrome.close();
import { spawn, spawnSync } from 'node:child_process';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';

const BROWSERS = [
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  '/Applications/Chromium.app/Contents/MacOS/Chromium',
  'google-chrome',
  'chromium',
];

export async function launchChrome() {
  const binary = BROWSERS.find((candidate) => spawnSync(candidate, ['--version']).status === 0);
  if (!binary) return null;
  const profile = mkdtempSync(path.join(tmpdir(), 'chrome-'));
  const browser = spawn(
    binary,
    [
      '--headless=new',
      '--remote-debugging-port=0',
      `--user-data-dir=${profile}`,
      '--no-first-run',
      '--no-default-browser-check',
      '--disable-gpu',
      '--hide-scrollbars',
      'about:blank',
    ],
    { stdio: ['ignore', 'ignore', 'pipe'] },
  );
  const stop = () => {
    browser.kill();
    rmSync(profile, { recursive: true, force: true, maxRetries: 5 });
  };

  // Chrome prints the address of its DevTools socket on stderr once it is up.
  const address = await new Promise((resolve, reject) => {
    let printed = '';
    browser.stderr.on('data', (chunk) => {
      printed += chunk;
      const found = printed.match(/DevTools listening on (ws:\/\/\S+)/);
      if (found) resolve(found[1]);
    });
    browser.once('exit', () => reject(new Error('Chrome closed before it was ready.')));
    setTimeout(() => reject(new Error('Chrome did not start in 20 s.')), 20_000);
  }).catch((error) => {
    stop();
    throw error;
  });

  const socket = new WebSocket(address);
  await new Promise((resolve, reject) => {
    socket.addEventListener('open', resolve, { once: true });
    socket.addEventListener('error', reject, { once: true });
  });
  let last = 0;
  const waiting = new Map(); // call id → { resolve, reject }
  const listeners = new Set(); // (event) => void
  socket.addEventListener('message', ({ data }) => {
    const message = JSON.parse(data);
    const call = waiting.get(message.id);
    if (!call) return listeners.forEach((listener) => listener(message));
    waiting.delete(message.id);
    if (message.error) call.reject(new Error(message.error.message));
    else call.resolve(message.result);
  });
  const send = (method, params = {}, sessionId) =>
    new Promise((resolve, reject) => {
      const id = ++last;
      waiting.set(id, { resolve, reject });
      socket.send(JSON.stringify({ id, method, params, sessionId }));
    });
  const next = (method, sessionId) =>
    new Promise((resolve) => {
      const listener = (event) => {
        if (event.method !== method || event.sessionId !== sessionId) return;
        listeners.delete(listener);
        resolve(event.params);
      };
      listeners.add(listener);
    });

  return {
    /** A tab `width` × `height` CSS pixels; `mobile` emulates a touch phone at `scale`× density. */
    async tab(width, height, { mobile = false, scale = 1 } = {}) {
      const { targetId } = await send('Target.createTarget', { url: 'about:blank' });
      const { sessionId } = await send('Target.attachToTarget', { targetId, flatten: true });
      const call = (method, params) => send(method, params, sessionId);
      await call('Page.enable');
      await call('Emulation.setDeviceMetricsOverride', { width, height, deviceScaleFactor: scale, mobile });
      if (mobile) await call('Emulation.setTouchEmulationEnabled', { enabled: true });
      return {
        call,
        async goto(url) {
          const loaded = next('Page.loadEventFired', sessionId);
          await call('Page.navigate', { url });
          await loaded;
        },
        /** Runs an expression in the page and returns its value; a promise is awaited. */
        async evaluate(expression) {
          const { result, exceptionDetails } = await call('Runtime.evaluate', {
            expression,
            awaitPromise: true,
            returnByValue: true,
            userGesture: true,
          });
          if (exceptionDetails)
            throw new Error(exceptionDetails.exception?.description ?? exceptionDetails.text);
          return result.value;
        },
        /** The viewport as a JPEG (or `format: 'png'`); `full` takes the whole page. */
        async screenshot({ format = 'jpeg', quality = 82, full = false } = {}) {
          const { data } = await call('Page.captureScreenshot', {
            format,
            ...(format === 'jpeg' && { quality }),
            captureBeyondViewport: full,
            ...(full && { clip: { ...(await call('Page.getLayoutMetrics')).cssContentSize, scale: 1 } }),
          });
          return Buffer.from(data, 'base64');
        },
        close: () => send('Target.closeTarget', { targetId }),
      };
    },
    async close() {
      socket.close();
      stop();
    },
  };
}
