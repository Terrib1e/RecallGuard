# backend/worker/scrape_recalls.py
import os, requests, datetime as dt, sqlalchemy as sa
from app.core.database import SessionLocal, engine, Base
from app.core.models import Recall

CPSC_URL = "https://www.saferproducts.gov/RestWebServices/Recall?format=json"


def main():
    db = SessionLocal()
    recalls = requests.get(CPSC_URL, timeout=20).json()
    for r in recalls:
        # basic filter: skip >30 days old
        rec_date = dt.datetime.strptime(r["RecallDate"], "%m/%d/%Y")
        if (dt.datetime.utcnow() - rec_date).days > 30:
            continue
        db.merge(  # UPSERT by (brand, model)
            Recall(
                brand=r["Products"][0]["Brand"].strip(),
                model=r["Products"][0]["Model"].strip(),
                product_name=r["Products"][0]["Name"],
                recall_date=rec_date,
                details=r["Summary"],
                link=r["URL"],
            )
        )
    db.commit()
    db.close()


if __name__ == "__main__":
    main()
