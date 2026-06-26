from ..extensions import db
from ..models import RequestMatch, SellerProfile, User


class MatchingService:
    @staticmethod
    def create_matches(service_request):
        profiles = (
            SellerProfile.query.join(User)
            .filter(
                User.is_active.is_(True),
                User.user_type == "seller",
                SellerProfile.is_available.is_(True),
                SellerProfile.service_category_id == service_request.service_category_id,
            )
            .all()
        )
        matches = []
        for profile in profiles:
            score = 30
            seller_city = (profile.user.city or profile.user.location or "").lower()
            request_city = (service_request.city or "").lower()
            if request_city and request_city in seller_city:
                score += 50
            score += min(20, (profile.rating or 0) * 4)
            match = RequestMatch(service_request_id=service_request.id, seller_id=profile.user_id, match_score=score)
            db.session.add(match)
            matches.append(match)
        return matches
