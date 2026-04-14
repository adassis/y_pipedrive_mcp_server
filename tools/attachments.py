# =============================================================
# tools/attachments.py — Outils MCP : Pièces jointes Pipedrive
# =============================================================
# Liste les pièces jointes d'un deal (depuis les emails).
# Le téléchargement + OCR restent sur le serveur OCR dédié.
# API : v1 (mail messages)
# =============================================================

import json
import re
from utils.pipedrive import pipedrive_get


def register(mcp):

    @mcp.tool()
    def list_deal_attachments(deal_id: str) -> str:
        """
        Liste toutes les pièces jointes des emails d'un deal Pipedrive.

        Workflow :
        1. Récupère tous les emails du deal (avec pagination automatique)
        2. Pour chaque email, extrait les pièces jointes
        3. Déduplique les IDs et retourne la liste

        Utilisez cet outil avant read_pipedrive_attachment_ocr
        (disponible sur le serveur OCR) pour connaître les IDs à analyser.

        Args:
            deal_id : identifiant numérique du deal

        Returns:
            JSON avec :
            - deal_id          : l'identifiant du deal
            - message_count    : nombre d'emails trouvés
            - attachment_count : nombre de pièces jointes uniques
            - attachments      : liste d'objets {id, filename, size, content_type}
        """
        try:
            # ── Pagination v1 (start/limit, pas cursor) ────────
            all_messages = []
            start = 0
            limit = 50

            while True:
                data = pipedrive_get(
                    f"/deals/{deal_id}/mailMessages",
                    params={"start": start, "limit": limit},
                    version=1
                )
                items = data.get("data") or []
                all_messages.extend(items)

                additional = data.get("additional_data") or {}
                pagination = additional.get("pagination") or {}
                if not pagination.get("more_items_in_collection", False):
                    break
                start += limit

            # ── Extraction des pièces jointes ──────────────────
            seen_ids = set()
            attachments = []

            for message in all_messages:
                msg_attachments = (message.get("data") or {}).get("attachments") or []

                for att in msg_attachments:
                    if not att:
                        continue

                    att_id = att.get("id")

                    # Fallback : extraire l'ID depuis l'URL
                    if att_id is None:
                        url = att.get("url") or ""
                        m = re.search(r"mailAttachments/(\d+)", url)
                        if m:
                            att_id = int(m.group(1))

                    if att_id is None:
                        continue

                    key = str(att_id)
                    if key in seen_ids:
                        continue

                    seen_ids.add(key)
                    attachments.append({
                        "id":           att_id,
                        "filename":     att.get("name") or att.get("filename") or "",
                        "content_type": att.get("content_type") or att.get("mime_type") or "",
                        "size":         att.get("size") or None,
                        "url":          att.get("url") or "",
                    })

            output = {
                "deal_id":          deal_id,
                "message_count":    len(all_messages),
                "attachment_count": len(attachments),
                "attachments":      attachments,
            }

            return json.dumps(output, ensure_ascii=False, indent=2)

        except Exception as e:
            return json.dumps({"error": str(e), "deal_id": deal_id}, ensure_ascii=False)