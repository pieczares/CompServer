from services.get_links import get_links


def fetch_product_links(hurtownia_url: str) -> list[str]:
    raw_links = get_links(hurtownia_url, 5, 500)

    if not isinstance(raw_links, list):
        raise TypeError(
            "Funkcja pobierająca linki musi zwracać listę."
        )

    cleaned_links: list[str] = []
    seen: set[str] = set()

    for link in raw_links:
        if not isinstance(link, str):
            raise TypeError(
                "Każdy element listy linków musi być napisem."
            )

        link = link.strip()

        if not link:
            continue

        if len(link) > 255:
            raise ValueError(
                "Pobrany link przekracza limit kolumny link "
                f"(255 znaków): {link}"
            )

        if link not in seen:
            seen.add(link)
            cleaned_links.append(link)

    return cleaned_links