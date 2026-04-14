# =============================================================
# server.py — Point d'entrée du serveur MCP Pipedrive
# =============================================================
# Pour ajouter un nouvel outil :
#   1. Créer tools/mon_outil.py avec register(mcp)
#   2. Ajouter import + register() ci-dessous
# =============================================================

import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from config import PORT, MCP_BEARER_TOKEN

import tools.deals
import tools.persons
import tools.activities
import tools.notes
import tools.mailbox
import tools.attachments

# ── Initialisation ────────────────────────────────────────────
mcp = FastMCP(
    name="pipedrive-server",
    host="0.0.0.0",
    port=PORT,
    instructions=(
        "Serveur MCP Pipedrive CRM. "
        "Outils disponibles : gestion des deals, contacts (persons), "
        "activités, notes, emails (mailbox) et pièces jointes. "
        "Utilisez list_deal_attachments pour lister les pièces jointes "
        "d'un deal avant de les analyser via le serveur OCR."
    )
)

# ── Enregistrement des outils ─────────────────────────────────
tools.deals.register(mcp)
tools.persons.register(mcp)
tools.activities.register(mcp)
tools.notes.register(mcp)
tools.mailbox.register(mcp)
tools.attachments.register(mcp)

# ── Middleware d'authentification ─────────────────────────────
class BearerAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if MCP_BEARER_TOKEN:
            auth = request.headers.get("Authorization", "")
            if not auth.startswith("Bearer ") or auth[7:].strip() != MCP_BEARER_TOKEN:
                return JSONResponse({"error": "Non autorisé"}, status_code=401)
        return await call_next(request)

# ── Démarrage ─────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"🚀 Serveur MCP Pipedrive démarré sur le port {PORT}")
    print(f"🔐 Auth : {'Activée' if MCP_BEARER_TOKEN else 'DÉSACTIVÉE'}")

    app = mcp.streamable_http_app()
    app.add_middleware(BearerAuthMiddleware)
    uvicorn.run(app, host="0.0.0.0", port=PORT)