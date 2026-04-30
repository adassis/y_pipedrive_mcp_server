# =============================================================
# tools/users.py — Outils MCP : Users Pipedrive
# =============================================================
# Permet de lister tous les utilisateurs du compte Pipedrive.
# Utile pour récupérer l'owner_id d'un user avant de lui
# assigner une activité, un deal, etc.
# API : v1 (l'endpoint /users n'existe qu'en v1)
# =============================================================

import json
from utils.pipedrive import pipedrive_get  # On réutilise le client HTTP centralisé


def register(mcp):
    # La fonction register() est appelée dans server.py.
    # Elle "enregistre" tous les tools de ce fichier dans l'instance FastMCP.

    @mcp.tool()
    def list_pipedrive_users() -> str:
        """
        Liste tous les utilisateurs du compte Pipedrive.
        Retourne l'ID, le nom, l'email et le statut actif de chaque user.
        Utilise cet outil pour trouver l'owner_id d'un utilisateur
        avant de lui assigner une activité ou un deal.

        Returns:
            JSON avec la liste des utilisateurs actifs.
        """
        try:
            # Appel à l'endpoint GET /api/v1/users
            # On force version=1 car cet endpoint n'existe qu'en v1
            # pipedrive_get gère automatiquement l'ajout de l'api_token
            data = pipedrive_get("/users", version=1)

            # data est un dict avec :
            # - data["success"] : True/False
            # - data["data"]    : liste des users

            users_raw = data.get("data") or []

            # Cas où aucun utilisateur n'est retourné
            if not users_raw:
                return json.dumps({"message": "Aucun utilisateur trouvé."}, ensure_ascii=False)

            # On ne garde que les champs utiles pour l'agent :
            # - id       → c'est l'owner_id à passer à create_activity / create_deal
            # - name     → nom complet affiché
            # - email    → email du user
            # - active   → True = compte actif, False = compte désactivé
            users = [
                {
                    "id":     u.get("id"),
                    "name":   u.get("name"),
                    "email":  u.get("email"),
                    "active": u.get("active_flag", False)
                }
                for u in users_raw
            ]

            # ensure_ascii=False pour garder les accents (ex: prénom français)
            return json.dumps(users, ensure_ascii=False, indent=2)

        except Exception as e:
            # En cas d'erreur (réseau, auth, etc.), on retourne un JSON d'erreur
            # plutôt que de crasher le serveur
            return json.dumps({"error": str(e)}, ensure_ascii=False)