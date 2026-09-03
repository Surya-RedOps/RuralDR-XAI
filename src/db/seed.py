"""
RuralDR-XAI: Database Metadata Seeder (SIH26038)
Populates ONLY foundational administrative geographical metadata:
- States, Districts (Locations)
- Primary Healthcare Centres (Healthcare Centres)

CRITICAL POLICY:
DO NOT seed fake application data.
DO NOT seed fake patients, fake doctors, fake healthcare workers, fake referrals,
fake screening cases, fake AI predictions, fake lesion findings, or fake hospitals.
The database starts clean for real user registrations and dynamic screenings.
"""

from sqlalchemy.orm import Session
from .models import Location, HealthcareCentre, Hospital, User


def seed_initial_data(db: Session):
    """Populates clean structural administrative metadata if uninitialized."""
    # Check if locations are already seeded
    if db.query(Location).first() is not None:
        return

    print("[*] Initializing administrative locations and healthcare centres metadata...")

    # Standard administrative districts
    locations_metadata = [
        # Tamil Nadu
        {"state": "Tamil Nadu", "district": "Coimbatore", "pincode": "641018"},
        {"state": "Tamil Nadu", "district": "Madurai", "pincode": "625020"},
        {"state": "Tamil Nadu", "district": "Salem", "pincode": "636030"},
        {"state": "Tamil Nadu", "district": "Tiruchirappalli", "pincode": "620017"},
        # Karnataka
        {"state": "Karnataka", "district": "Mysuru", "pincode": "570001"},
    ]

    loc_objs = {}
    for loc_data in locations_metadata:
        loc = Location(**loc_data)
        db.add(loc)
        db.flush()
        loc_objs[f"{loc.state}-{loc.district}"] = loc

    # Primary Healthcare Centres (Structural facilities for field screening)
    centres_data = [
        # Coimbatore
        {"name": "Primary Health Centre — Valparai", "location_key": "Tamil Nadu-Coimbatore", "centre_type": "PHC", "code": "TN-CBE-PHC01"},
        {"name": "Community Health Centre — Pollachi", "location_key": "Tamil Nadu-Coimbatore", "centre_type": "CHC", "code": "TN-CBE-CHC02"},
        {"name": "Upgraded Primary Health Centre — Sulur", "location_key": "Tamil Nadu-Coimbatore", "centre_type": "PHC", "code": "TN-CBE-PHC03"},
        {"name": "Rural Health Sub-Center — Anaimalai", "location_key": "Tamil Nadu-Coimbatore", "centre_type": "SUB_CENTRE", "code": "TN-CBE-SC04"},
        # Madurai
        {"name": "Primary Health Centre — Usilampatti", "location_key": "Tamil Nadu-Madurai", "centre_type": "PHC", "code": "TN-MDU-PHC01"},
        {"name": "Community Health Centre — Melur", "location_key": "Tamil Nadu-Madurai", "centre_type": "CHC", "code": "TN-MDU-CHC02"},
        # Salem
        {"name": "Rural Health Centre — Omalur", "location_key": "Tamil Nadu-Salem", "centre_type": "PHC", "code": "TN-SLM-PHC01"},
        {"name": "Community Health Centre — Mettur", "location_key": "Tamil Nadu-Salem", "centre_type": "CHC", "code": "TN-SLM-CHC02"},
        # Tiruchirappalli
        {"name": "Primary Health Centre — Musiri", "location_key": "Tamil Nadu-Tiruchirappalli", "centre_type": "PHC", "code": "TN-TRY-PHC01"},
        # Mysuru
        {"name": "Rural Primary Health Centre — Hunsur", "location_key": "Karnataka-Mysuru", "centre_type": "PHC", "code": "KA-MYS-PHC01"},
    ]

    for c_data in centres_data:
        loc = loc_objs.get(c_data["location_key"])
        if loc:
            centre = HealthcareCentre(
                name=c_data["name"],
                location_id=loc.id,
                centre_type=c_data["centre_type"],
                code=c_data["code"],
            )
            db.add(centre)

    db.commit()
    print("[*] Administrative location structure initialized. No fake clinical cases created.")
