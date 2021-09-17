"""
curl -X POST "https://dutycalls.me/api/ticket?channel=test"
-H  "accept: application/json"
-H  "Content-Type: application/json"
-d "{
    \"title\":\"This is the title of the ticket\",
    \"body\":\"This is the body of the ticket\",
    \"dateTime\":1565772510,\"severity\":\"medium\"
}"
"""
import json
import logging
import os
from aiohttp import ClientSession, ClientResponse, BasicAuth
from aiohttp.hdrs import METH_POST, METH_PUT
from typing import Optional
from .errors import DutyCallsRequestError, DutyCallsAuthError


class Client:

    BASE_URL = 'https://dutycalls.me/api'

    def __init__(self, login: str, password: str):
        """Initialize the DutyCalls.me Client.

        See https://docs.dutycalls.me/rest-api/#authentication for
        documentation on how to get creadentials.
        """
        authorization = BasicAuth(
            login=login,
            password=password,
            encoding='utf-8').encode()

        self._headers = {
            'Authorization': authorization,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        self._logger = logging.getLogger(__name__)

    async def _make_api_call(
            self,
            api: str,
            method: str,
            params: Optional[dict] = None,
            data: Optional[dict] = None) -> Optional[dict]:
        url = os.path.join(self.BASE_URL, api)
        data = json.dumps(data)
        async with ClientSession() as session:
            async with session.request(
                    method=method,
                    url=url,
                    headers=self._headers,
                    params=params,
                    data=data) as resp:
                if resp.status in (200, 201):
                    return await resp.json()
                if resp.status == 204:
                    return  # success, no content

                try:
                    err = await resp.json()
                    errmsg = err['error']
                except Exception:
                    try:
                        errmsg = await resp.text()
                    except Exception:
                        errmsg = 'unknown error occurred'
                if resp.status == 401:
                    raise DutyCallsAuthError(errmsg)
                raise DutyCallsRequestError(errmsg)

    async def new_ticket(self, ticket: dict, *channels: str, ) -> dict:
        """Create a new ticket and assign the ticket to a single channel."""
        res = await self._make_api_call(
            api='ticket',
            method=METH_POST,
            params=[('channel', channel) for channel in channels],
            data=ticket
        )
        return res['tickets']

    async def close_tickets(
            self,
            *ticket_sids: str,
            comment: Optional[str] = None) -> None:
        """Close one or more a ticket(s)."""
        data = {'status': 'closed'}
        if comment:
            data['comment'] = comment

        return await self._make_api_call(
            api='ticket',
            method=METH_PUT,
            params=[('sid', ticket_sid) for ticket_sid in ticket_sids],
            data=data)

    async def unacknowledge_tickets(
            self,
            *ticket_sids: str,
            comment: Optional[str] = None) -> None:
        """Unacknowledge one or more ticket(s)."""
        data = {'status': 'unacknowledged'}
        if comment:
            data['comment'] = comment

        return await self._make_api_call(
            api='ticket',
            method=METH_PUT,
            params=[('sid', ticket_sid) for ticket_sid in ticket_sids],
            data=data)
