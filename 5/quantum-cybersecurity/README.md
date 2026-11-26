# Quantum Cybersecurity: Quantum Lab

An interactive, small-number teaching lab about the impact of quantum computing on RSA and the ideas behind post-quantum cryptography. Flask serves a vanilla HTML/CSS/JavaScript frontend and a SQLite-backed API.

> **Educational use only.** This is not a quantum computer or a security product. The Shor-inspired demo finds a multiplicative order **classically**; the circuit and quantum steps are conceptual. Textbook RSA uses tiny keys and no padding. The noisy-arithmetic exchange is a one-dimensional analogy, not ML-KEM or secure post-quantum cryptography. Never use any of these for real secrets.

## Run on Windows

On a Windows 10/11 **64-bit x64** PC with no Python installed, download or copy the entire project folder to a writable location, then double-click **`setup-windows.bat`**. It downloads the official Python 3.12.10 installer from python.org, checks its Windows digital signature, and installs Python into the project's `.python` directory (not system-wide). It then runs `start.bat`, which creates `.venv`, installs the dependencies, starts Waitress on port 5000, and opens the browser. Initial setup needs an internet connection to python.org and PyPI, and Windows PowerShell. No administrator access should be necessary in a writable folder. If download, signature verification, or installation fails, the script displays an error instead of executing an unverified download.

For subsequent runs, double-click `start.bat`; it automatically uses the local Python installation. Close the server window to stop it. If a compatible Python 3.10+ is already available on PATH, the setup script uses it instead. On non-x64 Windows, install a compatible Python 3.10+ manually from python.org and use `start.bat`. Keep `.python` and `.venv` with the project, or rerun setup if they are removed or the project is moved (virtual environments may need to be recreated after a move).

## Run on macOS / Linux

```sh
cd 5/quantum-cybersecurity
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cd backend
python -m waitress --listen=0.0.0.0:5000 app:app
# Visit http://localhost:5000
```

For development, run `DEBUG=1 python app.py` from `backend` instead. `PORT` defaults to 5000 for development. Waitress's listen port is set via its command-line option. `FLASK_ENV=development` also enables debug mode; do not enable it in production. `SECRET_KEY` can be set in the environment; the app does not use login sessions. `DATABASE_PATH` sets the SQLite file path; the default is `backend/simulations.sqlite3`. `CORS_ORIGINS` is an optional comma-separated list of exact allowed origins (same-origin is preferred). Request bodies are limited and validated. Deploy behind TLS and a reverse proxy with rate limiting for public use; this teaching service has no authentication and history is shared by all visitors.

## How it works

Enter a number from 2 to 999. The backend checks for primes and even numbers, then classically searches the multiplicative order of coprime bases. If an even order yields nontrivial gcds, it returns the factors. Some inputs use a clearly labeled classical divisibility fallback. Shor's actual quantum subroutine estimates the period probabilistically using quantum operations and measurement; this app does not implement a quantum state or simulate measurement. A resulting pair is not necessarily prime.

In RSA vs. Quantum, generate toy RSA keys and encrypt a UTF-8 message, then decrypt it. If the randomly generated modulus fits the simulator's input range, use the factor button to send it to the simulator. In Post-Quantum Cryptography, explore a tiny noisy-arithmetic analogy inspired by lattice schemes. Hash-based cryptography is primarily used for signatures. The activity section displays the latest 20 saved simulations.

## API

All requests and responses use JSON. Invalid input returns `400` with an `error` field.

- `GET /api/health` — server status and storage mode.
- `POST /api/simulate/shor` — `{ "number": 15 }`; saves and returns the result, factors and step log.
- `POST /api/encrypt/rsa` — `{ "message": "Hello" }`; returns ciphertext, public and private toy keys, and parameters.
- `POST /api/decrypt/rsa` — `{ "ciphertext": [ ... ], "private_key": { "d": 123, "n": 323 } }`.
- `GET /api/history` — latest 20 entries.
- `POST /api/history` — `{ "input_number": 15, "factors": [3, 5], "algorithm": "Manual", "details": {} }`. The simulation endpoint saves through the same database function internally.

## Vercel

The included `api/index.py`, root `requirements.txt`, and `vercel.json` support deploying this directory as a Vercel Python app. **Vercel's filesystem is ephemeral**: SQLite is stored in `/tmp` there, is not shared reliably across function instances, and can disappear at any time. The history dashboard is therefore only best-effort on Vercel. Use a durable hosted database and appropriate access controls before relying on history; the local Waitress setup uses persistent SQLite. Vercel may also protect deployment URLs depending on team settings.

## Visual guide / screenshot description

The overview shows a dark cyber-themed workspace with a teal quantum-orbit illustration. The simulator card contains a number input, four-step circuit diagram and results log. To its right are RSA comparison and post-quantum cards. A history panel sits beneath the cards. On small screens, navigation and cards reflow for mobile.

## Tests

From the project directory, run `python -m unittest discover -s tests` after installing dependencies. Tests use a temporary SQLite database.
