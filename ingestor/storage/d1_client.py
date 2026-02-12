#!/usr/bin/env python3
"""
Cloudflare D1 client (skeleton).
This module provides a minimal interface to execute SQL against a Cloudflare D1 database.
"""
from __future__ import annotations

from typing import Any, Dict, List
import requests


class D1Client:
    def __init__(self, account_id: str, db_name: str, api_token: str, base_url: str = "https://api.cloudflare.com/client/v4"):
        self.account_id = account_id
        self.db_name = db_name
        self.api_token = api_token
        self.base_url = base_url.rstrip("/")

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

    def execute(self, sql: str, params: List[Any] | None = None) -> Dict[str, Any]:
        """
        Execute a D1 SQL statement (DDL/DML).
        This is a skeleton implementation; adapt to Cloudflare's actual D1 REST API.
        """
        payload = {"query": sql, "params": params or []}
        url = f"{self.base_url}/accounts/{self.account_id}/storage/d1/databases/{self.db_name}/execute"
        resp = requests.post(url, headers=self._headers(), json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("success", True):
            raise RuntimeError(f"D1 execute failed: {data}")
        return data

    def fetch(self, sql: str, params: List[Any] | None = None) -> List[Dict[str, Any]]:
        """
        Query data from D1 (SELECT).
        """
        payload = {"query": sql, "params": params or []}
        url = f"{self.base_url}/accounts/{self.account_id}/storage/d1/databases/{self.db_name}/query"
        resp = requests.post(url, headers=self._headers(), json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data.get("results", [])
