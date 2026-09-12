# Telegram Store Bot — Moon Bot

aiogram 3.x. Covers Stages 2-3 and now 6 from the master prompt: `/start`,
language, documents + acceptance, main menu, account, Telegram Stars
payments, and the module Store + "My Modules" (categories, search,
install/enable/disable/update/delete). Connect Userbot / Core pairing UI
and Custom Modules (Stage 7) come later - their menu buttons still reply
with a "coming soon" message.

## Requirements

- Python 3.12+
- A running Backend (see `../backend`) reachable at `BACKEND_URL`
- A bot token from @BotFather

## Install

```bash
pip install -r requirements.txt --break-system-packages
```

## Configuration

```bash
cp .env.example .env
```

`BACKEND_SERVICE_TOKEN` must be the exact same value as Backend's
`BOT_INTERNAL_TOKEN` — it's how Backend knows this request came from the
Bot and not from someone else (section 50).

Before the bot is useful, Backend needs at least one row per document
type in its `documents` table (terms/privacy/eula), each with
`is_current = true` and a real URL — otherwise `/documents/current`
comes back empty and the acceptance step has nothing to show. There's no
seed script for this yet since document text/URLs are yours to write;
insert them directly via SQL or a small script once you have the actual
Terms/Privacy/EULA text hosted somewhere.

## Running

```bash
python main.py
```

Long-polling, no webhook setup needed for now.

## Localization

`localization/ru.json` / `en.json`, loaded through
`localization.loader.t(key, lang, **kwargs)` — dotted keys, falls back to
Russian and then to the raw key if something's missing, so a typo in a
key never crashes a handler. Add a string to both files when you add a
new one; nothing enforces that they stay in sync yet (worth a lint check
once there are more languages).

## Store & My Modules (Stage 6)

The Store never talks to Core directly (section 51). Tapping "Install"
does two things in sequence:

1. `POST /modules/install` on Backend - the actual license + module-limit
   check (section 28-29), answered immediately so the user gets instant
   "✅ sent" or "❌ denied: module_limit_reached" feedback.
2. `POST /commands` - queues an `install_module` command that Core picks
   up on its own polling loop (10s interval) and executes for real
   (download, verify, load). Enable/disable/update/delete work the same
   way: an immediate Backend record update + a queued command for Core
   to actually apply it on disk.

