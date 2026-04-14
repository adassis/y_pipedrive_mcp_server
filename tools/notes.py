# =============================================================
# tools/notes.py — Outils MCP : Notes Pipedrive
# =============================================================
# Les notes sont des textes HTML attachés à des deals,
# personnes ou organisations.
# API : v1 uniquement (Notes pas encore migrées en v2)
# Méthode update : PUT (et non PATCH comme les autres)
# =============================================================

import json
from utils.pipedrive import pipedrive_get, pipedrive_post, pipedrive_put, pipedrive_delete


def register(mcp):

    @mcp.tool()
    def get_notes(
        deal_id: str = "",
        person_id: str = "",
        org_id: str = "",
        limit: int = 50
    ) -> str:
        """
        Liste les notes Pipedrive avec filtres optionnels.

        Args:
            deal_id   : filtrer par deal
            person_id : filtrer par personne
            org_id    : filtrer par organisation
            limit     : nombre max de notes (défaut: 50)

        Returns:
            JSON avec la liste des notes.
        """
        try:
            params = {"limit": min(limit, 500)}
            if deal_id:   params["deal_id"]   = deal_id
            if person_id: params["person_id"] = person_id
            if org_id:    params["org_id"]    = org_id

            data = pipedrive_get("/notes", params=params, version=1)
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)


    @mcp.tool()
    def get_note(note_id: str) -> str:
        """
        Retourne le contenu et les détails d'une note spécifique.

        Args:
            note_id : identifiant numérique de la note

        Returns:
            JSON avec le contenu HTML de la note et ses métadonnées.
        """
        try:
            data = pipedrive_get(f"/notes/{note_id}", version=1)
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e), "note_id": note_id}, ensure_ascii=False)


    @mcp.tool()
    def create_note(
        content: str,
        deal_id: str = "",
        person_id: str = "",
        org_id: str = "",
        pinned: str = "false"
    ) -> str:
        """
        Crée une nouvelle note dans Pipedrive.
        La note doit être attachée à au moins une entité (deal, personne ou organisation).

        Args:
            content   : contenu de la note (texte brut ou HTML) (obligatoire)
            deal_id   : ID du deal auquel attacher la note
            person_id : ID de la personne à laquelle attacher la note
            org_id    : ID de l'organisation à laquelle attacher la note
            pinned    : "true" pour épingler la note en haut (sur le deal si deal_id fourni)

        Returns:
            JSON avec la note créée et son identifiant.
        """
        try:
            if not deal_id and not person_id and not org_id:
                return json.dumps({
                    "error": "Fournissez au moins deal_id, person_id ou org_id."
                }, ensure_ascii=False)

            body = {"content": content}
            if deal_id:   body["deal_id"]   = int(deal_id)
            if person_id: body["person_id"] = int(person_id)
            if org_id:    body["org_id"]    = int(org_id)

            # Épinglage de la note sur l'entité liée
            if pinned.lower() == "true":
                if deal_id:   body["pinned_to_deal_flag"]         = 1
                if person_id: body["pinned_to_person_flag"]       = 1
                if org_id:    body["pinned_to_organization_flag"] = 1

            data = pipedrive_post("/notes", body=body, version=1)
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)


    @mcp.tool()
    def update_note(note_id: str, content: str) -> str:
        """
        Met à jour le contenu d'une note existante.
        Note : Pipedrive v1 utilise PUT (pas PATCH) pour les notes.

        Args:
            note_id : identifiant de la note à modifier (obligatoire)
            content : nouveau contenu (texte ou HTML) (obligatoire)

        Returns:
            JSON avec la note mise à jour.
        """
        try:
            data = pipedrive_put(f"/notes/{note_id}", body={"content": content}, version=1)
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e), "note_id": note_id}, ensure_ascii=False)


    @mcp.tool()
    def delete_note(note_id: str) -> str:
        """
        Supprime définitivement une note Pipedrive.

        Args:
            note_id : identifiant de la note à supprimer

        Returns:
            JSON confirmant la suppression.
        """
        try:
            data = pipedrive_delete(f"/notes/{note_id}", version=1)
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e), "note_id": note_id}, ensure_ascii=False)