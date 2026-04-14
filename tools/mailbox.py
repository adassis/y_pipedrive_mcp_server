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
    def get_mail_message(message_id: str, include_body: str = "true") -> str:
        """
        Retourne le contenu complet d'un message email.

        Args:
            message_id   : identifiant du message
            include_body : "true" pour inclure le corps du message (défaut: true)

        Returns:
            JSON avec le message complet (sujet, corps, expéditeur, destinataires,
            pièces jointes...).
        """
        try:
            params = {"include_body": 1 if include_body.lower() == "true" else 0}
            data = pipedrive_get(
                f"/mailbox/mailMessages/{message_id}",
                params=params, version=1
            )
            return json.dumps(data, ensure_ascii=False, indent=2)
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