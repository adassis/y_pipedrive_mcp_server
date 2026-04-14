# =============================================================
# tools/persons.py — Outils MCP : Persons Pipedrive
# =============================================================
# 5 outils :
#   - get_persons    : liste des contacts
#   - search_persons : recherche par nom/email/téléphone
#   - get_person     : détails d'un contact
#   - create_person  : création d'un contact
#   - update_person  : mise à jour d'un contact
#   - delete_person  : suppression d'un contact
# API : v2
# =============================================================

import json
from utils.pipedrive import pipedrive_get, pipedrive_post, pipedrive_patch, pipedrive_delete


def register(mcp):

    @mcp.tool()
    def get_persons(
        org_id: str = "",
        deal_id: str = "",
        limit: int = 50
    ) -> str:
        """
        Liste les contacts (persons) Pipedrive.

        Args:
            org_id  : filtrer par organisation
            deal_id : filtrer par deal lié
            limit   : nombre max de contacts (défaut: 50)

        Returns:
            JSON avec la liste des contacts.
        """
        try:
            params = {"limit": min(limit, 500)}
            if org_id:  params["org_id"]  = org_id
            if deal_id: params["deal_id"] = deal_id

            data = pipedrive_get("/persons", params=params, version=2)
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)


    @mcp.tool()
    def search_persons(term: str, org_id: str = "", limit: int = 20) -> str:
        """
        Recherche des contacts par nom, email, téléphone ou notes.

        Args:
            term   : terme de recherche (min 2 caractères)
            org_id : restreindre à une organisation
            limit  : nombre max de résultats

        Returns:
            JSON avec les contacts correspondants.
        """
        try:
            params = {"term": term, "limit": min(limit, 500)}
            if org_id: params["organization_id"] = org_id

            data = pipedrive_get("/persons/search", params=params, version=2)
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)


    @mcp.tool()
    def get_person(person_id: str) -> str:
        """
        Retourne les détails complets d'un contact.

        Args:
            person_id : identifiant numérique du contact

        Returns:
            JSON avec toutes les informations du contact.
        """
        try:
            data = pipedrive_get(f"/persons/{person_id}", version=2)
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e), "person_id": person_id}, ensure_ascii=False)


    @mcp.tool()
    def create_person(
        name: str,
        email: str = "",
        phone: str = "",
        org_id: str = ""
    ) -> str:
        """
        Crée un nouveau contact dans Pipedrive.

        Args:
            name   : nom complet du contact (obligatoire)
            email  : adresse email principale
            phone  : numéro de téléphone principal
            org_id : ID de l'organisation à lier

        Returns:
            JSON avec le contact créé et son identifiant.
        """
        try:
            body = {"name": name}
            if email:  body["emails"] = [{"value": email, "primary": True, "label": "work"}]
            if phone:  body["phones"] = [{"value": phone, "primary": True, "label": "work"}]
            if org_id: body["org_id"] = int(org_id)

            data = pipedrive_post("/persons", body=body, version=2)
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)


    @mcp.tool()
    def update_person(
        person_id: str,
        name: str = "",
        email: str = "",
        phone: str = "",
        org_id: str = ""
    ) -> str:
        """
        Met à jour un contact existant. Seuls les champs fournis sont modifiés.

        Args:
            person_id : identifiant du contact (obligatoire)
            name      : nouveau nom
            email     : nouvel email principal
            phone     : nouveau téléphone principal
            org_id    : nouvel ID d'organisation

        Returns:
            JSON avec le contact mis à jour.
        """
        try:
            body = {}
            if name:   body["name"]   = name
            if email:  body["emails"] = [{"value": email, "primary": True, "label": "work"}]
            if phone:  body["phones"] = [{"value": phone, "primary": True, "label": "work"}]
            if org_id: body["org_id"] = int(org_id)

            if not body:
                return json.dumps({"error": "Aucun champ à modifier fourni."}, ensure_ascii=False)

            data = pipedrive_patch(f"/persons/{person_id}", body=body, version=2)
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e), "person_id": person_id}, ensure_ascii=False)


    @mcp.tool()
    def delete_person(person_id: str) -> str:
        """
        Supprime un contact (effacement définitif après 30 jours).

        Args:
            person_id : identifiant du contact à supprimer

        Returns:
            JSON confirmant la suppression.
        """
        try:
            data = pipedrive_delete(f"/persons/{person_id}", version=2)
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e), "person_id": person_id}, ensure_ascii=False)