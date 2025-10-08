# actor.py
import zmq
import sqlite3
import json
import sys
from datetime import datetime, timedelta

DB = "library.db"

def handle_devolucion(data):
    code = data.get("book_code")
    user = data.get("user_id")
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    # eliminar loan si existe (asumimos que hay un prestamo para ese usuario+libro)
    c.execute("SELECT loan_id FROM loans WHERE book_code=? AND user_id=?", (code,user))
    row = c.fetchone()
    if row:
        loan_id = row[0]
        c.execute("DELETE FROM loans WHERE loan_id=?", (loan_id,))
        c.execute("UPDATE books SET available_copies = available_copies + 1 WHERE code=?", (code,))
        conn.commit()
        print(f"[Actor] Devolucion procesada: {code} por {user}")
    else:
        # si no existe registro, avisamos y seguimos
        print(f"[Actor] Devolucion: no se encontró préstamo para {code} por {user}. Ignorando.")
        #c.execute("UPDATE books SET available_copies = available_copies + 1 WHERE code=?", (code,))
        conn.commit()

    conn.close()

def handle_renovacion(data):
    code = data.get("book_code")
    user = data.get("user_id")
    new_due = data.get("new_due")
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT loan_id, renewals FROM loans WHERE book_code=? AND user_id=?", (code,user))
    row = c.fetchone()
    if row:
        loan_id, renewals = row
        if renewals >= 2:
            # ya alcanzo el limite de renovaciones
            print(f"[Actor] Renovacion DENEGADA para {code} por {user}: ya tiene {renewals} renovaciones")
        else:
            # actualizar la fecha y contador
            try:
                # se convierte iso a datetime
                nd = datetime.fromisoformat(new_due)
            except Exception:
                nd = datetime.now() + timedelta(days=7)
            c.execute("UPDATE loans SET due_date=?, renewals=renewals+1 WHERE loan_id=?", (nd.isoformat(), loan_id))
            conn.commit()
            print(f"[Actor] Renovacion ACEPTADA para {code} por {user}. Nuevo vencimiento {nd.isoformat()}")
    else:
        print(f"[Actor] Renovacion: no existe préstamo para {code} por {user}. Ignorando.")

    conn.close()

def run(gc_host="localhost", gc_pub_port=5560):
    context = zmq.Context()
    sub = context.socket(zmq.SUB)
    sub.connect(f"tcp://{gc_host}:{gc_pub_port}")
    # suscribirse a los topics
    sub.setsockopt_string(zmq.SUBSCRIBE, "devolucion")
    sub.setsockopt_string(zmq.SUBSCRIBE, "renovacion")
    print(f"[Actor] Suscrito a tcp://{gc_host}:{gc_pub_port} (devolucion, renovacion)")

    while True:
        try:
            raw = sub.recv_string()
            # formato: "<topic> <json>"
            topic, payload = raw.split(" ",1)
            data = json.loads(payload)
            if topic == "devolucion":
                handle_devolucion(data)
            elif topic == "renovacion":
                handle_renovacion(data)
        except KeyboardInterrupt:
            print("Actor detenido.")
            break
        except Exception as e:
            print("Actor error:", e)

if __name__ == "__main__":
    # el argumento 1 es el host o ip del Gestor, el 2 el puerto donde se esta haciendo el PUB
    host = sys.argv[1] if len(sys.argv) > 1 else "localhost"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 5560
    run(host, port)
