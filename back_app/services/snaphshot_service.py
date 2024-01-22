from config.settings import Context


def get_last_affiliate_snapshot_for(context: Context, affiliate: str):
    from app.models import AffiliateSnapshot

    snapshots = (
        AffiliateSnapshot.select()
        .where(
            AffiliateSnapshot.tenant == context.tenant,
            AffiliateSnapshot.name == affiliate,
        )
        .order_by(AffiliateSnapshot.timestamp.desc())
        .limit(1)
        .execute()
    )
    return snapshots[0] if len(snapshots) > 0 else None


def get_last_hedger_snapshot_for(context: Context, hedger: str):
    from app.models import HedgerSnapshot

    snapshots = (
        HedgerSnapshot.select()
        .where(
            HedgerSnapshot.tenant == context.tenant,
            HedgerSnapshot.name == hedger,
        )
        .order_by(HedgerSnapshot.timestamp.desc())
        .limit(1)
        .execute()
    )
    return snapshots[0] if len(snapshots) > 0 else None
