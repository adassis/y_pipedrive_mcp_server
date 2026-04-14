# =============================================================
# tools/mailbox.py — Outils MCP : Mailbox Pipedrive
# =============================================================

import json
import re
from utils.pipedrive import pipedrive_get, pipedrive_put, pipedrive_delete


# =============================================================
# FONCTIONS PRIVÉES (hors register — pas de @mcp.tool ici)
# =============================================================

def _strip_html(html: str) -> str:
    """Convertit du HTML en texte brut."""
    if not html:
        return ""
    text = re.sub(r"<(style|script)[^>]*>.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<(br|p|div|tr)[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def _extract_emails(parties: list) -> list:
    """Extrait uniquement les adresses email depuis une liste de parties Pipedrive."""
    return [p.get("email_address", "") for p in (parties or []) if p.get("email_address")]


# =============================================================
# ENREGISTREMENT DES OUTILS MCP
# ⚠️ TOUS les @mcp.tool() doivent être INSIDE register(mcp)
# =============================================================

def register(mcp):

    @mcp.tool()
    def get_deal_mail_messages(deal_id: str, limit: int = 50) -> str:
        """
        Liste les emails d'un deal avec uniquement les métadonnées essentielles.
        N'inclut PAS le body — utilisez get_mail_message_body pour lire
        le contenu complet d'un message spécifique.

        Args:
            deal_id : identifiant du deal
            limit   : nombre max de messages (défaut: 50)

        Returns:
            JSON avec : id, subject, from, to, cc, date, snippet, has_attachments.
        """
        try:
            params = {"start": 0, "limit": min(limit, 100)}
            data = pipedrive_get(
                f"/deals/{deal_id}/mailMessages",
                params=params, version=1
            )

            raw_messages = data.get("data") or []

            clean_messages = []
            for msg in raw_messages:
                d = msg.get("data") or {}
                clean_messages.append({
                    "id":              d.get("id"),
                    "subject":         d.get("subject", ""),
                    "date":            d.get("message_time") or d.get("timestamp"),
                    "from":            _extract_emails(d.get("from", [])),
                    "to":              _extract_emails(d.get("to", [])),
                    "cc":              _extract_emails(d.get("cc", [])),
                    "snippet":         d.get("snippet", ""),
                    "has_attachments": bool(d.get("has_real_attachments_flag")),
                    "read":            bool(d.get("read_flag")),
                    "thread_id":       d.get("mail_thread_id"),
                })

            return json.dumps({
                "deal_id":       deal_id,
                "message_count": len(clean_messages),
                "messages":      clean_messages,
            }, ensure_ascii=False, indent=2)

        except Exception as e:
            return json.dumps({"error": str(e), "deal_id": deal_id}, ensure_ascii=False)


    @mcp.tool()
    def get_mail_message_body(message_id: str) -> str:
        """
        Récupère le contenu complet d'un email : expéditeur, destinataires, date et body.

        Utilisez cet outil après get_deal_mail_messages pour lire
        le contenu d'un message spécifique.

        Args:
            message_id : identifiant du message (champ "id" dans get_deal_mail_messages)

        Returns:
            JSON avec : id, subject, date, from, to, cc, body (texte brut).
        """
        try:
            data = pipedrive_get(
                f"/mailbox/mailMessages/{message_id}",
                params={"include_body": 1},
                version=1
            )

            d = data.get("data") or {}
            body_text = _strip_html(d.get("body") or "")

            return json.dumps({
                "id":      d.get("id"),
                "subject": d.get("subject", ""),
                "date":    d.get("message_time") or d.get("add_time"),
                "from":    _extract_emails(d.get("from", [])),
                "to":      _extract_emails(d.get("to", [])),
                "cc":      _extract_emails(d.get("cc", [])),
                "body":    body_text,
            }, ensure_ascii=False, indent=2)

        except Exception as e:
            return json.dumps({"error": str(e), "message_id": message_id}, ensure_ascii=False)


    @mcp.tool()
    def get_deal_mail_messages(deal_id: str, max_items: int = 200) -> str:
    """
    Liste les emails d'un deal avec uniquement les métadonnées essentielles.
    Gère automatiquement la pagination pour récupérer TOUS les emails.
    N'inclut PAS le body — utilisez get_mail_message_body(message_id)
    pour lire le contenu complet d'un message spécifique.

    Args:
        deal_id   : identifiant du deal
        max_items : nombre maximum total d'emails à récupérer (défaut: 200, max: 500)
                    Pipedrive limite à 100 par requête — la pagination est gérée
                    automatiquement en interne.

    Returns:
        JSON avec : message_count, messages (id, subject, from, to, cc,
                    date, snippet, has_attachments, read, thread_id).
    """
    try:
        max_items = min(max_items, 500)  # Plafond de sécurité
        all_messages = []
        start = 0
        limit = 100  # Maximum autorisé par Pipedrive v1

        # ── Pagination automatique ─────────────────────────────
        # Pipedrive v1 retourne jusqu'à 100 messages par page.
        # On itère jusqu'à ce que more_items_in_collection = false
        # ou qu'on atteigne max_items.
        while True:
            data = pipedrive_get(
                f"/deals/{deal_id}/mailMessages",
                params={"start": start, "limit": limit},
                version=1
            )

            items = data.get("data") or []
            all_messages.extend(items)

            # Vérification s'il reste des pages
            pagination = (
                (data.get("additional_data") or {})
                .get("pagination") or {}
            )
            has_more = pagination.get("more_items_in_collection", False)

            if not has_more or len(all_messages) >= max_items:
                break  # Plus de pages ou limite atteinte

            start += limit  # Page suivante

        # Tronque si on a dépassé max_items
        all_messages = all_messages[:max_items]

        # ── Nettoyage : on garde uniquement les champs utiles ──
        clean_messages = []
        for msg in all_messages:
            d = msg.get("data") or {}
            clean_messages.append({
                "id":              d.get("id"),
                "subject":         d.get("subject", ""),
                "date":            d.get("message_time") or d.get("timestamp"),
                "from":            _extract_emails(d.get("from", [])),
                "to":              _extract_emails(d.get("to", [])),
                "cc":              _extract_emails(d.get("cc", [])),
                "snippet":         d.get("snippet", ""),
                "has_attachments": bool(d.get("has_real_attachments_flag")),
                "read":            bool(d.get("read_flag")),
                "thread_id":       d.get("mail_thread_id"),
            })

        output = {
            "deal_id":       deal_id,
            "message_count": len(clean_messages),
            "truncated":     len(all_messages) >= max_items and has_more,
            # truncated = True signifie qu'il existe encore des emails
            # au-delà de max_items — augmentez max_items si nécessaire
            "messages":      clean_messages,
        }
        return json.dumps(output, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e), "deal_id": deal_id}, ensure_ascii=False)


    @mcp.tool()
    def get_mail_threads(folder: str = "inbox", limit: int = 30) -> str:
        """
        Liste les fils de discussion email dans un dossier Pipedrive.

        Args:
            folder : "inbox" (défaut), "drafts", "sent", ou "archive"
            limit  : nombre max de fils (défaut: 30)

        Returns:
            JSON avec la liste des fils de discussion.
        """
        try:
            params = {"folder": folder, "start": 0, "limit": min(limit, 100)}
            data = pipedrive_get("/mailbox/mailThreads", params=params, version=1)
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)


    @mcp.tool()
    def get_mail_thread(thread_id: str) -> str:
        """
        Retourne les détails d'un fil de discussion email.

        Args:
            thread_id : identifiant du fil de discussion

        Returns:
            JSON avec les détails du fil.
        """
        try:
            data = pipedrive_get(f"/mailbox/mailThreads/{thread_id}", version=1)
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e), "thread_id": thread_id}, ensure_ascii=False)


    @mcp.tool()
    def get_mail_thread_messages(thread_id: str) -> str:
        """
        Retourne tous les messages d'un fil de discussion.

        Args:
            thread_id : identifiant du fil de discussion

        Returns:
            JSON avec tous les messages du fil.
        """
        try:
            data = pipedrive_get(
                f"/mailbox/mailThreads/{thread_id}/mailMessages",
                version=1
            )
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e), "thread_id": thread_id}, ensure_ascii=False)


    @mcp.tool()
    def update_mail_thread(
        thread_id: str,
        deal_id: str = "",
        read_flag: str = "",
        archived_flag: str = ""
    ) -> str:
        """
        Met à jour un fil de discussion : associer à un deal, marquer lu, archiver.

        Args:
            thread_id     : identifiant du fil (obligatoire)
            deal_id       : associer ce fil à un deal
            read_flag     : "1" = lu, "0" = non lu
            archived_flag : "1" = archiver, "0" = désarchiver

        Returns:
            JSON avec le fil mis à jour.
        """
        try:
            form_data = {}
            if deal_id:       form_data["deal_id"]       = deal_id
            if read_flag:     form_data["read_flag"]     = read_flag
            if archived_flag: form_data["archived_flag"] = archived_flag

            if not form_data:
                return json.dumps({"error": "Aucun champ à modifier fourni."}, ensure_ascii=False)

            data = pipedrive_put(
                f"/mailbox/mailThreads/{thread_id}",
                form_data=form_data, version=1
            )
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e), "thread_id": thread_id}, ensure_ascii=False)


    @mcp.tool()
    def delete_mail_thread(thread_id: str) -> str:
        """
        Supprime un fil de discussion email.

        Args:
            thread_id : identifiant du fil à supprimer

        Returns:
            JSON confirmant la suppression.
        """
        try:
            data = pipedrive_delete(f"/mailbox/mailThreads/{thread_id}", version=1)
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e), "thread_id": thread_id}, ensure_ascii=False)