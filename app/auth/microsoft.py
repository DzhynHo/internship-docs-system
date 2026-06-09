import msal
from flask import current_app

AUTHORITY = "https://login.microsoftonline.com/{}"
SCOPE = ["User.Read"]

def microsoft_configured():
    cfg = current_app.config
    return all([
        cfg.get("MICROSOFT_CLIENT_ID"),
        cfg.get("MICROSOFT_CLIENT_SECRET"),
        cfg.get("MICROSOFT_TENANT_ID"),
        cfg.get("MICROSOFT_REDIRECT_URI"),
    ])

def _build_msal_app():
    cfg = current_app.config
    return msal.ConfidentialClientApplication(
        cfg["MICROSOFT_CLIENT_ID"],
        authority=AUTHORITY.format(cfg["MICROSOFT_TENANT_ID"]),
        client_credential=cfg["MICROSOFT_CLIENT_SECRET"],
    )

def get_auth_url():
    if not microsoft_configured():
        return None, None
    flow = _build_msal_app().initiate_auth_code_flow(
        SCOPE,
        redirect_uri=current_app.config["MICROSOFT_REDIRECT_URI"],
    )
    # Force response_mode to 'query' for local/dev usage so that the
    # browser performs a top-level GET redirect and the Flask session
    # cookie (SameSite=Lax) is sent. MSAL recommends form_post for
    # security, but form_post may not send cookies in some dev setups.
    auth_uri = flow.get("auth_uri")
    if auth_uri and "response_mode=" not in auth_uri:
        sep = "&" if "?" in auth_uri else "?"
        auth_uri = f"{auth_uri}{sep}response_mode=query"
        flow["auth_uri"] = auth_uri

    if flow is None:
        return None, None
    return flow["auth_uri"], flow

def get_token_from_code(auth_response, flow):
    result = _build_msal_app().acquire_token_by_auth_code_flow(
        flow, auth_response
    )
    return result

def get_user_info(token):
    import requests
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(
        "https://graph.microsoft.com/v1.0/me",
        headers=headers
    )
    resp.raise_for_status()
    data = resp.json()
    return {
        "email":       data.get("mail") or data.get("userPrincipalName"),
        "full_name":   data.get("displayName"),
        "external_id": data.get("id"),
        "tenant":      data.get("userPrincipalName", "").split("@")[-1],
    }