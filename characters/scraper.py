import asyncio
import time
from asgiref.sync import sync_to_async

import httpx
from httpx import AsyncClient
from characters.models import Character


GRAPHQL_API_URL = "https://rickandmortyapi.com/graphql"

GET_CHARACTERS_QUERY = """
query ($page: Int!) {
    characters(page: $page) {
        info {
            pages
        }
        results {
          api_id: id
          name
          status
          species
          gender
          image
        }
      }
    }
"""


def parse_character_response(character_response: dict) -> list[Character]:
    return [
        Character(**character_dict)
        for character_dict in character_response["data"]["characters"]["results"]
    ]


async def scrape_single_page(
    client: AsyncClient, url_to_scrape: str, page: int
) -> list[Character]:
    try:
        response = await client.post(
            url_to_scrape,
            json={"query": GET_CHARACTERS_QUERY, "variables": {"page": page}},
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        data = response.json()
        if "data" not in data:
            print(f"No key 'data' in response for page {page}: {data}")
            return []
        return parse_character_response(data)
    except httpx.HTTPStatusError as e:
        print(f"Error HTTP in request page {page}: {e}. Response: {e.response.text}")
        return []
    except Exception as e:
        print(f"Unexpected error in page request {page}: {e}")
        return []


async def scrape_characters() -> list[Character]:
    start = time.perf_counter()

    url_to_scrape = GRAPHQL_API_URL
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url_to_scrape,
                json={"query": GET_CHARACTERS_QUERY, "variables": {"page": 1}},
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            characters_response = response.json()
            print(f"First response API: {characters_response}")
            if "errors" in characters_response:
                print(
                    f"Error GraphQL in first response: {characters_response['errors']}"
                )
                return []
            if "data" not in characters_response:
                print(f"No key 'data' in first response: {characters_response}")
                return []
            num_pages = characters_response["data"]["characters"]["info"]["pages"]
            characters = parse_character_response(characters_response)
        except httpx.HTTPStatusError as e:
            print(f"Error HTTP in first request: {e}. Response: {e.response.text}")
            return []
        except KeyError as e:
            print(
                f"Error in parse first response: {e}. Response: {characters_response}"
            )
            return []
        except Exception as e:
            print(f"Unexpected error in first request: {e}")
            return []

        tasks = [
            scrape_single_page(client, url_to_scrape, page)
            for page in range(2, num_pages + 1)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, list):
                characters.extend(result)
            else:
                print(f"Error in page handling: {result}")

    end = time.perf_counter()
    print(f"Take {len(characters)} characters in {end - start} sec.")
    return characters


async def save_characters(characters: list[Character]) -> None:
    """Save characters in DB."""
    start = time.perf_counter()
    if characters:
        await sync_to_async(Character.objects.bulk_create)(
            characters, ignore_conflicts=True, batch_size=1000
        )

    end = time.perf_counter()
    print(f"Saved {len(characters)} characters in {end - start} sec.")


async def sync_characters_with_api() -> None:
    """Synchronization characters with API."""
    characters = await scrape_characters()
    await save_characters(characters)
