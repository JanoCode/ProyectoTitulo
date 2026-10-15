"""Cliente único utilizado por el desktop para comunicarse con la API."""

from ergosense.api_client.client import ApiClient, ApiClientError

__all__ = ["ApiClient", "ApiClientError"]
