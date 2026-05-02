"""
Notificacion de estado del pipeline Railway via Discord webhook.
Se llama desde railway_pipeline.py al final de cada ejecucion.

Uso:
  python scripts/notify_railway.py --status ok --productos 16000 --scrapers 3 --pushed 1 --error ""
  python scripts/notify_railway.py --status fail --productos 0 --scrapers 0 --pushed 0 --error "all_scrapers_failed"

Si DISCORD_WEBHOOK_URL no esta en .env, solo imprime y no falla.
"""
import argparse
import os
import sys
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()


def send_discord(webhook_url: str, content: str) -> bool:
    try:
        import urllib.request
        import json as _json
        payload = _json.dumps({"content": content}).encode("utf-8")
        req = urllib.request.Request(
            webhook_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status in (200, 204)
    except Exception as e:
        print(f"[notify] Discord fallo: {e}")
        return False


def build_message(status: str, productos: int, scrapers: int, pushed: bool, error: str) -> str:
    hora = datetime.now().strftime("%d/%m/%Y %H:%M")
    if status == "ok" and pushed:
        icono = "OK"
        resumen = f"Pipeline exitoso | {productos:,} productos | {scrapers}/3 scrapers | Vercel actualizado"
    elif status == "ok" and not pushed:
        icono = "AVISO"
        resumen = f"Pipeline corrio pero sin cambios en catalogo | {scrapers}/3 scrapers exitosos"
    else:
        icono = "FALLA"
        causas = {
            "all_scrapers_failed": "Todos los scrapers fallaron (cookies expiradas?)",
            "catalogo_failed": "actualizar_catalogo.py fallo",
            "catalogo_bajo": f"Catalogo con solo {productos} productos (anormalmente bajo)",
            "push_failed": "git push fallo",
            "sin_cambios": "Sin cambios en el catalogo",
        }
        causa = next((v for k, v in causas.items() if error.startswith(k)), f"Error: {error}")
        resumen = f"PIPELINE FALLO | {causa} | {scrapers}/3 scrapers | Revisar Railway logs"

    return f"[Brujula {hora}] {icono} - {resumen}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--status", default="fail")
    parser.add_argument("--productos", type=int, default=0)
    parser.add_argument("--scrapers", type=int, default=0)
    parser.add_argument("--pushed", type=int, default=0)
    parser.add_argument("--error", default="")
    args = parser.parse_args()

    msg = build_message(
        status=args.status,
        productos=args.productos,
        scrapers=args.scrapers,
        pushed=bool(args.pushed),
        error=args.error,
    )
    print(f"[notify] {msg}")

    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("[notify] DISCORD_WEBHOOK_URL no configurada - solo imprimiendo")
        return

    ok = send_discord(webhook_url, msg)
    if not ok:
        print("[notify] Discord no respondio correctamente")


if __name__ == "__main__":
    main()
