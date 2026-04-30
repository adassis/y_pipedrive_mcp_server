# =============================================================
# tools/activities.py — Outils MCP : Activities Pipedrive
# =============================================================
# Les activités sont les tâches/appels/réunions associés
# à des deals, personnes ou organisations.
# API : v2 (CRUD complet disponible en v2)
# =============================================================

import json
from utils.pipedrive import pipedrive_get, pipedrive_post, pipedrive_patch, pipedrive_delete


def register(mcp):

    @mcp.tool()
    def get_activities(
        deal_id: str = "",
        person_id: str = "",
        org_id: str = "",
        done: str = "",
        limit: int = 50
    ) -> str:
        """
        Liste les activités Pipedrive avec filtres optionnels.

        Args:
            deal_id   : filtrer par deal lié
            person_id : filtrer par personne liée
            org_id    : filtrer par organisation liée
            done      : "true" = activités terminées, "false" = en cours
            limit     : nombre max d'activités (défaut: 50)

        Returns:
            JSON avec la liste des activités.
        """
        try:
            params = {"limit": min(limit, 500)}
            if deal_id:   params["deal_id"]   = deal_id
            if person_id: params["person_id"] = person_id
            if org_id:    params["org_id"]    = org_id
            if done:      params["done"]      = done.lower() == "true"

            data = pipedrive_get("/activities", params=params, version=2)
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)


    @mcp.tool()
    def get_activity(activity_id: str) -> str:
        """
        Retourne les détails d'une activité spécifique.

        Args:
            activity_id : identifiant de l'activité

        Returns:
            JSON avec toutes les informations de l'activité.
        """
        try:
            data = pipedrive_get(f"/activities/{activity_id}", version=2)
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e), "activity_id": activity_id}, ensure_ascii=False)


    @mcp.tool()
    def create_activity(
        subject: str,
        activity_type: str = "task",
        deal_id: str = "",
        person_id: str = "",
        owner_id: str = "",
        org_id: str = "",
        due_date: str = "",
        due_time: str = "",
        duration: str = "",
        note: str = "",
        done: str = "false"
    ) -> str:
        """
        Crée une nouvelle activité dans Pipedrive.

        Args:
            subject       : titre/sujet de l'activité (obligatoire)
            activity_type : type — "call", "meeting", "task", "email", "deadline", etc.
            deal_id       : ID du deal lié
            person_id     : ID de la personne liée
            owner_id      : ID du bizdev owner de l'acti
            org_id        : ID de l'organisation liée
            due_date      : date d'échéance (YYYY-MM-DD)
            due_time      : heure d'échéance (HH:MM)
            duration      : durée (HH:MM)
            note          : note associée à l'activité
            done          : "true" si déjà terminée, "false" sinon

        Returns:
            JSON avec l'activité créée.
        """
        try:
            body = {
                "subject": subject,
                "type":    activity_type,
                "done":    done.lower() == "true"
            }
            if deal_id:   body["deal_id"]   = int(deal_id)
            if person_id: body["person_id"] = int(person_id)
            if owner_id:   body["owner_id"]   = int(owner_id)
            if org_id:    body["org_id"]    = int(org_id)
            if due_date:  body["due_date"]  = due_date
            if due_time:  body["due_time"]  = due_time
            if duration:  body["duration"]  = duration
            if note:      body["note"]      = note

            data = pipedrive_post("/activities", body=body, version=2)
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)


    @mcp.tool()
    def update_activity(
        activity_id: str,
        subject: str = "",
        activity_type: str = "",
        deal_id: str = "",
        person_id: str = "",
        owner_id: str = "",
        due_date: str = "",
        due_time: str = "",
        duration: str = "",
        note: str = "",
        done: str = ""
    ) -> str:
        """
        Met à jour une activité existante. Seuls les champs fournis sont modifiés.

        Args:
            activity_id   : identifiant de l'activité (obligatoire)
            subject       : nouveau sujet
            activity_type : nouveau type
            deal_id       : nouvel ID de deal lié
            person_id     : nouvel ID de personne liée
            owner_id       : bizdev owner de l'acti
            due_date      : nouvelle date d'échéance (YYYY-MM-DD)
            due_time      : nouvelle heure (HH:MM)
            duration      : nouvelle durée (HH:MM)
            note          : nouvelle note
            done          : "true" pour marquer comme terminée

        Returns:
            JSON avec l'activité mise à jour.
        """
        try:
            body = {}
            if subject:       body["subject"]  = subject
            if activity_type: body["type"]     = activity_type
            if deal_id:       body["deal_id"]  = int(deal_id)
            if person_id:     body["person_id"] = int(person_id)
            if owner_id:      body["owner_id"]  = int(user_id)
            if due_date:      body["due_date"] = due_date
            if due_time:      body["due_time"] = due_time
            if duration:      body["duration"] = duration
            if note:          body["note"]     = note
            if done:          body["done"]     = done.lower() == "true"

            if not body:
                return json.dumps({"error": "Aucun champ à modifier fourni."}, ensure_ascii=False)

            data = pipedrive_patch(f"/activities/{activity_id}", body=body, version=2)
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e), "activity_id": activity_id}, ensure_ascii=False)


    @mcp.tool()
    def delete_activity(activity_id: str) -> str:
        """
        Supprime une activité (effacement définitif après 30 jours).

        Args:
            activity_id : identifiant de l'activité à supprimer

        Returns:
            JSON confirmant la suppression.
        """
        try:
            data = pipedrive_delete(f"/activities/{activity_id}", version=2)
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e), "activity_id": activity_id}, ensure_ascii=False)