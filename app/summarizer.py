from utils.packages import *

def summarize(rows, metrics):
    logger.info(f"LLM Parse Running")
    try:
        api_key = os.getenv("LITELLM_KEY")

        client = OpenAI(api_key=api_key,
                        base_url="http://3.110.18.218")

        logger.info(f"Client Initialized")
        prompt = f"""
        You are a Analyst working as a GA4 analytics response summarizer.
        Summarize the results obtained by Google Analytics 4, Capture and highlight the key trends
        
        Return STRICT JSON ONLY.

        Query:
        {query}

        JSON format:
        {{
        "metrics": ["screenPageViews", "totalUsers"],
        "days": 14,
        "page_path": "/pricing"
        }}
        """
        logger.info(f"prompt is :- {prompt}")
        response = client.chat.completions.create(
            model="gemini-2.5-flash",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        logger.info(f"Response:{response}")
        return safe_json_loads(response.choices[0].message.content)
    # return response

    except Exception as e:
        # Any failure → fallback to rules
        logger.error(f"Error {e}")
        return None