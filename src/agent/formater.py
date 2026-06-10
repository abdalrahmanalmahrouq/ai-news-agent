from loguru import logger
from agent.state import AgentState


def render_card(index: int, article: dict) -> str:
    headline = article.get("headline", "Untitled")
    summary = article.get("summary", "")
    category = article.get("category", "Other")
    url = article.get("url", "#")

    return f"""
          <tr>
            <td style="padding:0 24px;">
              <span style="display:inline-block; font-family:Arial, Helvetica, sans-serif; font-size:11px; font-weight:bold; text-transform:uppercase; letter-spacing:0.5px; color:#2563eb; background-color:#eff6ff; padding:3px 8px; border-radius:4px;">{category}</span>
              <h3 style="font-family:Arial, Helvetica, sans-serif; font-size:17px; line-height:1.4; color:#111827; margin:8px 0 8px 0;">{index}. {headline}</h3>
              <p style="font-family:Arial, Helvetica, sans-serif; font-size:14px; line-height:1.6; color:#374151; margin:6px 0;">{summary}</p>
              <p style="margin:10px 0 0 0;">
                <a href="{url}" target="_blank" style="font-family:Arial, Helvetica, sans-serif; font-size:13px; color:#2563eb; text-decoration:none;">&#128279; Read Full Source</a>
              </p>
              <hr style="border:none; border-top:1px solid #e5e7eb; margin:22px 0;">
            </td>
          </tr>"""


def build_digest(intro: str, validated: list[dict]) -> str:
    ranked = sorted(validated, key=lambda a: a.get("relevance_score", 0), reverse=True)
    items = "".join(render_card(i + 1, a) for i, a in enumerate(ranked))

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>TECH News Digest</title>
</head>
<body style="margin:0; padding:0; background-color:#f3f4f6;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f3f4f6;">
    <tr>
      <td align="center" style="padding:24px 12px;">
        <table role="presentation" width="640" cellpadding="0" cellspacing="0" style="max-width:640px; width:100%; background-color:#ffffff;">
          <tr>
            <td style="padding:28px 24px 12px 24px;">
              <h1 style="font-family:Arial, Helvetica, sans-serif; font-size:24px; color:#111827; margin:0;">&#127760; Executive Technology News Briefing</h1>
              <hr style="border:none; border-top:2px solid #111827; margin:14px 0 0 0;">
            </td>
          </tr>
          <tr>
            <td style="padding:14px 24px 4px 24px;">
              <p style="font-family:Arial, Helvetica, sans-serif; font-size:15px; line-height:1.6; color:#374151; margin:0;">{intro}</p>
            </td>
          </tr>
          {items}
          <tr>
            <td style="padding:8px 24px 28px 24px; text-align:center;">
             <p style="font-family:Arial, Helvetica, sans-serif; font-size:12px; color:#9ca3af; margin:0;">You're receiving this because you subscribed to 
              <a href='https://technewsagent.indevs.in' style="text-decoration:none" target="_blank">Technewsagent</a>
              Digest.</p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def empty_digest() -> str:
    return build_digest(
        "No stories met the quality bar in this run. Check back next time.", [],
    )


async def formatter_node(state: AgentState) -> dict:
    validated = state.get("validated", [])

    if not validated:
        logger.warning("Formatter: no validated articles — building empty digest")
        return {"digest": empty_digest()}

    intro = f"Today's briefing covers {len(validated)} stories worth your attention."
    digest = build_digest(intro, validated)
    logger.info("✓ Formatter: built digest with {} articles", len(validated))
    return {"digest": digest}


if __name__ == "__main__":
    import asyncio

    sample = {
        "validated": [
            {"url": "https://example.com/a", "headline": "OpenRouter raises $113M Series B",
             "summary": "OpenRouter closed a large funding round. Capital expands infrastructure. Backers cited developer adoption.",
             "category": "Industry", "relevance_score": 0.9},
        ]
    }
    result = asyncio.run(formatter_node(sample))
    with open("sample_digest.html", "w") as f:
        f.write(result["digest"])
    logger.info("Wrote sample_digest.html")