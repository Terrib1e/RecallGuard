# backend/worker/match_and_notify.py
import os, sqlalchemy as sa
from app.core.database import SessionLocal
from app.core.models import Recall, Product, User
from sentence_transformers import SentenceTransformer, util
from twilio.rest import Client
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

SIM_THRESHOLD = 0.85
model = SentenceTransformer("all-MiniLM-L6-v2")

twilio = Client(os.getenv("TWILIO_SID"), os.getenv("TWILIO_TOKEN"))
sendgrid = SendGridAPIClient(os.getenv("SENDGRID_KEY"))


def send_sms(phone: str, msg: str):
    twilio.messages.create(from_=os.getenv("TWILIO_FROM"), to=phone, body=msg)


def send_email(email: str, subject: str, html: str):
    mail = Mail(
        from_email="alerts@recallguard.com",
        to_emails=email,
        subject=subject,
        html_content=html,
    )
    sendgrid.send(mail)


def notify(user: User, product: Product, recall: Recall):
    msg = (
        f"Recall alert: {product.brand} {product.model}\n"
        f"{recall.details[:140]}...\n{recall.link}"
    )
    if user.phone:
        send_sms(user.phone, msg)
    send_email(user.email, "Recall Alert", msg)


def main():
    db = SessionLocal()
    products = db.query(Product).all()
    recalls = db.query(Recall).all()

    # Pre-compute recall embeddings once
    recall_embeds = {
        rec.id: model.encode(f"{rec.brand} {rec.model} {rec.product_name}")
        for rec in recalls
    }

    for prod in products:
        prod_text = f"{prod.brand} {prod.model} {prod.product_name}"
        prod_emb = model.encode(prod_text)
        for rec in recalls:
            sim = util.cos_sim(prod_emb, recall_embeds[rec.id]).item()
            if sim >= SIM_THRESHOLD:
                notify(prod.owner, prod, rec)
    db.close()


if __name__ == "__main__":
    main()
