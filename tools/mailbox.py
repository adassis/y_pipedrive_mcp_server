# =============================================================
# tools/mailbox.py — Outils MCP : Mailbox Pipedrive
# =============================================================
# Accès aux emails synchronisés avec Pipedrive.
# Aucun endpoint de création (Pipedrive ne permet pas d'envoyer
# des emails via l'API — uniquement lire/mettre à jour/supprimer).
# API : v1 uniquement
# =============================================================

import json
from utils.pipedrive import pipedrive_get, pipedrive_put, pipedrive_delete

def _strip_html(html: str) -> str:
    """
    Supprime les balises HTML pour retourner du texte brut.
    Utilisé pour nettoyer le body des emails avant de le retourner.
    """
    if not html:
        return ""
    # Supprime les balises <style> et <script> avec leur contenu
    text = re.sub(r"<(style|script)[^>]*>.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
    # Remplace <br>, <p>, <div> par des sauts de ligne
    text = re.sub(r"<(br|p|div|tr)[^>]*>", "\n", text, flags=re.IGNORECASE)
    # Supprime toutes les autres balises HTML
    text = re.sub(r"<[^>]+>", "", text)
    # Décode les entités HTML courantes
    text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')
    # Nettoie les espaces et lignes vides multiples
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def _extract_emails(parties: list) -> list:
    """
    Extrait uniquement les adresses email depuis une liste de parties
    (from/to/cc Pipedrive).
    """
    return [p.get("email_address", "") for p in (parties or []) if p.get("email_address")]

def register(mcp):

    @mcp.tool()
    def get_deal_mail_messages(deal_id: str, limit: int = 50) -> str:
        """
        Liste tous les emails associés à un deal spécifique.
        Inclut les pièces jointes (ids) de chaque message.

        Args:
            deal_id : identifiant du deal
            limit   : nombre max de messages (défaut: 50)

        Returns:
            JSON avec la liste des messages et leurs métadonnées (expéditeur,
            sujet, date, pièces jointes...).
        """
        try:
            params = {"start": 0, "limit": min(limit, 100)}
            data = pipedrive_get(
                f"/deals/{deal_id}/mailMessages",
                params=params, version=1
            )
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e), "deal_id": deal_id}, ensure_ascii=False)

@mcp.tool()
def get_deal_mail_messages(deal_id: str, limit: int = 50) -> str:
    """
    Liste les emails d'un deal avec uniquement les métadonnées essentielles.
    N'inclut PAS le body — utilisez get_mail_message_body(message_id)
    pour récupérer le contenu complet d'un message spécifique.

    Args:
        deal_id : identifiant du deal
        limit   : nombre max de messages (défaut: 50)

    Returns:
        JSON avec la liste résumée des messages :
        id, subject, from, to, date, has_attachments.
    """
    try:
        params = {"start": 0, "limit": min(limit, 100)}
        data = pipedrive_get(
            f"/deals/{deal_id}/mailMessages",
            params=params, version=1
        )

        raw_messages = data.get("data") or []

        # ── Extraction des champs utiles uniquement ────────────
        # On élimine les dizaines de champs techniques inutiles
        # (s3_bucket, nylas_id, flags internes, etc.)
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
                "snippet":         d.get("snippet", ""),   # Aperçu du contenu
                "has_attachments": bool(d.get("has_real_attachments_flag")),
                "read":            bool(d.get("read_flag")),
                "thread_id":       d.get("mail_thread_id"),
            })

        output = {
            "deal_id":       deal_id,
            "message_count": len(clean_messages),
            "messages":      clean_messages,
        }

        return json.dumps(output, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e), "deal_id": deal_id}, ensure_ascii=False)
        
@mcp.tool()
def get_mail_message_body(message_id: str) -> str:
    """
    Récupère le contenu complet d'un email avec uniquement
    les métadonnées pertinentes : expéditeur, destinataires, date et body.

    Utilisez cet outil après get_deal_mail_messages pour lire
    le contenu d'un message spécifique.

    Args:
        message_id : identifiant du message (champ "id" dans get_deal_mail_messages)

    Returns:
        JSON avec :
        - id      : identifiant du message
        - subject : sujet de l'email
        - date    : date d'envoi (ISO 8601)
        - from    : adresse email de l'expéditeur
        - to      : liste des adresses email des destinataires
        - cc      : liste des adresses email en copie
        - body    : contenu texte brut de l'email (HTML strippé)
    """
    try:
        # include_body=1 demande à Pipedrive d'inclure le corps du message
        # Sans ce paramètre, le body est absent de la réponse
        data = pipedrive_get(
            f"/mailbox/mailMessages/{message_id}",
            params={"include_body": 1},
            version=1
        )

        d = (data.get("data") or {})

        # ── Extraction et nettoyage du body ────────────────────
        # Pipedrive retourne le body en HTML → on le convertit en texte brut
        body_html = d.get("body") or ""
        body_text = _strip_html(body_html)

        output = {
            "id":      d.get("id"),
            "subject": d.get("subject", ""),
            "date":    d.get("message_time") or d.get("add_time"),
            "from":    _extract_emails(d.get("from", [])),
            "to":      _extract_emails(d.get("to", [])),
            "cc":      _extract_emails(d.get("cc", [])),
            "body":    body_text,
        }

        return json.dumps(output, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e), "message_id": message_id}, ensure_ascii=False)

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
            JSON avec les détails du fil (participants, sujet, deal associé...).
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
        Met à jour un fil de discussion email.
        Permet d'associer le fil à un deal, de le marquer comme lu,
        ou de l'archiver.

        Args:
            thread_id     : identifiant du fil (obligatoire)
            deal_id       : associer ce fil à un deal Pipedrive
            read_flag     : "1" = marquer comme lu, "0" = non lu
            archived_flag : "1" = archiver, "0" = désarchiver

        Returns:
            JSON avec le fil mis à jour.
        """
        try:
            # Mailbox v1 attend du form-urlencoded (pas du JSON)
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