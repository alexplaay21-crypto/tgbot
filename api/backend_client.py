import httpx

from config.settings import settings


class BackendClient:
    """
    All calls carry X-Service-Token: BACKEND_SERVICE_TOKEN, matching
    Backend's require_bot_token dependency (section 50). Backend is
    always the source of truth (section 89) - this client never caches
    anything locally.
    """

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=settings.BACKEND_URL,
            headers={"X-Service-Token": settings.BACKEND_SERVICE_TOKEN},
            timeout=10.0,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def auth_bot(self, telegram_user_id: int, username: str | None) -> dict:
        resp = await self._client.post(
            "/auth/bot", json={"telegram_user_id": telegram_user_id, "username": username}
        )
        resp.raise_for_status()
        return resp.json()

    async def get_user_by_telegram_id(self, telegram_user_id: int) -> dict | None:
        resp = await self._client.get("/users/by-telegram-id", params={"telegram_user_id": telegram_user_id})
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()

    async def set_language(self, telegram_user_id: int, language: str) -> dict:
        resp = await self._client.post(
            "/users/language", json={"telegram_user_id": telegram_user_id, "language": language}
        )
        resp.raise_for_status()
        return resp.json()

    async def current_documents(self) -> list[dict]:
        resp = await self._client.get("/documents/current")
        resp.raise_for_status()
        return resp.json()

    async def pending_documents(self, telegram_user_id: int) -> list[dict]:
        resp = await self._client.get("/documents/pending", params={"telegram_user_id": telegram_user_id})
        resp.raise_for_status()
        return resp.json()

    async def accept_document(self, telegram_user_id: int, document_type: str, version: str) -> None:
        resp = await self._client.post(
            "/documents/accept",
            json={"telegram_user_id": telegram_user_id, "document_type": document_type, "version": version},
        )
        resp.raise_for_status()

    async def get_subscription(self, telegram_user_id: int) -> dict:
        resp = await self._client.get(f"/subscriptions/{telegram_user_id}")
        resp.raise_for_status()
        return resp.json()

    async def get_purchases(self, telegram_user_id: int) -> list[dict]:
        resp = await self._client.get(f"/purchases/{telegram_user_id}")
        resp.raise_for_status()
        return resp.json()

    async def get_devices(self, telegram_user_id: int) -> list[dict]:
        resp = await self._client.get("/devices", params={"telegram_user_id": telegram_user_id})
        resp.raise_for_status()
        return resp.json()

    async def confirm_pairing(self, code: str, telegram_user_id: int) -> dict:
        """The Bot-side half of device pairing (section 40/97) - Core
        prints the code, whoever sends it here (via Moon Bot, so their
        identity is authenticated by Telegram itself) redeems it."""
        resp = await self._client.post(
            "/devices/pair/confirm", json={"code": code, "telegram_user_id": telegram_user_id}
        )
        resp.raise_for_status()
        return resp.json()

    async def delete_account(self, account_id: int, requester_telegram_id: int) -> dict:
        resp = await self._client.delete(
            f"/accounts/{account_id}", params={"requester_telegram_id": requester_telegram_id}
        )
        resp.raise_for_status()
        return resp.json()

    async def list_accounts(self, telegram_user_id: int) -> list[dict]:
        resp = await self._client.get("/accounts", params={"telegram_user_id": telegram_user_id})
        resp.raise_for_status()
        return resp.json()

    async def list_modules(self, category: str | None = None) -> list[dict]:
        params = {"category": category} if category else {}
        resp = await self._client.get("/modules", params=params)
        resp.raise_for_status()
        return resp.json()

    async def get_module(self, module_id: str) -> dict:
        resp = await self._client.get(f"/modules/{module_id}")
        resp.raise_for_status()
        return resp.json()

    async def list_installed_modules(self, account_id: int) -> list[dict]:
        resp = await self._client.get("/modules/installed", params={"account_id": account_id})
        resp.raise_for_status()
        return resp.json()

    async def install_module(self, account_id: int, module_id: str) -> dict:
        """Section 28: this is the immediate allow/deny check - raises
        httpx.HTTPStatusError(403) with a reason if denied (limit reached,
        plan doesn't cover it, etc.)."""
        resp = await self._client.post(
            "/modules/install", json={"account_id": account_id, "module_id": module_id}
        )
        resp.raise_for_status()
        return resp.json()

    async def uninstall_module(self, account_id: int, module_id: str) -> dict:
        resp = await self._client.post(
            "/modules/uninstall", json={"account_id": account_id, "module_id": module_id}
        )
        resp.raise_for_status()
        return resp.json()

    async def toggle_module(self, account_id: int, module_id: str, enabled: bool) -> dict:
        resp = await self._client.post(
            "/modules/toggle",
            json={"account_id": account_id, "module_id": module_id, "enabled": enabled},
        )
        resp.raise_for_status()
        return resp.json()

    async def create_command(self, account_id: int, type_: str, payload: dict) -> dict:
        """Section 51: this is how the Bot ever gets Core to actually DO
        something - it never talks to Core directly."""
        resp = await self._client.post(
            "/commands", json={"account_id": account_id, "type": type_, "payload": payload}
        )
        resp.raise_for_status()
        return resp.json()

    async def upload_custom_module(self, account_id: int, name: str, filename: str, data: bytes) -> dict:
        """Section 31-32: Backend does technical validation only and
        assigns the account-namespaced module_id - no admin approval step."""
        resp = await self._client.post(
            "/modules/custom/upload",
            data={"account_id": str(account_id), "name": name},
            files={"file": (filename, data, "application/zip")},
        )
        resp.raise_for_status()
        return resp.json()

    async def upload_official_module(
        self,
        module_id: str,
        name: str,
        description: str,
        category: str,
        access_type: str,
        core_version_requirement: str,
        version: str,
        icon_file_id: str,
        creator_telegram_id: int,
        filename: str,
        data: bytes,
    ) -> dict:
        resp = await self._client.post(
            "/modules/official/upload",
            data={
                "module_id": module_id,
                "name": name,
                "description": description,
                "category": category,
                "access_type": access_type,
                "core_version_requirement": core_version_requirement,
                "version": version,
                "icon_file_id": icon_file_id,
                "creator_telegram_id": str(creator_telegram_id),
            },
            files={"file": (filename, data, "application/zip")},
        )
        resp.raise_for_status()
        return resp.json()

    async def verify_module(self, module_id: str, creator_telegram_id: int) -> dict:
        resp = await self._client.post(
            f"/modules/{module_id}/verify",
            params={"creator_telegram_id": creator_telegram_id},
        )
        resp.raise_for_status()
        return resp.json()

    async def create_promo_code(
        self,
        code: str,
        type_: str,
        plan_code: str | None,
        bonus_days: int | None,
        discount_percent: int | None,
        usage_limit: int | None,
        expires_in_days: int | None,
        creator_telegram_id: int,
    ) -> dict:
        resp = await self._client.post(
            "/promocodes",
            json={
                "code": code,
                "type": type_,
                "plan_code": plan_code,
                "bonus_days": bonus_days,
                "discount_percent": discount_percent,
                "usage_limit": usage_limit,
                "expires_in_days": expires_in_days,
                "creator_telegram_id": creator_telegram_id,
            },
        )
        resp.raise_for_status()
        return resp.json()

    async def redeem_promo_code(self, telegram_user_id: int, code: str) -> dict:
        resp = await self._client.post(
            "/promocodes/redeem",
            json={
                "telegram_user_id": telegram_user_id,
                "code": code,
            },
        )
        resp.raise_for_status()
        return resp.json()

    async def get_pending_discount(self, telegram_user_id: int) -> int | None:
        resp = await self._client.get(
            "/promocodes/pending-discount",
            params={"telegram_user_id": telegram_user_id},
        )
        resp.raise_for_status()
        return resp.json().get("discount_percent")

    async def list_admin_users(
        self,
        creator_telegram_id: int,
        limit: int = 20,
    ) -> list[dict]:
        resp = await self._client.get(
            "/admin/users",
            params={
                "creator_telegram_id": creator_telegram_id,
                "limit": limit,
            },
        )
        resp.raise_for_status()
        return resp.json()

    async def get_admin_stats(self, creator_telegram_id: int) -> dict:
        resp = await self._client.get(
            "/admin/stats",
            params={"creator_telegram_id": creator_telegram_id},
        )
        resp.raise_for_status()
        return resp.json()

    async def flag_user(
        self,
        creator_telegram_id: int,
        target_telegram_user_id: int,
        reason: str,
    ) -> dict:
        resp = await self._client.post(
            "/moderation/flag",
            json={
                "creator_telegram_id": creator_telegram_id,
                "target_telegram_user_id": target_telegram_user_id,
                "reason": reason,
            },
        )
        resp.raise_for_status()
        return resp.json()

    async def list_moderation_flags(
        self,
        creator_telegram_id: int,
        telegram_user_id: int | None = None,
    ) -> list[dict]:
        params = {"creator_telegram_id": creator_telegram_id}

        if telegram_user_id is not None:
            params["telegram_user_id"] = telegram_user_id

        resp = await self._client.get(
            "/moderation/flags",
            params=params,
        )
        resp.raise_for_status()
        return resp.json()

    async def list_plans(self) -> list[dict]:
        resp = await self._client.get("/plans")
        resp.raise_for_status()
        return resp.json()

    async def confirm_payment(
        self,
        telegram_user_id: int,
        kind: str,
        plan_code: str | None,
        duration: str | None,
        stars_amount: int,
        provider_charge_id: str,
    ) -> dict:
        """Section 52-53: only ever called after Telegram's own
        successful_payment update, never from a bare button tap."""
        resp = await self._client.post(
            "/payments/confirm",
            json={
                "telegram_user_id": telegram_user_id,
                "kind": kind,
                "plan_code": plan_code,
                "duration": duration,
                "stars_amount": stars_amount,
                "provider_charge_id": provider_charge_id,
            },
        )
        resp.raise_for_status()
        return resp.json()


backend_client = BackendClient()
