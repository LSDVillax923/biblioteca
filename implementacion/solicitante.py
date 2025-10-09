# ps.py
import zmq
import sys
import time
import json

def run(ps_name, requests_file, gc_host="localhost", gc_port=5555, delay=0.2):
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect(f"tcp://{gc_host}:{gc_port}")  # conecta al GC (REP)
    print(f"[PS {ps_name}] conectado a GC tcp://{gc_host}:{gc_port}")

    with open(requests_file, "r") as f:
        lines = [l.strip() for l in f if l.strip()]

    for line in lines:
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 3:
            continue
        tipo, code, user = parts[0].lower(), parts[1], parts[2]
        payload = {
            "ps": ps_name,
            "type": tipo,
            "book_code": code,
            "user_id": user,
            "ts": time.time()
        }
        msg = json.dumps(payload)
        print(f"[PS {ps_name}] Enviando -> {msg}")
        socket.send_string(msg)
        # espera la respuesta del Gestor
        reply = socket.recv_string()
        print(f"[PS {ps_name}] Respuesta GC -> {reply}")
        time.sleep(delay)

if __name__ == "__main__":
    # el argumento 1 es el nombre del PS, el 2 el archivo de solicitudes para hacer la carga
    # el 3 el host del Gestor y el 4 el puerto del REQ Configurado en el Gestor
    if len(sys.argv) < 3:
        print("Uso: python ps.py <PS_NAME> <requests_file> [gc_host] [gc_port]")
        sys.exit(1)
    ps_name = sys.argv[1]
    requests_file = sys.argv[2]
    gc_host = sys.argv[3] if len(sys.argv) > 3 else "localhost"
    gc_port = int(sys.argv[4]) if len(sys.argv) > 4 else 5555
    run(ps_name, requests_file, gc_host, gc_port)
