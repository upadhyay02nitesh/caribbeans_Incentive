"""The 9 experience categories. Full copy on /your-caribbean-journey; first 1-2
sentences used as short/emotional teasers on the homepage circle grid."""

EXPERIENCES_INTRO = (
    "From private sailing adventures and vibrant culinary discoveries to meaningful cultural "
    "encounters and unforgettable celebrations, every Caribbean experience is thoughtfully "
    "designed around your people and your purpose."
)

EXPERIENCES_CLOSER = (
    "We transform every event and incentive program into a collection of meaningful "
    "moments, where Caribbean warmth meets thoughtful creativity, and every detail is "
    "brought beautifully to life."
)

# Homepage circle-grid intro (short copy).
EXPERIENCES_HOME = {
    "kicker": "EXPERIENCES",
    "h2": "Your Caribbean Journey",
    "lede": "From historical discoveries and culinary journeys to island adventures and cultural encounters, every element of your Caribbean journey is personal and thoughtfully designed.",
}

EXPERIENCES = [
    {
        "slug": "curated-experiences",
        "title": "Curated Experiences",
        "body": [
            "True luxury is not simply about where you go, it is about **how an experience makes you feel** and the memories that remain long after the journey ends.",
            "Every experience we create is an invitation to discover the true spirit of the Caribbean: its welcoming people, remarkable landscapes, rich cultures, vibrant flavors, and effortless way of life.",
            "Whether we are designing an inspiring incentive program, an executive retreat, a corporate celebration, or a multi-island journey, every detail is thoughtfully curated to **reward, connect, and inspire**.",
        ],
    },
    {
        "slug": "caribbean-legacy",
        "title": "Caribbean Legacy",
        "body": [
            "Discover the stories, cultures, and traditions that have shaped the Caribbean.",
            "Explore historic towns with knowledgeable local storytellers, visit centuries-old estates, discover beautifully preserved architecture, and experience the music, art, and traditions that give each island its distinctive identity.",
            "From the colorful streets of the French and Dutch Caribbean to the fascinating heritage of the region's smaller islands, every encounter offers your guests an authentic connection to the destination, and to the people who call it home.",
        ],
    },
    {
        "slug": "island-flavors",
        "title": "Island Flavors",
        "body": [
            "Experience the Caribbean through its flavors, aromas, and warm tradition of sharing food around the table.",
            "Enjoy elegant beachfront dinners, private chef experiences in beautiful villas, colorful market visits, and hands-on cooking workshops inspired by generations of island recipes.",
            "Meet local chefs, farmers, fishermen, rum makers, and culinary artisans who bring the region's character to life. From refined Caribbean cuisine to relaxed toes-in-the-sand celebrations, every dining experience is designed to create connection, conversation, and lasting memories.",
        ],
    },
    {
        "slug": "across-sand-and-sea",
        "title": "Across Sand and Sea",
        "body": [
            "Adventure feels different in the Caribbean.",
            "Sail between neighboring islands aboard a private yacht, cruise along hidden coastlines by catamaran, or discover secluded beaches accessible only from the sea. For something more exhilarating, take to the water by speedboat, enjoy a private regatta, or explore the extraordinary marine world beneath the surface.",
            "On land, journey through tropical rainforests, volcanic landscapes, natural pools, and panoramic mountain trails. From 4×4 island adventures to scenic helicopter flights above turquoise waters, each experience combines discovery and excitement with comfort, elegance, and effortless organization.",
        ],
    },
    {
        "slug": "unique-team-building-experiences",
        "title": "Team Building Experiences",
        "body": [
            "Bring your people together through energizing experiences inspired by the landscapes, cultures, and playful spirit of the Caribbean.",
            "Compete in a private sailing regatta, take on an island discovery challenge, participate in lively beach games, or collaborate in a Caribbean cooking competition. Teams can also reconnect through guided hikes, water-based challenges, conservation activities, or customized adventures created around your company's values.",
            "Every activity is designed to encourage **teamwork, communication, and shared achievement**, while creating genuine moments of laughter and connection.",
        ],
    },
    {
        "slug": "crafted-in-the-caribbean",
        "title": "Crafted in the Caribbean",
        "body": [
            "Connect with the creative spirit of the Caribbean through personal encounters with local artists, designers, musicians, and craftspeople.",
            "Step inside intimate studios and galleries, discover traditional techniques passed down through generations, or participate in private workshops inspired by the colors and natural materials of the islands.",
            "These meaningful exchanges allow guests to experience the Caribbean beyond its beautiful landscapes, revealing the creativity, character, and stories at the heart of each destination.",
        ],
    },
    {
        "slug": "quiet-island-moments",
        "title": "Quiet Island Moments",
        "body": [
            "In the Caribbean, wellbeing comes naturally.",
            "Begin the day with sunrise yoga on a secluded beach, experience a private meditation surrounded by tropical gardens, or unwind with treatments inspired by local botanicals and traditional island remedies.",
            "From restorative spa rituals and mindful nature walks to quiet moments aboard a yacht, we create space for your guests to pause, recharge, and reconnect.",
            "These peaceful experiences offer the perfect balance to an active program, leaving every guest feeling renewed and cared for.",
        ],
    },
    {
        "slug": "the-art-of-execution",
        "title": "The Art of Execution",
        "body": [
            "Discover a side of the Caribbean that few visitors have the opportunity to experience.",
            "Enjoy private access to remarkable villas and historic estates, meet celebrated chefs and local personalities, or experience an intimate performance in an unforgettable setting.",
            "Go behind the scenes with artists, conservationists, rum makers, marine experts, and cultural storytellers who share their worlds with warmth and authenticity.",
            "These privileged encounters turn an itinerary into something deeply personal, creating stories your guests will continue sharing long after they return home.",
        ],
    },
    {
        "slug": "sustainability-and-authenticity",
        "title": "Sustainability & Authenticity",
        "body": [
            "Our love for the Caribbean comes with a responsibility to protect its natural beauty, celebrate its cultures, and support the communities that make every experience possible.",
            "We work with trusted local partners to incorporate responsible choices throughout our programs, from locally sourced dining and community-led experiences to conservation initiatives, eco-conscious activities, and opportunities to give back.",
            "Every experience is thoughtfully designed to create a positive connection between guests and destination, ensuring that the beauty and spirit of our islands can be enjoyed for generations to come.",
        ],
    },
]

EXPERIENCE_BY_SLUG = {e["slug"]: e for e in EXPERIENCES}
