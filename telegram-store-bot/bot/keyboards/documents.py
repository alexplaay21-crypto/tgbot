from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from localization.loader import t


def document_keyboard(document: dict, lang: str) -> InlineKeyboardMarkup:
    label = t(f"documents.type_{document['document_type']}", lang)
    rows = []
    if document.get("url"):
        rows.append([InlineKeyboardButton(text=label, url=document["url"])])
    rows.append(
        [
            InlineKeyboardButton(
                text=t("documents.accept_button", lang),
                callback_data=f"accept_doc:{document['document_type']}:{document['version']}",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)
