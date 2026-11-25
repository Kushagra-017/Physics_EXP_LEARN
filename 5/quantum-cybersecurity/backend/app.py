"""A small-number cryptography teaching lab; never use its keys for real data."""
import logging
import math
import os
import secrets
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory
from werkzeug.exceptions import HTTPException
import database

ROOT = Path(__file__).resolve().parent
app = Flask(__name__, static_folder=str(ROOT / "static"), static_url_path="/static")
app.config.update(SECRET_KEY=os.environ.get("SECRET_KEY", "educational-only-not-a-session-secret"), MAX_CONTENT_LENGTH=16384)
logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))


@app.after_request
def security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
    origin = request.headers.get("Origin")
    allowed = [x.strip() for x in os.environ.get("CORS_ORIGINS", "").split(",") if x.strip()]
    if origin and origin in allowed:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


@app.errorhandler(Exception)
def handle_error(error):
    if isinstance(error, HTTPException):
        return jsonify(error=error.description), error.code
    app.logger.exception("Unhandled request error")
    return jsonify(error="An internal error occurred."), 500


def body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValueError("Expected a JSON object.")
    return data


def integer(value, name, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer between {low} and {high}.")
    return value


@app.errorhandler(ValueError)
def bad_input(error):
    return jsonify(error=str(error)), 400


def is_prime(n):
    return n >= 2 and all(n % i for i in range(2, math.isqrt(n) + 1))


def simulate(n):
    """Classically find orders for Shor's reduction; no quantum state is simulated."""
    steps = [{"stage": "Superposition", "description": "A quantum computer would prepare a superposition of exponent values. Here we describe this step, not simulate qubits."}]
    if is_prime(n):
        steps.append({"stage": "Result", "description": f"{n} is prime; no non-trivial factors exist."})
        return {"input_number": n, "factors": [], "steps": steps, "status": "prime", "base": None, "period": None}
    if n % 2 == 0:
        steps.append({"stage": "Classical shortcut", "description": "The number is even, so 2 is an immediate factor; no quantum circuit is needed."})
        return {"input_number": n, "factors": [2, n // 2], "steps": steps, "status": "factored", "base": None, "period": None}
    # Try coprime bases first to make the period-finding demonstration informative.
    for a in range(2, n):
        if math.gcd(a, n) != 1:
            continue
        value, sequence = 1, []
        for r in range(1, n + 1):
            value = value * a % n
            sequence.append(value)
            if value == 1:
                break
        if r % 2 or pow(a, r // 2, n) == n - 1:
            continue
        x = pow(a, r // 2, n)
        candidates = [math.gcd(x - 1, n), math.gcd(x + 1, n)]
        factor = next((f for f in candidates if 1 < f < n), None)
        if factor:
            factors = sorted([factor, n // factor])
            steps.extend([
                {"stage": "Modular exponentiation", "description": f"For base a = {a}, the values aˣ mod {n} repeat: {', '.join(map(str, sequence[:20]))}{'…' if len(sequence) > 20 else ''}."},
                {"stage": "Quantum Fourier transform", "description": "In Shor's algorithm, the QFT reveals information about the period. This demo computes that period classically."},
                {"stage": "Measurement", "description": f"A real quantum measurement is probabilistic. Our classical period search found r = {r}."},
                {"stage": "Classical post-processing", "description": f"gcd({a}^({r}/2) ± 1, {n}) gives non-trivial factors {factors[0]} and {factors[1]}."}])
            return {"input_number": n, "factors": factors, "steps": steps, "status": "factored", "base": a, "period": r}
    # Some composites (e.g. odd prime powers) do not yield a useful order.
    factor = next(i for i in range(2, math.isqrt(n) + 1) if n % i == 0)
    steps.append({"stage": "Classical shortcut", "description": f"No useful order was found among the bases tried. Classical divisibility finds {factor} × {n // factor}; this is not a quantum result."})
    return {"input_number": n, "factors": [factor, n // factor], "steps": steps, "status": "factored", "base": None, "period": None}


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/api/health")
def health():
    return jsonify(status="ok", storage="ephemeral" if os.environ.get("VERCEL") else "sqlite")


@app.post("/api/simulate/shor")
def shor():
    n = integer(body().get("number"), "number", 2, 999)
    result = simulate(n)
    result["id"] = database.save_simulation(n, result["factors"], "Shor-inspired", result)
    return jsonify(result)


@app.get("/api/history")
def history():
    return jsonify(simulations=database.get_history())


@app.post("/api/history")
def add_history():
    data = body()
    n = integer(data.get("input_number"), "input_number", 2, 999)
    factors = data.get("factors")
    if not isinstance(factors, list) or len(factors) > 2 or any(type(x) is not int or x < 2 or x > 999 for x in factors):
        raise ValueError("factors must be a list of at most two small integers.")
    if factors and (len(factors) != 2 or factors[0] * factors[1] != n):
        raise ValueError("factors must multiply to input_number.")
    algorithm = data.get("algorithm", "Manual")
    details = data.get("details", {})
    if not isinstance(algorithm, str) or not 1 <= len(algorithm) <= 50 or not isinstance(details, dict):
        raise ValueError("Invalid algorithm or details.")
    return jsonify(id=database.save_simulation(n, factors, algorithm, details)), 201


@app.post("/api/encrypt/rsa")
def encrypt():
    data = body()
    message = data.get("message")
    if not isinstance(message, str) or not 1 <= len(message.encode('utf-8')) <= 128:
        raise ValueError("message must be 1–128 UTF-8 bytes.")
    # Deliberately tiny, unpadded textbook RSA, with one byte per block.
    primes = [17, 19, 23, 29, 31, 37, 41, 43, 47]
    p, q = secrets.SystemRandom().sample(primes, 2)
    n, phi = p*q, (p-1)*(q-1)
    e = next(v for v in (17, 5, 3, 7, 11, 13) if math.gcd(v, phi) == 1)
    d = pow(e, -1, phi)
    return jsonify(ciphertext=[pow(b, e, n) for b in message.encode('utf-8')], public_key={"e": e, "n": n}, private_key={"d": d, "n": n}, p=p, q=q, phi=phi, warning="Toy textbook RSA without padding; never use for security.")


@app.post("/api/decrypt/rsa")
def decrypt():
    data = body()
    key, cipher = data.get("private_key"), data.get("ciphertext")
    if not isinstance(key, dict) or not isinstance(cipher, list) or not 1 <= len(cipher) <= 128:
        raise ValueError("Provide private_key and a ciphertext list of 1–128 integers.")
    n = integer(key.get("n"), "n", 256, 100000)
    d = integer(key.get("d"), "d", 1, 100000)
    values = [pow(integer(c, "ciphertext item", 0, n - 1), d, n) for c in cipher]
    try:
        message = bytes(values).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        raise ValueError("The key and ciphertext do not decode to a UTF-8 message.")
    return jsonify(message=message)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=os.environ.get("DEBUG", "").lower() in ("1", "true", "yes") or os.environ.get("FLASK_ENV") == "development")
