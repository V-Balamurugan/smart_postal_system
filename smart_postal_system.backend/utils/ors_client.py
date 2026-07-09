import httpx
import logging
from typing import Any, Dict

from fastapi import HTTPException, status

from app.core.config import settings

logger = logging.getLogger(__name__)


class ORSClient:
    """
    OpenRouteService API Client.

    Responsible only for communicating with the ORS API.
    Business logic should remain in the service layer.
    """

    BASE_URL = "https://api.openrouteservice.org/v2"

    def __init__(self):
        self.api_key = settings.ORS_API_KEY

        if (
            not self.api_key
            or self.api_key == "your-ors-api-key-change-this-in-production"
        ):
            raise ValueError(
                "ORS_API_KEY is missing. Please configure it in the .env file."
            )

        self.headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        self.timeout = httpx.Timeout(
            timeout=30.0,
            connect=10.0,
        )

    async def get_driving_route(
        self,
        start_longitude: float,
        start_latitude: float,
        end_longitude: float,
        end_latitude: float,
    ) -> Dict[str, Any]:
        """
        Fetch optimized driving route from ORS.

        Parameters
        ----------
        start_longitude : float
        start_latitude : float
        end_longitude : float
        end_latitude : float

        Returns
        -------
        dict
            Complete ORS response.
        """

        url = f"{self.BASE_URL}/directions/driving-car"

        payload = {
            "coordinates": [
                [start_longitude, start_latitude],
                [end_longitude, end_latitude],
            ]
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url=url,
                    headers=self.headers,
                    json=payload,
                )

            response.raise_for_status()

            return response.json()

        except httpx.HTTPStatusError as exc:
            logger.exception("ORS returned an error.")

            try:
                error_detail = exc.response.json()
            except Exception:
                error_detail = exc.response.text

            raise HTTPException(
                status_code=exc.response.status_code,
                detail={
                    "message": "OpenRouteService API error.",
                    "error": error_detail,
                },
            )

        except httpx.TimeoutException:
            logger.exception("ORS request timed out.")

            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="OpenRouteService request timed out.",
            )

        except httpx.RequestError as exc:
            logger.exception("Unable to connect to ORS.")

            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Unable to connect to OpenRouteService: {exc}",
            )

        except Exception as exc:
            logger.exception("Unexpected ORS error.")

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected ORS client error: {exc}",
            )


ors_client = ORSClient()