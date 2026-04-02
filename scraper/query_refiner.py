from openai import OpenAI


def refine_query(raw_query: str, api_key: str) -> list[str]:
    """Use OpenAI GPT to refine a raw search query into optimized Google Maps search terms."""
    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a Google Maps search optimization expert. "
                    "Given a user's business search query, generate 2-3 optimized Google Maps search queries "
                    "that will return the most relevant business results. "
                    "Focus on queries that will find businesses with contact information. "
                    "Return ONLY the queries, one per line, no numbering or bullets."
                ),
            },
            {
                "role": "user",
                "content": f"Generate optimized Google Maps search queries for: {raw_query}",
            },
        ],
        temperature=0.7,
        max_tokens=200,
    )

    result = response.choices[0].message.content.strip()
    queries = [q.strip() for q in result.split("\n") if q.strip()]
    return queries
