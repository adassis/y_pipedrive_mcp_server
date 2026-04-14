# =============================================================
# config.py — Configuration du serveur MCP Pipedrive
# =============================================================

import os

# ── Serveur MCP ───────────────────────────────────────────────
PORT             = int(os.environ.get("PORT", 8000))
MCP_BEARER_TOKEN = os.environ.get("MCP_BEARER_TOKEN", "")

# ── Pipedrive ─────────────────────────────────────────────────
PIPEDRIVE_API_TOKEN = os.environ.get("PIPEDRIVE_API_TOKEN", "")
# Token API Pipedrive : Profil > Personal preferences > API

PIPEDRIVE_SUBDOMAIN = os.environ.get("PIPEDRIVE_SUBDOMAIN", "")
# Sous-domaine Pipedrive — ex: "seraphin" pour seraphin.pipedrive.com