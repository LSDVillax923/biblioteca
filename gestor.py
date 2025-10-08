# gc.py
import zmq
import json
import time
import sys

def run(bind_reply="*:5555", bind_pub="*:5560"):
    context = zmq.Context()

    # REP socket para recibir de PS
    rep = context.socket(zmq.REP)
    rep.bind(f"tcp://{bind_reply}")
    print(f"[GC] REP escuchando en tcp://{bind_reply}")

    # PUB socket para publicar a los actores (devolucion, renovacion)
    pub = context.socket(zmq.PUB)
    pub.bind(f"tcp://{bind_pub}")
    print(f"[GC] PUB en tcp://{bind_pub} (topic: devolucion, renovacion)")

    while True:
        try:
            msg = rep.recv_string()
            data = json.loads(msg)
            tipo = data.get("type")
            # Formatea respuesta de recepcion inmediata (según especificacion)
            if tipo == "devolucion":
                response = {"status":"accepted","op":"devolucion","info":"Recibido. Se registrará asincrónicamente."}
                rep.send_string(json.dumps(response))
                # Publicar en topic 'devolucion'
                pub_msg = json.dumps(data)
                pub.send_string("devolucion " + pub_msg)
                print(f"[GC] Publicado devolucion -> {pub_msg}")

            elif tipo == "renovacion" or tipo == "renovación":
                # calcular nueva fecha propuesta (GC devuelve nueva fecha: +7 días)
                from datetime import datetime, timedelta
                new_due = (datetime.now() + timedelta(days=7)).isoformat()
                response = {"status":"accepted","op":"renovacion","new_due":new_due}
                rep.send_string(json.dumps(response))
                data["new_due"] = new_due
                pub_msg = json.dumps(data)
                pub.send_string("renovacion " + pub_msg)
                print(f"[GC] Publicado renovacion -> {pub_msg}")

            else:
                rep.send_string(json.dumps({"status":"error","reason":"tipo desconocido"}))
        except KeyboardInterrupt:
            print("GC detenido.")
            break
        except Exception as e:
            print("GC error:", e)
            # no bloquear, continuar

if __name__ == "__main__":
    # el argumento 1 es el bind para REP (PS), el 2 para PUB (Actores)
    bind_reply = sys.argv[1] if len(sys.argv) > 1 else "*:5555"
    bind_pub = sys.argv[2] if len(sys.argv) > 2 else "*:5560"
    run(bind_reply, bind_pub)
