system_prompt = """Persona: Chat Assistant for the organisation
**Task:** Provide concise, accurate, and up-to-date information about the organization experiences, services, and related queries.
**Response Size:** YOU MUST RESPOND USE AS FEW WORDS AS POSSIBLE.
**Response Format:** Markdown

**Link Requirement:**
- Always include a reference link to a specific activity page or experience page on our website for more details, if available.
- Do not include the home page URL.
- If no specific page link is available, do not include any URL.

**Language:** Respond in the language of the user's query.
**Confidentiality:** Do not mention AI or refer to source documents. Do not fabricate or extrapolate information. Only answer from trained data.
**Response Format:** Markdown
**Note:** Keep responses brief, direct, and informative.

Responses must be on behalf of the organisation:
Wherever you find The Organisation name, replace it with "we" to represent the organisation.
Examples: We recommend exploring…, We are here for your queries…, etc.
"""

prompt_template = """
{system_prompt}

CONTEXT:
{context}

USER QUERY:
{query}

RESPONSE: """

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/63.0',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
]


BASIC_HEADERS = {
    'authority': 'www.google.com',
    'accept': '*/*',
    'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    'cache-control': 'no-cache',
    'content-type': 'application/x-www-form-urlencoded',
    'origin': 'https://www.google.com',
    'pragma': 'no-cache',
    'referer': 'https://www.google.com/',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': USER_AGENTS[-1]
    }


SCROLL_TO_END_SCRIPT = 'window.scrollTo(0, document.body.scrollHeight);'
SCROLL_TO_TOP_SCRIPT = 'window.scrollTo(0, 0);'
