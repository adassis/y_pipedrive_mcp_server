# =============================================================
# tools/deals.py — Outils MCP : Deals Pipedrive
# =============================================================
# 4 outils exposés :
#   - get_deals      : liste et recherche de deals
#   - get_deal       : détails d'un deal
#   - create_deal    : création d'un deal
#   - update_deal    : mise à jour d'un deal
#   - delete_deal    : suppression d'un deal
# API : v2 (endpoints modernes Pipedrive)
# =============================================================

import json
from utils.pipedrive import pipedrive_get, pipedrive_post, pipedrive_patch, pipedrive_delete


def register(mcp):

    @mcp.tool()
    def get_deals(
        status: str = "open",
        person_id: str = "",
        org_id: str = "",
        stage_id: str = "",
        limit: int = 50
    ) -> str:
        """
        Liste les deals Pipedrive avec filtres optionnels.

        Args:
            status    : "open" (défaut), "won", "lost", ou "deleted"
            person_id : filtrer par ID de personne liée
            org_id    : filtrer par ID d'organisation
            stage_id  : filtrer par ID d'étape du pipeline
            limit     : nombre max de deals à retourner (défaut: 50, max: 500)

        Returns:
            JSON avec la liste des deals et leurs informations principales.
        """
        try:
            params = {"status": status, "limit": min(limit, 500)}
            if person_id: params["person_id"] = person_id
            if org_id:    params["org_id"]    = org_id
            if stage_id:  params["stage_id"]  = stage_id

            data = pipedrive_get("/deals", params=params, version=2)
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)


    @mcp.tool()
    def search_deals(term: str, status: str = "", limit: int = 20) -> str:
        """
        Recherche des deals par titre, notes ou champs personnalisés.

        Args:
            term   : terme de recherche (minimum 2 caractères)
            status : filtrer par statut : "open", "won", "lost"
            limit  : nombre max de résultats (défaut: 20)

        Returns:
            JSON avec les deals correspondant au terme recherché.
        """
        try:
            params = {"term": term, "limit": min(limit, 500)}
            if status: params["status"] = status

            data = pipedrive_get("/deals/search", params=params, version=2)
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)


    @mcp.tool()
    def get_deal(deal_id: str) -> str:
        """
        Retourne tous les détails d'un deal spécifique.

        Args:
            deal_id : identifiant numérique du deal

        Returns:
            JSON avec toutes les informations du deal.
        """
        try:
            data = pipedrive_get(f"/deals/{deal_id}", version=2)
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e), "deal_id": deal_id}, ensure_ascii=False)


    @mcp.tool()
    def create_deal(
        title: str,
        person_id: str = "",
        org_id: str = "",
        pipeline_id: str = "",
        stage_id: str = "",
        value: str = "",
        currency: str = "EUR",
        status: str = "open",
        expected_close_date: str = ""
    ) -> str:
        """
        Crée un nouveau deal dans Pipedrive.

        Args:
            title               : titre du deal (obligatoire)
            person_id           : ID de la personne liée
            org_id              : ID de l'organisation liée
            pipeline_id         : ID du pipeline
            stage_id            : ID de l'étape
            value               : valeur monétaire du deal
            currency            : devise (défaut: EUR)
            status              : "open" (défaut), "won", "lost"
            expected_close_date : date de clôture prévue (format: YYYY-MM-DD)

        Returns:
            JSON avec le deal créé et son identifiant.
        """
        try:
            body = {"title": title, "currency": currency, "status": status}
            if person_id:           body["person_id"]           = int(person_id)
            if org_id:              body["org_id"]              = int(org_id)
            if pipeline_id:         body["pipeline_id"]         = int(pipeline_id)
            if stage_id:            body["stage_id"]            = int(stage_id)
            if value:               body["value"]               = float(value)
            if expected_close_date: body["expected_close_date"] = expected_close_date

            data = pipedrive_post("/deals", body=body, version=2)
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)


    @mcp.tool()
    def update_deal(
        deal_id: str,
        title: str = "",
        person_id: str = "",
        org_id: str = "",
        stage_id: str = "",
        status: str = "",
        value: str = "",
        lost_reason: str = "",
        expected_close_date: str = ""
    ) -> str:
        """
        Met à jour un deal existant. Seuls les champs fournis sont modifiés.

        Args:
            deal_id             : identifiant du deal à modifier (obligatoire)
            title               : nouveau titre
            person_id           : nouvel ID de personne liée
            org_id              : nouvel ID d'organisation
            stage_id            : nouvel ID d'étape
            status              : "open", "won", "lost"
            value               : nouvelle valeur monétaire
            lost_reason         : raison de perte (si status = "lost")
            expected_close_date : nouvelle date de clôture (YYYY-MM-DD)

        Returns:
            JSON avec le deal mis à jour.
        """
        try:
            body = {}
            if title:               body["title"]               = title
            if person_id:           body["person_id"]           = int(person_id)
            if org_id:              body["org_id"]              = int(org_id)
            if stage_id:            body["stage_id"]            = int(stage_id)
            if status:              body["status"]              = status
            if value:               body["value"]               = float(value)
            if lost_reason:         body["lost_reason"]         = lost_reason
            if expected_close_date: body["expected_close_date"] = expected_close_date

            if not body:
                return json.dumps({"error": "Aucun champ à modifier fourni."}, ensure_ascii=False)

            data = pipedrive_patch(f"/deals/{deal_id}", body=body, version=2)
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e), "deal_id": deal_id}, ensure_ascii=False)


    @mcp.tool()
    def delete_deal(deal_id: str) -> str:
        """
        Supprime un deal (marqué comme supprimé, effacement définitif après 30 jours).

        Args:
            deal_id : identifiant du deal à supprimer

        Returns:
            JSON confirmant la suppression.
        """
        try:
            data = pipedrive_delete(f"/deals/{deal_id}", version=2)
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e), "deal_id": deal_id}, ensure_ascii=False)