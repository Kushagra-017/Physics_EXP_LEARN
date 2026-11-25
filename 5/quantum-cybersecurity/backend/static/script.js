'use strict';
const $ = (selector) => document.querySelector(selector);
const result = $('#result');
let lastRSA = null;

async function api(path, options = {}) {
  const response = await fetch(path, { ...options, headers: { 'Content-Type': 'application/json', ...(options.headers || {}) } });
  let data;
  try { data = await response.json(); } catch { throw new Error('The server returned an unexpected response.'); }
  if (!response.ok) throw new Error(data.error || 'Something went wrong.');
  return data;
}
const post = (path, data) => api(path, { method: 'POST', body: JSON.stringify(data) });
function setResult(message, kind = '') {
  result.className = `result ${kind}`;
  result.replaceChildren();
  const icon = document.createElement('span'); icon.className = 'result-icon'; icon.textContent = kind === 'error' ? '!' : '✧';
  const text = document.createElement('span'); text.textContent = message; result.append(icon, text);
}

async function runSimulation(number) {
  const button = $('#run'); button.disabled = true; button.textContent = 'Running…';
  $('#step-log').replaceChildren();
  try {
    const data = await post('/api/simulate/shor', { number });
    setResult(data.factors.length ? `${data.input_number} = ${data.factors.join(' × ')}  ·  ${data.period ? `Period r = ${data.period}, base a = ${data.base}` : 'Classical shortcut'}` : `${data.input_number} is prime. No non-trivial factors found.`, 'success');
    data.steps.forEach((step, index) => {
      const item = document.createElement('div'); item.className = 'log-step';
      const title = document.createElement('strong'); title.textContent = `${String(index + 1).padStart(2, '0')} / ${step.stage}`;
      const description = document.createElement('span'); description.textContent = step.description;
      item.append(title, description); $('#step-log').append(item);
    });
    await loadHistory();
  } catch (error) { setResult(error.message, 'error'); }
  finally { button.disabled = false; button.innerHTML = 'Run simulation <span>→</span>'; }
}
$('#run').addEventListener('click', () => {
  const value = $('#number').value;
  if (!value || !Number.isInteger(Number(value)) || Number(value) < 2 || Number(value) > 999) return setResult('Enter a whole number from 2 to 999.', 'error');
  runSimulation(Number(value));
});

async function loadHistory() {
  const list = $('#history-list');
  try {
    const { simulations } = await api('/api/history');
    list.replaceChildren();
    if (!simulations.length) {
      const empty = document.createElement('div'); empty.className = 'empty-history';
      const icon = document.createElement('span'); icon.textContent = '◷';
      const text = document.createElement('div'); const title = document.createElement('strong'); title.textContent = 'No simulations yet';
      const hint = document.createElement('p'); hint.textContent = 'Run your first simulation to see it here.'; text.append(title, hint); empty.append(icon, text); list.append(empty); return;
    }
    simulations.forEach(entry => {
      const row = document.createElement('div'); row.className = 'history-row';
      const icon = document.createElement('span'); icon.className = 'history-factor'; icon.textContent = '✧';
      const title = document.createElement('strong'); title.textContent = `N = ${entry.input_number}`;
      const factor = document.createElement('span'); factor.className = 'history-factor'; factor.textContent = entry.factors.length ? entry.factors.join(' × ') : 'No factors';
      const algorithm = document.createElement('span'); algorithm.textContent = entry.algorithm;
      const time = document.createElement('time'); time.textContent = `${entry.timestamp} UTC`;
      row.append(icon, title, factor, algorithm, time); list.append(row);
    });
  } catch (error) { list.textContent = `Could not load history: ${error.message}`; }
}
$('#refresh').addEventListener('click', loadHistory);
$('#encrypt').addEventListener('click', async () => {
  const output = $('#rsa-result'); output.textContent = 'Generating keys…'; $('#decrypt').classList.add('hidden');
  try {
    lastRSA = await post('/api/encrypt/rsa', { message: $('#message').value });
    output.textContent = `p = ${lastRSA.p}, q = ${lastRSA.q} → n = ${lastRSA.public_key.n}; φ(n) = ${lastRSA.phi}. Public key (e, n) = (${lastRSA.public_key.e}, ${lastRSA.public_key.n}); private d = ${lastRSA.private_key.d}. Ciphertext: [${lastRSA.ciphertext.join(', ')}]. Toy RSA only; never use for security.`;
    $('#decrypt').classList.remove('hidden');
    if (lastRSA.public_key.n <= 999) {
      const attack = document.createElement('button'); attack.className = 'text-button'; attack.textContent = 'Factor this public modulus in the simulator →';
      attack.addEventListener('click', () => { $('#number').value = lastRSA.public_key.n; location.hash = 'simulator'; runSimulation(lastRSA.public_key.n); });
      output.append(document.createElement('br'), attack);
    }
  } catch (error) { lastRSA = null; output.textContent = error.message; }
});
$('#decrypt').addEventListener('click', async () => {
  if (!lastRSA) return;
  try { const data = await post('/api/decrypt/rsa', { ciphertext: lastRSA.ciphertext, private_key: lastRSA.private_key }); $('#rsa-result').append(document.createTextNode(` Decrypted: ${data.message}`)); }
  catch (error) { $('#rsa-result').append(document.createTextNode(` ${error.message}`)); }
});

// A one-dimensional, tiny noisy arithmetic analogy. It is NOT a real KEM or secure lattice cryptography.
$('#exchange').addEventListener('click', () => {
  const random = max => { const a = new Uint32Array(1); crypto.getRandomValues(a); return a[0] % max; };
  const mod = x => ((x % 97) + 97) % 97;
  const a = 17, s = random(3) + 1, t = random(3) + 1, e = random(3) - 1, e1 = random(3) - 1, e2 = random(3) - 1, bit = random(2);
  const b = mod(a * s + e), u = mod(a * t + e1), v = mod(b * t + e2 + 48 * bit);
  const recovered = mod(v - s * u), decoded = recovered >= 24 && recovered < 73 ? 1 : 0;
  $('#exchange-result').textContent = `Toy noisy-arithmetic analogy (not a secure key exchange): Alice publishes (a, b) = (${a}, ${b}); Bob sends (u, v) = (${u}, ${v}), encoding bit ${bit}. Alice uses her secret to recover ${decoded}. Real lattice KEMs use high-dimensional structures and standardized parameters; hash-based schemes are generally signatures, not key exchange.`;
});

api('/api/health').then(data => { $('#server-status').textContent = data.storage === 'ephemeral' ? 'Online · temporary history' : 'All systems operational'; }).catch(() => { $('#server-status').textContent = 'Backend unavailable'; });
loadHistory();
const links = document.querySelectorAll('.nav-link');
links.forEach(link => link.addEventListener('click', () => { links.forEach(item => item.classList.remove('active')); link.classList.add('active'); }));
