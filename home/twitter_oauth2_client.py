"""
Custom OAuth2 Client for Twitter with proper Content-Type header
"""
from http import HTTPStatus
from urllib.parse import parse_qsl, urlencode
import requests
from allauth.socialaccount.adapter import get_adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client, OAuth2Error


class TwitterOAuth2Client(OAuth2Client):
    """Custom OAuth2 client for Twitter that ensures proper headers"""
    
    def get_access_token(self, code, pkce_code_verifier=None, extra_data=None):
        data = {
            "redirect_uri": self.callback_url,
            "grant_type": "authorization_code",
            "code": code,
        }
        
        if self.basic_auth:
            auth = requests.auth.HTTPBasicAuth(self.consumer_key, self.consumer_secret)
        else:
            auth = None
            data.update(
                {
                    self.client_id_parameter: self.consumer_key,
                    "client_secret": self.consumer_secret,
                }
            )
        
        if extra_data:
            data.update(extra_data)
        
        params = None
        self._strip_empty_keys(data)
        url = self.access_token_url
        
        if self.access_token_method == "GET":
            params = data
            data = None
        
        if data and pkce_code_verifier:
            data["code_verifier"] = pkce_code_verifier
        
        # Twitter OAuth2 requires Content-Type: application/x-www-form-urlencoded
        # Note: requests automatically URL-encodes dict data and sets Content-Type
        # but we explicitly set it to ensure Twitter accepts it
        headers = dict(self.headers) if self.headers else {}
        if data and self.access_token_method == "POST":
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        
        resp = (
            get_adapter()
            .get_requests_session()
            .request(
                self.access_token_method,
                url,
                params=params,
                data=data,
                headers=headers,
                auth=auth,
            )
        )
        
        access_token = None
        if resp.status_code in [HTTPStatus.OK, HTTPStatus.CREATED]:
            if (
                resp.headers.get("content-type", "").split(";")[0] == "application/json"
                or resp.text[:2] == '{"'
            ):
                access_token = resp.json()
            else:
                access_token = dict(parse_qsl(resp.text))
        
        if not access_token or "access_token" not in access_token:
            error_msg = f"Error retrieving access token: {resp.content}"
            raise OAuth2Error(error_msg)
        
        return access_token

