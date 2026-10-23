"""Wallex Exchange REST API Client.

Provides asynchronous HTTP methods to interact with Wallex public and private
endpoints with rate limiting, timeouts, and error handling.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional
import httpx

logger = logging.getLogger(__name__)


class WallexAPIError(Exception):
  """Custom exception for Wallex API errors."""

  def __init__(self, message: str, status_code: int = 400, code: int = 0):
    super().__init__(message)
    self.status_code = status_code
    self.code = code


class WallexClient:
  """Async HTTP client for interacting with the Wallex API."""

  def __init__(
      self,
      base_url: str = "https://api.wallex.ir",
      api_key: Optional[str] = None,
      timeout_seconds: float = 10.0,
      rate_limit_per_minute: int = 60,
  ):
    self.base_url = base_url.rstrip("/")
    self.api_key = api_key
    self.timeout = timeout_seconds
    self.min_request_interval = 60.0 / rate_limit_per_minute
    self._last_request_time = 0.0
    self._lock = asyncio.Lock()
    self._session: Optional[httpx.AsyncClient] = None

  def _get_headers(self, requires_auth: bool = False) -> Dict[str, str]:
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "WallexAgenticTrader/1.0",
    }
    if requires_auth:
      if not self.api_key:
        raise WallexAPIError("API key is required for private endpoints", 401)
      headers["x-api-key"] = self.api_key
    return headers

  async def _get_session(self) -> httpx.AsyncClient:
    if self._session is None or self._session.is_closed:
      self._session = httpx.AsyncClient(timeout=self.timeout)
    return self._session

  async def close(self) -> None:
    if self._session and not self._session.is_closed:
      await self._session.aclose()
      self._session = None

  async def _request(
      self,
      method: str,
      endpoint: str,
      params: Optional[Dict[str, Any]] = None,
      json_data: Optional[Dict[str, Any]] = None,
      requires_auth: bool = False,
  ) -> Dict[str, Any]:
    url = f"{self.base_url}{endpoint}"
    headers = self._get_headers(requires_auth=requires_auth)

    async with self._lock:
      # Rate limiting
      loop = asyncio.get_running_loop()
      now = loop.time()
      elapsed = now - self._last_request_time
      if elapsed < self.min_request_interval:
        await asyncio.sleep(self.min_request_interval - elapsed)
      self._last_request_time = loop.time()

    session = await self._get_session()
    try:
      response = await session.request(
          method=method,
          url=url,
          params=params,
          json=json_data,
          headers=headers,
      )

      if response.status_code == 429:
        logger.warning(
            "Wallex rate limit reached (HTTP 429). Backing off for 2 seconds."
        )
        await asyncio.sleep(2.0)
        raise WallexAPIError("Rate limit exceeded", status_code=429)

      if response.status_code >= 400:
        logger.error(
            "Wallex API error %d for %s: %s",
            response.status_code,
            endpoint,
            response.text,
        )
        raise WallexAPIError(
            f"HTTP {response.status_code}: {response.text}",
            status_code=response.status_code,
        )

      return response.json()
    except httpx.RequestError as exc:
      logger.error("Network error during request to %s: %s", url, exc)
      raise WallexAPIError(f"Network error: {exc}", status_code=503)

  # Public methods
  async def get_markets(self) -> Dict[str, Any]:
    """Retrieve all available symbols and their metadata."""
    return await self._request("GET", "/v1/markets")

  async def get_depth(self, symbol: str) -> Dict[str, Any]:
    """Retrieve order book depth for a symbol."""
    return await self._request("GET", "/v1/depth", params={"symbol": symbol})

  async def get_trades(self, symbol: str) -> Dict[str, Any]:
    """Retrieve recent trades for a symbol."""
    return await self._request("GET", "/v1/trades", params={"symbol": symbol})

  async def get_udf_history(
      self,
      symbol: str,
      resolution: str,
      from_ts: int,
      to_ts: int,
  ) -> Dict[str, Any]:
    """Retrieve TradingView UDF OHLCV historical candle data."""
    params = {
        "symbol": symbol,
        "resolution": resolution,
        "from": from_ts,
        "to": to_ts,
    }
    return await self._request("GET", "/v1/udf/history", params=params)

  # Private authenticated methods
  async def get_balances(self) -> Dict[str, Any]:
    """Retrieve account balances across all assets."""
    return await self._request("GET", "/v1/account/balances", requires_auth=True)

  async def get_open_orders(self) -> Dict[str, Any]:
    """Retrieve all open orders."""
    return await self._request(
        "GET", "/v1/account/open-orders", requires_auth=True
    )

  async def place_order(
      self,
      symbol: str,
      order_type: str,
      side: str,
      price: str,
      quantity: str,
      client_order_id: Optional[str] = None,
  ) -> Dict[str, Any]:
    """Place a new spot order."""
    payload: Dict[str, Any] = {
        "symbol": symbol,
        "type": order_type.upper(),
        "side": side.upper(),
        "price": price,
        "quantity": quantity,
    }
    if client_order_id:
      payload["clientOrderId"] = client_order_id

    return await self._request(
        "POST", "/v1/account/orders", json_data=payload, requires_auth=True
    )

  async def cancel_order(
      self,
      order_id: Optional[str] = None,
      client_order_id: Optional[str] = None,
  ) -> Dict[str, Any]:
    """Cancel an active order by ID or clientOrderId."""
    params: Dict[str, Any] = {}
    if order_id:
      params["orderId"] = order_id
    elif client_order_id:
      params["clientOrderId"] = client_order_id
    else:
      raise ValueError("Either order_id or client_order_id must be provided")

    return await self._request(
        "DELETE", "/v1/account/orders", params=params, requires_auth=True
    )
