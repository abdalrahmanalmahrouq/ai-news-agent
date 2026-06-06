import os
import smtplib
from datetime import datetime
from email.message import EmailMessage
from loguru import logger
from dotenv import load_dotenv
from agent.state import AgentState
from agent.persistence.subscriber_store import init_subscribers, get_active_subscribers

load_dotenv()


def get_digests_dir() -> str:
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    digests_dir = os.path.join(project_root, "data", "digests")
    os.makedirs(digests_dir, exist_ok=True)
    return digests_dir


def archive_digest(digest: str, run_id: str) -> str:
    """Write the digest to data/digests/ and return the file path."""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(get_digests_dir(), f"{run_id}_{timestamp}.html")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(digest)
    return filepath


def render_plaintext(validated: list[dict]) -> str:
    """A plain-text fallback for email clients that can't render HTML."""
    if not validated:
        return "No stories in this digest."
    lines = []
    for i, a in enumerate(validated, start=1):
        lines.append(f"{i}. {a.get('headline', '')}")
        lines.append(f"   {a.get('summary', '')}")
        lines.append(f"   {a.get('url', '')}")
        lines.append("")
    return "\n".join(lines)


def send_email(digest: str, validated: list[dict], recipient: str) -> bool:
    """Send the digest via SMTP. Returns True on success, False if skipped/failed."""
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASS")
    sender = os.getenv("EMAIL_FROM", user)

    if not all([host, user, password, recipient]):
        logger.warning("Delivery: SMTP not configured — skipping email")
        return False

    msg = EmailMessage()
    msg["Subject"] = f"Technology News Digest — {datetime.utcnow().strftime('%b %d, %Y')}"
    msg["From"] = sender
    msg["To"] = recipient
    msg.set_content(render_plaintext(validated))
    msg.add_alternative(digest, subtype="html")

    try:
        # timeout=20 means a stuck connection fails in 20s instead of hanging forever
        if port == 465:
            with smtplib.SMTP_SSL(host, port, timeout=20) as server:
                server.login(user, password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=20) as server:
                server.starttls()
                server.login(user, password)
                server.send_message(msg)
        logger.info("✓ Email sent to {}", recipient)
        return True
    except Exception as e:
        logger.error("Email failed to {} — {}", recipient, e)
        return False


async def delivery_node(state: AgentState) -> dict:
    digest = state.get("digest", "")
    validated = state.get("validated", [])
    run_meta = state.get("run_meta", {})
    run_id = run_meta.get("run_id", "unknown")

    if not digest:
        logger.warning("Delivery: no digest to deliver")
        run_meta["delivered_to"] = []
        return {"run_meta": run_meta}

    delivered_to = []

    # Output 1 — always archive (cheap, no credentials)
    filepath = archive_digest(digest, run_id)
    delivered_to.append(filepath)
    logger.info("✓ Digest archived → {}", filepath)

    if not validated:
        logger.warning("Delivery: no validated stories — skipping email")
        run_meta["delivered_to"] = delivered_to
        return {"run_meta": run_meta}

    admin_email = os.getenv("EMAIL_FROM") or os.getenv("SMTP_USER")
    # if admin_email:
    #     print(f"  \u2192 Admin copy \u2192 {admin_email}")
    #     if send_email(digest, validated, admin_email):
    #         delivered_to.append(f"email:{admin_email}")
    
    init_subscribers()
    subscribers = get_active_subscribers()
    admin_email = os.getenv("EMAIL_FROM") or os.getenv("SMTP_USER")
    logger.info("Broadcasting to {} subscriber(s)", len(subscribers))

    for sub in subscribers:
        recipient = sub["email"]
        if recipient == admin_email:
            continue
        logger.debug("  Sending to: {}", recipient)
        if send_email(digest, validated, recipient):
            delivered_to.append(f"email:{recipient}")

    run_meta["delivered_to"] = delivered_to
    return {"run_meta": run_meta}


if __name__ == "__main__":
    import asyncio

    sample_state = {
        "digest": "<!DOCTYPE html><html><body><h1>Test digest</h1></body></html>",
        "validated": [{"headline": "Test story", "summary": "A test.", "url": "https://x.com"}],
        "run_meta": {"run_id": "test1234"},
    }
    result = asyncio.run(delivery_node(sample_state))
    logger.info("delivered_to: {}", result["run_meta"]["delivered_to"])