Categories are just a fixed set of codes (`popular`, `new`, `utilities`,
`automation`, `moderation`) matched against `Module.category` - a
Creator publishing a module needs to use one of these exact strings for
it to show up under a category (not enforced anywhere yet, just a
convention - Backend's `category` column is free text).

Search is the first real use of `bot/states/` - FSM state for "the next
message is a search query", since that's genuinely local conversational
state Backend has no reason to track.

## Custom Modules (Stage 7)

"📤 Upload custom module" lives at the bottom of My Modules (shows even
when the list is empty). The flow: send a `.zip` (≤10 MB) →
`POST /modules/custom/upload` on Backend for technical validation only
(valid zip, size, Custom VIP entitlement - never a code review, section
34) → the mandatory risk warning from section 33, verbatim, in both
languages → `[✅ Install]` reuses the exact same `/modules/install` +
command-queue flow official modules use. `[❌ Cancel]` just drops it;
there's no "delete an unconfirmed upload" cleanup since Backend
overwrites the same `(account, module_id)` row on the next upload
attempt anyway.

If the .zip contains a `manifest.json` (section 32's "если
предусмотрен"), Backend reads name/version/description from it; if not,
it falls back to the filename and version "1.0.0". Either way the actual
module_id is `custom.<your_account_id>.<sanitized_name>`, assigned by
Backend, not something you pick directly - see the Backend README for
why (per-account namespacing to avoid ID collisions across customers).

## Connect Userbot & Duo (Stage 8, and a Stage-4 gap it fixed)

**Important correction:** Core has printed a pairing code and told people
to send it to Moon Bot since Stage 4, but until this stage the Bot had
no handler that actually received and confirmed that code -
"🖥 Connect Userbot" was a coming-soon stub the whole time. That's fixed
now: `bot/handlers/connect.py` shows the mandatory risk warning (section
42), then a two-way fork per section 73:

- **🖥 Own server** — install guides (GitHub/Termux/VPS/generic install,
  all from `.env`), then the bot waits for a plain-text message and
  calls `POST /devices/pair/confirm` with it. This is the only path that
  exists right now, and it's the safe one: the phone/OTP/2FA handshake
  happens entirely inside Core, on the user's own machine, exactly per
  sections 44-45.
- **⭐ Platform server** — currently just points to support
  (`SUPPORT_URL`), on purpose. A hosted option that has *this bot*
  prompt for a phone number, then a login code, then a 2FA password
  would be functionally identical to a Telegram account-takeover scam,
  regardless of intent - a compromised Bot/Backend would mean a
  compromised Telegram account for every customer who'd used it, not
  just their subscription data. Sections 44-45 and 102's own "never
  send OTP/2FA/session through Bot" rules already rule this out; a real
  platform-hosted offering needs the same login handshake to still
  happen against an isolated Core process the customer (or a support
  agent, with them present) interacts with directly - that's a separate
  piece of infrastructure to design deliberately, not something to bolt
  onto this chat flow.

If you deployed Stages 4-7 for real users before this, nobody could
actually finish connecting via the self-hosted path either - sorry about
that, and it's why this stage front-loaded fixing it over the Duo UI it
was originally scoped for.

Duo itself: `bot/handlers/account.py`'s account view now checks how many
accounts you have. One → unchanged from Stage 2. Two → a switcher
first, then per-account details (module count now shown for real,
prefix shown read-only - prefix stays a Core-only `.prefix` command per
section 19, not something this bot edits). Devices are filtered
client-side by `account_id` from the same `GET /devices` call rather
than needing a new Backend endpoint. Removing the second account calls
the new `DELETE /accounts/{id}` (see Backend's design notes for why that
needed a real cascade instead of reusing the device-delete endpoint).

**A second, smaller thing this stage fixed while it was in the
neighborhood:** `bot/states/store.py`'s search prompt and
`custom_modules.py`'s zip-upload prompt would previously swallow a main
menu tap as if it were the expected input (typing "👤 Мой аккаунт" while
the bot was waiting for a search query would search for literally
that). `bot/menu_labels.py` now holds every menu button label across
both languages; FSM-scoped handlers exclude them so the tap falls
through to `menu.py` instead, and `UserContextMiddleware` clears any
leftover FSM state on a menu tap so it can't linger and swallow a later,
unrelated message either. The new pairing-code handler uses the same
pattern from the start.

## Creator Panel / Payments

`CREATOR_IDS` / `ADMIN_IDS` are already read into config for when the
Creator Panel lands (Stage 9) - not wired up yet.

Payments are live: `bot/handlers/payments.py` handles plan selection,
duration selection (Pro/Duo have month/3-month/year, Basic is
month-only), Custom VIP, and the full `send_invoice` →
`pre_checkout_query` → `successful_payment` → `POST /payments/confirm`
chain. Prices come from Backend's `GET /plans` at the moment the invoice
is built, not from anything hardcoded in the bot - change a price in
Backend's `plan_prices` table and the bot picks it up on the next tap,
no redeploy needed. Custom VIP's price is the one exception
(`payments/pricing.py`) since it isn't a subscription plan/duration row.

## Testing

```bash
pytest
```

Only `tests/test_localization.py` right now. This stage added ~24 new
keys (`account.*` additions, all of `connect.*`) - same cross-check as
before, and I verified it actually resolves 100 distinct `t()` calls
across all of `bot/` in both languages by grepping the real source, not
eyeballing the JSON. I still could not install/run aiogram itself in
this sandbox (no network) - please run the bot for real and specifically
check:
- **Connect Userbot end to end**: warning → install options → paste a
  real code from a running Core instance → confirm it actually pairs.
  This is the single most important thing to verify since it was silently
  broken since Stage 4.
- **The menu-label escape hatch**: start a search, then tap a main menu
  button instead of typing a query, and confirm it navigates normally
  instead of searching for the button's own label text. I could not
  verify `data.get("state")` is populated in `UserContextMiddleware`
  the way I expect (i.e. that aiogram's FSM context middleware runs
  before user-registered `.message.middleware()` calls) without actually
  running the dispatcher - if the fix doesn't take effect, this
  assumption is the first thing to check.
- **Duo**: pair two Core instances under one Duo subscription, confirm
  the account switcher shows both, and that removing the second one
  actually deactivates its device.

## Design decisions worth double-checking

1. **Onboarding is stateless** — no aiogram FSM storage. Each step
   (language set? which document is still pending?) is recomputed from
   Backend on every message/callback. Simpler and avoids local/Backend
   state drifting apart, at the cost of one extra HTTP round-trip per
   step. `bot/states/` is now used for genuinely local, conversational
   state (the store search prompt, the custom module upload prompt) -
   see its docstring for the line between the two.
2. **A middleware fetches the Backend user on every update**
   (`UserContextMiddleware`) rather than caching it anywhere locally, for
   the same reason. This means every button press costs one Backend call
   before the handler even runs; fine at this scale, worth revisiting if
   Backend latency ever becomes noticeable.
3. **The "coming soon" menu items are honest stubs, not fake ones** —
   tapping them replies with a plain "not yet" message rather than
   showing fabricated data (no fake module list, no fake device pairing
   flow). The four sections gated this way are exactly the ones that
   need functionality that doesn't exist yet in another repo (Core) or
   another stage (Store catalog, Referrals).
4. **`/documents/current` returning nothing is an env/data problem, not
   a code bug** — see the Configuration note above about seeding real
   document rows in Backend.
5. **No stale-price race window** — the bot re-fetches `GET /plans`
   right before building each invoice rather than caching prices from an
   earlier screen, so a price change in Backend takes effect immediately
   without a mismatch between what the button showed and what the
   invoice charges.
6. **`pre_checkout_query` always answers `ok=True`** — there's nothing
   left to validate at that point since the price was just pulled fresh;
   if you add stock limits or per-user purchase caps later, that's where
   the check goes.
7. **Install/enable/disable/update/delete each fire two Backend calls**
   (an immediate record update + a queued command) rather than one -
   documented above under Store & My Modules. This means the Backend
   record and what Core has actually done on disk can be briefly out of
   sync (a few seconds, normally) - acceptable here since "installed"
   is really about entitlement/intent, not a live process-state mirror.
8. **My Modules and Store still act on the primary account only** -
   only the Account view got a Duo switcher this stage (it's the screen
   section 39 explicitly calls out for per-account display). Installing
   or managing modules always targets the primary account's `account_id`
   for now, even for a Duo customer with two - a real gap, not a
   deliberate design choice, and worth closing before Duo ships to real
   users with a second account they actually want to manage modules on.
9. **The custom-module warning text is exactly section 33's wording**,
   translated, not paraphrased or shortened - it's a liability-relevant
   disclosure, not just UX copy, so I kept it verbatim in both languages
   rather than tightening it for tone.
10. **Prefix is shown, not editable, from the Bot** - section 19 frames
    `.prefix` as a Core chat command exclusively, with no Bot-side
    mention anywhere in the master prompt. Backend's
    `POST /accounts/prefix` stayed Core-token-only rather than opening it
    to the Bot too, to avoid adding a feature the spec doesn't ask for.
11. **A stray Telegram message that happens to be 1-16 characters could
    still be misread as a pairing code** if the user is in
    `waiting_for_pairing_code` state and types something unrelated (that
    isn't a menu label) - Backend's own `invalid_code` response catches
    this safely, just with a slightly confusing error message rather
    than a clearly-wrong-format one. Not fixed here since Backend already
    guards the actual security boundary; a tighter client-side regex
    would only improve the error message, not the safety.

## What's next

Store and My Modules still act on the primary account only (noted below
under design decisions) - a natural Stage-8 follow-up would extend the
same account-switcher pattern from `account.py` to those two screens.
Stage 9: a Creator Panel screen for publishing and verifying official/
custom modules (`POST /modules`, `POST /modules/{id}/verify` on Backend
already exist and only need a form here). Stage 10: Referrals (schema
exists, service/API layer doesn't yet).
