# =============================================================
# utils/pipedrive.py — Client HTTP Pipedrive centralisé
# =============================================================
# Toutes les fonctions d'appel à l'API Pipedrive passent ici.
# Gère automatiquement :
#   - l'URL de base (v1 ou v2 selon l'endpoint)
#   - l'authentification via api_token
#   - les erreurs HTTP
#   - la pagination (helper dédié)
# =============================================================

import requests
from config import PIPEDRIVE_API_TOKEN, PIPEDRIVE_SUBDOMAIN


def _base_url(version: int = 2) -> str:
    """
    Construit l'URL de base selon la version de l'API.
    v2 pour les endpoints modernes, v1 pour Notes/Mailbox/Attachments.
    """
    return f"https://{PIPEDRIVE_SUBDOMAIN}.pipedrive.com/api/v{version}"


def _check_credentials():
    """Lève une RuntimeError si les credentials ne sont pas configurés."""
    if not PIPEDRIVE_API_TOKEN or not PIPEDRIVE_SUBDOMAIN:
        raise RuntimeError(
            "PIPEDRIVE_API_TOKEN ou PIPEDRIVE_SUBDOMAIN non configurés. "
            "Vérifiez vos variables d'environnement sur Railway."
        )


def pipedrive_get(path: str, params: dict = None, version: int = 2) -> dict:
    """
    Effectue un GET authentifié vers l'API Pipedrive.

    Args:
        path    : chemin de l'endpoint, ex: "/deals/42"
        params  : paramètres query string supplémentaires
        version : version de l'API à utiliser (1 ou 2)

    Returns:
        dict : corps JSON complet de la réponse Pipedrive

    Raises:
        RuntimeError : si credentials manquants ou erreur HTTP
    """
    _check_credentials()
    all_params = {"api_token": PIPEDRIVE_API_TOKEN}
    if params:
        all_params.update(params)

    r = requests.get(_base_url(version) + path, params=all_params, timeout=30)
    if not r.ok:
        raise RuntimeError(f"GET {path} → HTTP {r.status_code}: {r.text[:400]}")
    return r.json()


def pipedrive_post(path: str, body: dict, version: int = 2) -> dict:
    """
    Effectue un POST authentifié vers l'API Pipedrive.
    Utilisé pour créer des entités (deal, person, activity, note...).

    Args:
        path    : chemin de l'endpoint, ex: "/deals"
        body    : corps JSON de la requête
        version : version de l'API (1 ou 2)

    Returns:
        dict : réponse JSON Pipedrive
    """
    _check_credentials()
    params = {"api_token": PIPEDRIVE_API_TOKEN}
    r = requests.post(
        _base_url(version) + path,
        params=params, json=body, timeout=30
    )
    if not r.ok:
        raise RuntimeError(f"POST {path} → HTTP {r.status_code}: {r.text[:400]}")
    return r.json()


def pipedrive_patch(path: str, body: dict, version: int = 2) -> dict:
    """
    Effectue un PATCH authentifié vers l'API Pipedrive.
    Utilisé pour mettre à jour partiellement une entité.
    PATCH = on envoie uniquement les champs à modifier (contrairement à PUT).

    Args:
        path    : chemin de l'endpoint, ex: "/deals/42"
        body    : champs à modifier
        version : version de l'API (1 ou 2)
    """
    _check_credentials()
    params = {"api_token": PIPEDRIVE_API_TOKEN}
    r = requests.patch(
        _base_url(version) + path,
        params=params, json=body, timeout=30
    )
    if not r.ok:
        raise RuntimeError(f"PATCH {path} → HTTP {r.status_code}: {r.text[:400]}")
    return r.json()


def pipedrive_put(path: str, body: dict = None, form_data: dict = None, version: int = 1) -> dict:
    """
    Effectue un PUT authentifié vers l'API Pipedrive.
    Utilisé par les endpoints Notes (v1) et Mailbox (v1).

    Pipedrive v1 attend parfois du JSON, parfois du form-urlencoded.
    - body      → envoyé en JSON (Content-Type: application/json)
    - form_data → envoyé en form-urlencoded (Mailbox threads)

    Args:
        path      : chemin de l'endpoint
        body      : corps JSON (Notes)
        form_data : données form (Mailbox)
        version   : version de l'API (toujours 1 pour PUT)
    """
    _check_credentials()
    params = {"api_token": PIPEDRIVE_API_TOKEN}

    if form_data:
        r = requests.put(
            _base_url(version) + path,
            params=params, data=form_data, timeout=30
        )
    else:
        r = requests.put(
            _base_url(version) + path,
            params=params, json=body or {}, timeout=30
        )

    if not r.ok:
        raise RuntimeError(f"PUT {path} → HTTP {r.status_code}: {r.text[:400]}")
    return r.json()


def pipedrive_delete(path: str, version: int = 2) -> dict:
    """
    Effectue un DELETE authentifié vers l'API Pipedrive.

    Args:
        path    : chemin de l'endpoint, ex: "/deals/42"
        version : version de l'API (1 ou 2)
    """
    _check_credentials()
    params = {"api_token": PIPEDRIVE_API_TOKEN}
    r = requests.delete(_base_url(version) + path, params=params, timeout=30)
    if not r.ok:
        raise RuntimeError(f"DELETE {path} → HTTP {r.status_code}: {r.text[:400]}")
    return r.json()


def paginate_all(path: str, params: dict = None, version: int = 2, max_items: int = 500) -> list:
    """
    Récupère TOUTES les pages d'un endpoint Pipedrive v2 (pagination par cursor).

    Pipedrive v2 utilise un système de cursor :
    - Chaque réponse contient additional_data.next_cursor
    - Tant que next_cursor est présent, il y a une page suivante
    - On itère jusqu'à épuisement ou jusqu'à max_items

    Args:
        path      : endpoint à paginer, ex: "/deals"
        params    : paramètres de filtrage additionnels
        version   : version API (2 par défaut, 1 pour les anciens endpoints)
        max_items : limite de sécurité pour éviter les boucles infinies

    Returns:
        list : tous les items collectés
    """
    _check_credentials()
    all_items = []
    base_params = {"api_token": PIPEDRIVE_API_TOKEN, "limit": 100}
    if params:
        base_params.update(params)

    cursor = None

    while True:
        if cursor:
            base_params["cursor"] = cursor

        r = requests.get(_base_url(version) + path, params=base_params, timeout=30)
        if not r.ok:
            raise RuntimeError(f"GET {path} → HTTP {r.status_code}: {r.text[:400]}")

        data = r.json()
        items = data.get("data") or []
        all_items.extend(items)

        # Vérification de la page suivante
        additional = data.get("additional_data") or {}
        next_cursor = additional.get("next_cursor")

        if not next_cursor or len(all_items) >= max_items:
            break

        cursor = next_cursor

    return all_items[:max_items]