"""Two service groupings, plus the immersive 12-step arrival-to-departure journey."""

SERVICE_CATEGORIES = [
    (
        "Corporate & MICE Excellence",
        [
            "Corporate Meetings",
            "Incentive Travel Programs",
            "International Conferences",
            "Product Launches & Brand Activations",
            "Executive Retreats",
            "Gala Dinners & Private Events",
            "Complete Event Production & Logistics",
        ],
    ),
    (
        "Curated Luxury Travel",
        [
            "Tailor-Made Itineraries",
            "Exclusive Villa & 5-Star Hotel Stays",
            "Private Transfers",
            "Curated Experiences & Local Experts",
            "Gastronomic Journeys",
            "Wellness & Cultural Immersions",
        ],
    ),
]

JOURNEY = [
    ("01", "Airport Welcome", "Meet & greet and seamless private transfers on arrival."),
    ("02", "Transportation", "Ground, ferry and charter logistics between islands."),
    ("03", "Meetings & Conferences", "Venues and full production for the working sessions."),
    ("04", "Activities & Team Building", "Curated experiences suited to the group and island."),
    ("05", "Private Boats & Yachts", "Charter excursions and on-water experiences."),
    ("06", "Decoration & Event Design", "Theming and production for every occasion."),
    ("07", "Audiovisual & Production", "Technical delivery for meetings and events."),
    ("08", "Restaurants & Private Dining", "From casual island fare to private chef dinners."),
    ("09", "Entertainment", "Live music, local performers, and evening programming."),
    ("10", "Corporate Gifting", "Locally sourced gifts and amenities."),
    ("11", "On-site Management", "Our team present throughout, start to finish."),
    ("12", "Departure Assistance", "Smooth transfers and send-off for every traveller."),
]

JOURNEY_SECTION = {
    "kicker": "WHAT WE HANDLE",
    "h2": "A journey from arrival to departure",
    "lede": "Scroll to see every service woven into the program, in the order your group experiences it.",
}
