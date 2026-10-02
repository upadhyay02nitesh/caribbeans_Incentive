"""7 destination pages + 10-row access table. Order on page: Saint Martin, St. Barth,
Anguilla, British Virgin Islands, Dominica, Grenada, Barbados."""

# Visual centre of the regional map (rings, glow) — a fixed point, not an island.
# No island is labelled a "hub" on this site.
MAP_CENTER = {"x": 455, "y": 190}

ISLANDS = [
    {
        "slug": "saint-martin",
        "name": "Saint Martin",
        "full_name": "Saint Martin / Sint Maarten",
        "headline": "An island where two cultures meet, and every experience feels effortlessly Caribbean.",
        "intro": (
            "French charm, Dutch energy, elegant beachfront venues and private villas create an "
            "inspiring setting for incentive programs, executive retreats and unforgettable gala "
            "dinners. From private sailing and island-hopping to culinary discoveries, team-building "
            "adventures and vibrant cultural encounters, Saint Martin combines sophistication, "
            "diversity and genuine Caribbean warmth."
        ),
        "access": "International Direct Flights & Inter-Island Connection",
        "suited_to": "Incentive Trips, Corporate Retreats, Leisure Groups",
        "gateway": {"label": "From USA", "value": "Direct 4h"},
        "map": {"x": 455, "y": 190, "label": "left", "land": [(0, 0, 9, 6.5, -10)]},
        "panels": {
            "the-island": [
                "Two nations, one island: French elegance on one side, Dutch energy on the other, and a shared spirit of hospitality throughout.",
                "Saint Martin is where most programs begin: private terminal welcomes, easy access, and venues suited to everything from an intimate retreat to a full-scale conference.",
            ],
            "gastronomy": [
                "From beachfront grills to refined French tables, dining here moves easily between casual and elevated.",
                "A single evening can carry your group from a toes-in-the-sand lunch to a formal gala without ever feeling like a compromise.",
            ],
            "experiences": [
                "Sail to nearby islets, explore both sides of the border in an afternoon, or gather for a sunset catamaran cruise.",
                "Saint Martin rewards groups who want variety without complexity: everything is close, and everything connects.",
            ],
        },
        "cards": {
            "the-island": [
                {"label": "Culture", "title": "French Side", "body": "Cobblestone streets, boutique shopping, and a distinctly European pace in Marigot and Grand Case. Sidewalk cafés and open-air markets give this half of the island a slower, more deliberate rhythm."},
                {"label": "Culture", "title": "Dutch Side", "body": "Philipsburg's boardwalk energy, casinos, and cruise-port buzz on the Sint Maarten side. A livelier counterpoint to the French quarter, with duty-free shopping and beachfront bars steps from the pier."},
                {"label": "Leisure", "title": "Simpson Bay", "body": "The island's social hub, with marinas, beach bars, and easy access to nightlife. Superyachts line the lagoon here, and the drawbridge opening is a daily spectacle worth timing a happy hour around."},
                {"label": "Discovery", "title": "Two Nations, One Border", "body": "An open land border lets groups move between French and Dutch territory without ever showing a passport. Half-day tours pair the crossing with stops at historic monuments on each side."},
            ],
            "gastronomy": [
                {"label": "Culinary", "title": "Grand Case Lolos", "body": "Open-air BBQ shacks serving some of the best grilled seafood in the Caribbean. Known as the island's 'gourmet capital,' Grand Case's waterfront row of lolos turns a casual dinner into an event."},
                {"label": "Culinary", "title": "French Fine Dining", "body": "Award-winning tables bringing Michelin-trained technique to island ingredients. Expect tasting menus built around fresh-caught fish, French wine pairings, and service that matches any Paris address."},
                {"label": "Culinary", "title": "Beach Club Lunches", "body": "Toes-in-the-sand dining with a view, perfect for a relaxed working lunch. Long tables set directly on the beach make it easy to move a meeting outdoors without losing momentum."},
                {"label": "Culinary", "title": "Rum & Cocktail Terraces", "body": "Sunset terraces pour rum flights and island-inflected cocktails with a view over the lagoon or the Caribbean Sea. A natural close to a day of meetings or an easy start to an evening gala."},
            ],
            "experiences": [
                {"label": "Adventure", "title": "Catamaran Day Sail", "body": "A full-day sail with snorkeling stops and a sunset return into the lagoon. Crewed charters can host anywhere from a small executive group to a full incentive program."},
                {"label": "Adventure", "title": "Sunset Sailing & Nightlife", "body": "Evening cruises time their return to catch the sky turning gold over the water, before groups head ashore to Simpson Bay's bars and live-music venues."},
                {"label": "Leisure", "title": "Orient Bay Beach Day", "body": "A dedicated beach day with water sports and beachfront group dining. Kayaks, paddleboards, and jet skis are all on hand for teams who want an active afternoon."},
                {"label": "Adventure", "title": "Water Sports Adventure", "body": "Kite surfing, parasailing, and jet-ski tours cluster around the island's calmer bays, an easy way to add an adrenaline element to an otherwise relaxed itinerary."},
            ],
        },
    },
    {
        "slug": "st-barth",
        "name": "St. Barth",
        "full_name": "St. Barth",
        "headline": "An island where understated elegance, exclusivity and Caribbean beauty come naturally.",
        "intro": (
            "Iconic hotels, private villas and exceptional beachfront venues create an inspiring "
            "setting for executive retreats, luxury incentives and intimate celebrations. From private "
            "yacht journeys and refined dining to exclusive island experiences and sunset events, St "
            "Barth brings sophistication, impeccable service and unforgettable Caribbean moments to "
            "every program."
        ),
        "access": "International Direct Flight & Inter-Island Connection (flight & boat via SXM)",
        "suited_to": "Executive Retreats, Luxury Incentive Trips, Social Events",
        "gateway": {"label": "From USA", "value": "Direct 4h"},
        "map": {"x": 525, "y": 222, "label": "right", "land": [(0, 0, 6.5, 3.2, -15)]},
        "panels": {
            "the-island": [
                "Understated luxury defines St Barth: chic without excess, private without being distant.",
                "Villas and boutique hotels here are built for small, high-value groups who want privacy alongside polish.",
            ],
            "gastronomy": [
                "French culinary tradition meets Caribbean ingredients, served in some of the region's most exclusive rooms.",
                "Expect refined tasting menus, quiet beach clubs, and dinners that feel personally curated for your group.",
            ],
            "experiences": [
                "Charter a yacht for the day, discover secluded coves, or close the evening with a sunset gathering above the harbor.",
                "Every experience here is scaled for intimacy: St Barth is where smaller groups feel exceptionally looked after.",
            ],
        },
        "cards": {
            "the-island": [
                {"label": "Culture", "title": "Gustavia Harbor", "body": "The island's chic capital, with designer boutiques, cafes, and superyachts at anchor. Red-roofed buildings and a duty-free waterfront give the harbor an unmistakably French Riviera feel."},
                {"label": "Leisure", "title": "Private Villas", "body": "Some of the Caribbean's most exclusive rental estates, built for total privacy. Infinity pools and hilltop views make villas here a venue in their own right, not just accommodation."},
                {"label": "Nature", "title": "Shell Beach", "body": "A quiet cove just steps from town, ideal for an easy afternoon break. Shallow, calm water and a beachfront bar make it a favorite for a low-key group gathering."},
                {"label": "Leisure", "title": "St. Jean Bay", "body": "The island's most photographed stretch of sand, framed by boutique hotels and the small-plane runway that skims just above the beach."},
            ],
            "gastronomy": [
                {"label": "Culinary", "title": "Nikki Beach", "body": "Iconic beachfront dining and entertainment in one of St Barth's signature settings. Daytime lunches slide easily into a full evening of music and champagne."},
                {"label": "Culinary", "title": "French Bistros", "body": "Intimate dining rooms serving refined French cuisine with island ingredients. Many seat only a handful of tables, making a full buyout simple for smaller groups."},
                {"label": "Culinary", "title": "Private Chef Villas", "body": "In-villa dining experiences tailored entirely to your group. A private chef can shape a full week of menus around dietary needs, group size, and occasion."},
                {"label": "Culinary", "title": "Wine Cellar Tastings", "body": "Several of the island's top restaurants keep serious wine cellars, and private tastings can be arranged for groups who want a quieter, seated evening."},
            ],
            "experiences": [
                {"label": "Adventure", "title": "Yacht Charters", "body": "Full or half-day charters exploring the island's coves and neighboring cays. Crewed sailing or motor yachts scale easily from an executive pair to a full incentive group."},
                {"label": "Leisure", "title": "Sunset Cocktails", "body": "Harborside gatherings timed to the island's famous sunsets, with Gustavia's hillside bars offering some of the best vantage points in the Caribbean."},
                {"label": "Culture", "title": "Boutique Shopping Tour", "body": "A guided walk through Gustavia's designer storefronts, pairing retail therapy with the island's laid-back luxury atmosphere."},
                {"label": "Wellness", "title": "Spa & Wellness Retreats", "body": "Hilltop spas and hotel wellness centers offer private group sessions, a quiet counterpoint to a program built around sailing and sun."},
            ],
        },
    },
    {
        "slug": "anguilla",
        "name": "Anguilla",
        "full_name": "Anguilla",
        "headline": "An island where barefoot elegance, pristine beauty and genuine Caribbean warmth come together.",
        "intro": (
            "Exceptional beachfront resorts, private villas and secluded venues create an inspiring "
            "setting for executive retreats, incentive programs and elegant celebrations. From private "
            "sailing and island-hopping to culinary experiences, wellness activities and barefoot gala "
            "dinners, Anguilla offers effortless sophistication, warm hospitality and unforgettable "
            "moments for every program."
        ),
        "access": "International Direct Flight & Inter-Island Connection (flight & boat via SXM)",
        "suited_to": "Executive Retreats, Wellness Retreats, Luxury Incentive Trips",
        "gateway": {"label": "From USA", "value": "Direct 4h"},
        "map": {"x": 430, "y": 128, "label": "left", "land": [(0, 0, 15, 3.6, -22)]},
        "panels": {
            "the-island": [
                "Anguilla trades spectacle for serenity: some of the Caribbean's finest beaches, without the crowds.",
                "It is the island for groups who want elegance to feel effortless, and quiet to feel intentional.",
            ],
            "gastronomy": [
                "Barefoot dining at its most refined: feet in the sand, plates that rival any city restaurant.",
                "Local seafood, open-air kitchens, and sunset tables make every meal an occasion.",
            ],
            "experiences": [
                "Morning wellness sessions on the beach, afternoon sailing between coves, and gala dinners under open sky.",
                "Anguilla is built for programs that want to slow down without losing sophistication.",
            ],
        },
        "cards": {
            "the-island": [
                {"label": "Nature", "title": "Shoal Bay", "body": "Consistently ranked among the world's best beaches, with powder-white sand and calm water. A handful of low-key beach bars keep the setting relaxed rather than crowded."},
                {"label": "Leisure", "title": "Villa Estates", "body": "Sprawling private villas designed for groups who want space and privacy, many with private pools, chef's kitchens, and staff who can run an entire program on-site."},
                {"label": "Nature", "title": "Meads Bay", "body": "A postcard stretch of coastline lined with boutique resorts, its calm, shallow water making it a natural setting for a beachfront welcome reception."},
                {"label": "Culture", "title": "Island Harbour", "body": "A working fishing village on the island's quieter east end, where traditional wooden boats and local fish shacks offer a more authentic side of Anguilla."},
            ],
            "gastronomy": [
                {"label": "Culinary", "title": "Beach Grills", "body": "Casual, barefoot dining with some of the best seafood on the island. Grilled crayfish and fresh-caught snapper are local specialties worth building a menu around."},
                {"label": "Culinary", "title": "Sunset Tables", "body": "Refined dinners set right at the waterline as the sun goes down, blending fine-dining plating with the informality of dining with your feet in the sand."},
                {"label": "Culinary", "title": "Rum Tastings", "body": "A guided tasting through the island's local rum traditions, led by bartenders who can also design a signature cocktail for your group's closing event."},
                {"label": "Culinary", "title": "Private Beach Dinners", "body": "Fully staged dinners on a private stretch of sand, with lighting, linens, and a custom menu built around the day's catch."},
            ],
            "experiences": [
                {"label": "Adventure", "title": "Sailing to Prickly Pear", "body": "A day-trip by boat to a secluded nearby cay for swimming and lunch, with the boat itself doubling as a floating base for the group all day."},
                {"label": "Wellness", "title": "Sunrise Yoga", "body": "Beachfront sessions timed to the calm of early morning, a gentle way to open a conference day before the agenda begins."},
                {"label": "Culture", "title": "Barefoot Gala", "body": "An elegant evening event staged directly on the sand, pairing formal service and lighting with the relaxed spirit that defines Anguilla."},
                {"label": "Wellness", "title": "Spa Rituals", "body": "Treatments drawing on island botanicals and sea-salt scrubs, offered beachside or in-villa for a quieter counterpoint to an active itinerary."},
            ],
        },
    },
    {
        "slug": "british-virgin-islands",
        "name": "British Virgin Islands",
        "full_name": "British Virgin Islands",
        "headline": "An archipelago where private-island luxury, adventure and the freedom of the sea come together.",
        "intro": (
            "Exclusive resorts, secluded villas and spectacular waterfront venues create an inspiring "
            "setting for incentive programs, executive retreats and elegant celebrations. From private "
            "yacht journeys and island-hopping to sailing regattas, beachfront dining and team "
            "adventures, the British Virgin Islands bring exclusivity, connection and unforgettable "
            "Caribbean experiences to every program."
        ),
        "access": "International Direct Flight & Inter-Island Connection",
        "suited_to": "Incentive Trips, Executive Retreats, Social Events",
        "gateway": {"label": "From USA", "value": "Direct 3h"},
        "map": {"x": 245, "y": 160, "label": "left", "land": [(-18, 3, 6, 2.8, -8), (-5, 0, 7, 3, -5), (7, -2, 4, 2.2, 5), (17, -3, 4.5, 2.4, 12)]},
        "panels": {
            "the-island": [
                "An archipelago rather than a single island: the BVI is built for groups who want to move between anchorages.",
                "Private islands, protected harbors, and a sailing culture that runs generations deep.",
            ],
            "gastronomy": [
                "Beachfront bars and waterfront restaurants set the tone: relaxed, social, and built around the water.",
                "Many of the best meals here happen dockside, straight off the boat.",
            ],
            "experiences": [
                "Charter a fleet for a private regatta, hop between islands by day, and gather for beachfront dinners by night.",
                "Few destinations in the Caribbean reward a sailing-based program as naturally as the BVI.",
            ],
        },
        "cards": {
            "the-island": [
                {"label": "Culture", "title": "Tortola", "body": "The main island and gateway, with deep harbors and easy access to the wider archipelago. Road Town serves as the natural hub for a multi-island program."},
                {"label": "Nature", "title": "Virgin Gorda", "body": "Home to The Baths, a dramatic maze of granite boulders and hidden pools reached by short hikes and swims, one of the most photographed spots in the Caribbean."},
                {"label": "Leisure", "title": "Private Islands", "body": "Exclusive-use islands available for full-buyout group programs, offering complete privacy for a welcome event, gala dinner, or multi-day retreat."},
                {"label": "Nature", "title": "Anegada", "body": "A low-lying coral atoll ringed by one of the world's largest barrier reefs, reachable by boat for a day of snorkeling and a famous lobster lunch."},
            ],
            "gastronomy": [
                {"label": "Culinary", "title": "Dockside Dining", "body": "Waterfront restaurants where the catch of the day arrives by boat, keeping menus fresh and service tied to the rhythm of the harbor."},
                {"label": "Culinary", "title": "Beach Bars", "body": "Laid-back spots built around rum, reggae, and ocean views. The BVI's famous 'Painkiller' cocktail originated in one of these beachfront bars."},
                {"label": "Culinary", "title": "Sunset Cruise Dinners", "body": "Dinner served underway as the boat cruises the coastline, combining a moving venue with uninterrupted water views through the meal."},
                {"label": "Culinary", "title": "Anegada Lobster Lunch", "body": "A signature grilled-lobster meal at a beach shack on Anegada, best paired with a full day on the reef beforehand."},
            ],
            "experiences": [
                {"label": "Adventure", "title": "Private Regatta", "body": "A friendly team sailing competition across a fleet of chartered boats, built around real teamwork and a prize-giving dinner to close the day."},
                {"label": "Adventure", "title": "Island Hopping", "body": "Visit multiple anchorages and beaches in a single day by boat, keeping the itinerary varied without ever repacking a bag."},
                {"label": "Adventure", "title": "Snorkeling the Wrecks", "body": "Guided dives and snorkels through the BVI's famous wreck sites, including the RMS Rhone, one of the Caribbean's best-preserved dive wrecks."},
                {"label": "Culture", "title": "Foxy's Beach Bar", "body": "A legendary Jost Van Dyke institution where live music and full-moon parties have drawn sailors for decades, a natural closing-night stop."},
            ],
        },
    },
    {
        "slug": "dominica",
        "name": "Dominica",
        "full_name": "Dominica",
        "headline": "An island where untamed nature, adventure and authentic Caribbean spirit come alive.",
        "intro": (
            "Rainforest retreats, dramatic landscapes and secluded natural settings create an "
            "inspiring backdrop for incentive programs, executive escapes and meaningful team "
            "experiences. From waterfall hikes and river adventures to wellness rituals, cultural "
            "encounters and immersive outdoor dining, Dominica brings connection, discovery and "
            "unforgettable energy to every program."
        ),
        "access": "International Direct Flight & Inter-Island Connection",
        "suited_to": "Incentive Trips, Corporate Retreats, Team-Building",
        "gateway": {"label": "From USA", "value": "Direct 4h"},
        "map": {"x": 620, "y": 345, "label": "right", "land": [(0, 0, 6, 12, 8)]},
        "panels": {
            "the-island": [
                "The Caribbean's wildest island: rainforest canopy, volcanic peaks, and rivers that outnumber the calendar days.",
                "Dominica is for groups who want their program shaped by nature rather than a beach chair.",
            ],
            "gastronomy": [
                "Farm-to-table takes on new meaning here: much of what you eat was grown or caught within sight of the table.",
                "Outdoor dining beside rivers and waterfalls turns every meal into part of the adventure.",
            ],
            "experiences": [
                "Hike to hidden waterfalls, navigate rivers by kayak, or gather teams for conservation-minded challenges.",
                "This is the island for programs built around discovery, energy, and genuine connection to place.",
            ],
        },
        "cards": {
            "the-island": [
                {"label": "Nature", "title": "Morne Trois Pitons", "body": "A UNESCO World Heritage rainforest park of volcanic peaks and crater lakes. Trails here range from an easy lookout walk to a full-day summit trek."},
                {"label": "Adventure", "title": "Boiling Lake", "body": "One of the world's largest fumaroles, reached by a guided hike through the aptly named Valley of Desolation, past bubbling sulphur springs and steam vents."},
                {"label": "Nature", "title": "Trafalgar Falls", "body": "Twin waterfalls just a short walk from the roadside, with pools at their base warm and cool respectively, fed by both a hot spring and a mountain river."},
                {"label": "Culture", "title": "Kalinago Territory", "body": "Home to the descendants of the region's original Carib inhabitants, where traditional crafts, canoe-building, and cassava farming are still practiced daily."},
            ],
            "gastronomy": [
                {"label": "Culinary", "title": "River-side Dining", "body": "Outdoor tables set beside rushing water, deep in the rainforest, turning even a working lunch into a genuinely immersive experience."},
                {"label": "Culinary", "title": "Farm-to-Table", "body": "Meals built around produce grown within sight of the kitchen, often harvested from the same estate hosting the dinner."},
                {"label": "Culinary", "title": "Local Bush Rum", "body": "A tasting of traditional herbal rum infusions unique to Dominica, each recipe passed down through generations and steeped with island roots and bark."},
                {"label": "Culinary", "title": "Sea Moss & Local Juices", "body": "A tasting of Dominica's traditional sea moss drinks and fresh tropical juices, a distinctive, healthful counterpoint to a rum-forward evening."},
            ],
            "experiences": [
                {"label": "Adventure", "title": "River Tubing", "body": "A guided float down one of the island's many freshwater rivers, easily scaled for groups of any size and fitness level."},
                {"label": "Adventure", "title": "Waterfall Hike", "body": "A team trek to a hidden falls, with a swim at the end, one of the most reliably crowd-pleasing half-day excursions on the island."},
                {"label": "Culture", "title": "Conservation Challenge", "body": "A team-building activity centered on local reforestation efforts, pairing hands-on planting with a briefing from island conservation guides."},
                {"label": "Wellness", "title": "Hot Sulphur Springs", "body": "Natural volcanic pools warmed from below the earth, a restorative close to a day of hiking and an easy way to slow a program's pace."},
            ],
        },
    },
    {
        "slug": "grenada",
        "name": "Grenada",
        "full_name": "Grenada",
        "headline": "An island where lush landscapes, rich flavours and authentic Caribbean warmth come together.",
        "intro": (
            "Elegant beachfront resorts, historic estates and tropical gardens create an inspiring "
            "setting for incentive programs, executive retreats and memorable celebrations. From "
            "sailing and waterfall adventures to spice discoveries, culinary experiences and beachfront "
            "gala dinners, Grenada brings natural beauty, cultural richness and genuine island "
            "character to every program."
        ),
        "access": "International Direct Flight & Inter-Island Connection",
        "suited_to": "Incentive Trips, Corporate Retreats, Team-Building",
        "gateway": {"label": "From USA", "value": "Direct 4h"},
        "map": {"x": 590, "y": 490, "label": "right", "land": [(0, 0, 5.5, 9, 20)]},
        "panels": {
            "the-island": [
                "Known as the Spice Isle, Grenada layers lush landscape with genuine cultural depth.",
                "Historic estates and tropical gardens give programs here a sense of place few islands can match.",
            ],
            "gastronomy": [
                "Nutmeg, cocoa, and spice run through everything, from market stalls to fine dining tables.",
                "A culinary program here doubles as a cultural one; the flavors carry the island's story.",
            ],
            "experiences": [
                "Sail the coastline, hike to hidden waterfalls, or gather for a beachfront gala beneath the palms.",
                "Grenada suits groups who want their program to feel rooted in something real.",
            ],
        },
        "cards": {
            "the-island": [
                {"label": "Nature", "title": "Grand Anse Beach", "body": "Two miles of soft white sand, framed by resorts and reef, regularly ranked among the finest beaches in the Caribbean and an easy anchor for a full-day program."},
                {"label": "Culture", "title": "Historic Estates", "body": "Restored plantation houses set among tropical gardens, many still operating as working spice or cocoa farms open for private group tours and dinners."},
                {"label": "Culture", "title": "St. George's", "body": "A colorful harbor town of colonial architecture and hillside views, its horseshoe-shaped Carenage harbor one of the most photogenic in the region."},
                {"label": "Nature", "title": "Grand Etang Rainforest", "body": "A volcanic crater lake at the island's green heart, ringed by rainforest trails and lookout points over both coasts."},
            ],
            "gastronomy": [
                {"label": "Culinary", "title": "Spice Market Tour", "body": "A guided walk through stalls of nutmeg, cocoa, and local produce, led by vendors who can trace each spice back to the estate it was grown on."},
                {"label": "Culinary", "title": "Estate Dinners", "body": "Multi-course meals served on the grounds of a historic plantation, pairing colonial-era architecture with contemporary Grenadian cooking."},
                {"label": "Culinary", "title": "Chocolate Tasting", "body": "A tasting flight from the island's own cocoa-to-bar producers, walking guests from raw bean through fermentation to the finished bar."},
                {"label": "Culinary", "title": "Nutmeg Rum Cocktails", "body": "Signature cocktails built around the island's namesake spice, mixed by local bartenders who use nutmeg the way other islands use lime."},
            ],
            "experiences": [
                {"label": "Adventure", "title": "Waterfall Sailing Day", "body": "A coastal sail combined with a hike to a hidden waterfall, pairing time on the water with a cooling swim inland."},
                {"label": "Adventure", "title": "Underwater Sculpture Park", "body": "A snorkel tour of the world's first underwater sculpture garden, its submerged figures now colonized by coral and reef fish."},
                {"label": "Culture", "title": "Beachfront Gala", "body": "An elegant closing dinner staged beneath the palms at the shoreline, with the sound of the surf as a natural backdrop to speeches and toasts."},
                {"label": "Culture", "title": "River Antoine Rum Distillery", "body": "The Caribbean's oldest functioning water-wheel rum distillery, still producing overproof rum by hand for a hands-on tasting tour."},
            ],
        },
    },
    {
        "slug": "barbados",
        "name": "Barbados",
        "full_name": "Barbados",
        "headline": "An island where timeless elegance, vibrant culture and genuine Caribbean warmth come together.",
        "intro": (
            "Luxury beachfront resorts, historic estates and exceptional venues create an inspiring "
            "setting for incentive programs, executive retreats and memorable celebrations. From "
            "private sailing and island adventures to immersive culinary experiences, cultural "
            "discoveries and elegant gala dinners, Barbados brings sophistication, energy and "
            "authentic island character to every program."
        ),
        "access": "International Direct Flight & Inter-Island Connection",
        "suited_to": "Incentive Trips, Corporate Retreats, Team-Building",
        "gateway": {"label": "From USA", "value": "Direct 4h"},
        "map": {"x": 770, "y": 445, "label": "right", "land": [(0, 0, 6.5, 9, -15)]},
        "panels": {
            "the-island": [
                "Polished infrastructure meets genuine island culture: Barbados is built to handle scale without losing character.",
                "It's the island of choice when a program needs both sophistication and capacity.",
            ],
            "gastronomy": [
                "Rum runs through everything here, poured with the same pride in a roadside shack as a candlelit dining room.",
                "A single evening can move your group from sun-warmed street food to a chef's tasting menu, and feel completely natural either way.",
            ],
            "experiences": [
                "Sail the calm turquoise of the west coast, wander centuries-old plantation estates, or gather for a gala with your toes nearly in the sand.",
                "Barbados has the scale and polish for your most ambitious program, without ever losing that personal, looked-after feeling.",
            ],
        },
        "cards": {
            "the-island": [
                {"label": "Leisure", "title": "Platinum Coast", "body": "The island's premier stretch of luxury resorts and calm west-coast water, home to some of the Caribbean's most established five-star properties."},
                {"label": "Culture", "title": "Bridgetown", "body": "A UNESCO-listed capital blending colonial history with modern energy, its historic Garrison district and harbor front well suited to a walking tour."},
                {"label": "Culture", "title": "Plantation Estates", "body": "Historic great houses set among sugar cane fields and gardens, several restored and open for private group tours and estate dinners."},
                {"label": "Nature", "title": "East Coast & Bathsheba", "body": "A dramatically different Barbados on the Atlantic side, with rugged cliffs, surf breaks, and a wilder coastline than the calm west."},
            ],
            "gastronomy": [
                {"label": "Culinary", "title": "Oistins Fish Fry", "body": "A lively, casual seafood market that turns into a nightly street party, with grilled mahi-mahi, flying fish, and live music drawing locals and visitors alike."},
                {"label": "Culinary", "title": "Rum Heritage Tour", "body": "A tasting tour through the birthplace of Caribbean rum, visiting the island's historic distilleries where the spirit was first commercially produced."},
                {"label": "Culinary", "title": "Fine Dining Rooms", "body": "White-tablecloth restaurants pairing local ingredients with global technique, many set directly on the Platinum Coast waterfront."},
                {"label": "Culinary", "title": "Flying Fish & Cou-Cou", "body": "Barbados's national dish, served everywhere from roadside stalls to formal dining rooms, a signature tasting stop for any culinary-themed program."},
            ],
            "experiences": [
                {"label": "Adventure", "title": "Catamaran & Turtles", "body": "A sail along the west coast with a stop to swim alongside sea turtles in clear, calm water, one of the island's most requested group excursions."},
                {"label": "Culture", "title": "Plantation Tour", "body": "A guided visit through one of the island's working sugar estates, tracing the crop's history from field to distillery."},
                {"label": "Culture", "title": "Beachfront Gala", "body": "A polished evening event on one of the island's signature beaches, scaled easily from an intimate dinner to a large-group conference close."},
                {"label": "Adventure", "title": "Surf Lessons at Bathsheba", "body": "Group surf lessons on the island's Atlantic coast, a high-energy team activity for programs that want to move beyond the calm west-coast water."},
            ],
        },
    },
]

ISLAND_BY_SLUG = {isle["slug"]: isle for isle in ISLANDS}


def get_island(slug):
    return ISLAND_BY_SLUG.get(slug)


def next_island(slug):
    """Return the next island in ISLANDS order, wrapping at the end."""
    idx = next((i for i, isle in enumerate(ISLANDS) if isle["slug"] == slug), 0)
    return ISLANDS[(idx + 1) % len(ISLANDS)]


# ---------------------------------------------------------------------------
# Per-island connection data (for the map cards)
# ---------------------------------------------------------------------------
CONNECTIONS = {
    "anguilla": [("Ferry", "25-30 min", "frequent daily crossings"), ("Flight", "10 min", "private / charter")],
    "st-barth": [("Ferry", "45–60 min", "scheduled daily"), ("Flight", "10 min", "scheduled, several carriers")],
    "british-virgin-islands": [("Ferry", "~2 hrs", "via connection"), ("Flight", "30–40 min", "charter recommended")],
    "barbados": [("Flight", "~2.5–3 hrs", "via San Juan / Antigua")],
    "dominica": [("Flight", "~2–2.5 hrs", "via Antigua / San Juan")],
    "grenada": [("Flight", "~2.5–3 hrs", "via San Juan / Antigua")],
}

# ---------------------------------------------------------------------------
# Access table — GETTING_THERE (10 rows, MODULE 2b)
# Longer than the 7 destination pages — includes islands served but not featured.
# ---------------------------------------------------------------------------
GETTING_THERE = [
    ("Saint Martin / Sint Maarten", "Direct flight", "saint-martin"),
    ("Anguilla", "Fly or boat via SXM", "anguilla"),
    ("St Barths", "Fly or boat via SXM", "st-barth"),
    ("Saba", "Fly or boat via SXM", None),
    ("Guadeloupe", "Direct flight", None),
    ("Martinique", "Direct flight", None),
    ("Dominica", "Via regional connection", "dominica"),
    ("Grenada", "Direct flight", "grenada"),
    ("Saint Lucia", "Direct flight", None),
    ("Barbados", "Direct flight", "barbados"),
]

ORIGINS = ["Toronto", "New York", "Miami", "Panama City"]

# Islands served but without a destination page — drawn on the regional map as
# plain labelled dots so the map matches the 10-row GETTING_THERE table.
# "land" on every map entry: stylised landmass ellipses (dx, dy, rx, ry, rotation°)
# relative to the island's map point — drawn with an organic coastline filter.
MAP_EXTRA_ISLANDS = [
    {"name": "Saba", "x": 398, "y": 232, "label": "left", "land": [(0, 0, 3, 3, 0)]},
    {"name": "Guadeloupe", "x": 622, "y": 275, "label": "right", "land": [(-6, 0, 6, 8, 10), (5, 1, 7, 5, -20)]},
    {"name": "Martinique", "x": 648, "y": 402, "label": "right", "land": [(0, 0, 6, 11, -25)]},
    {"name": "Saint Lucia", "x": 660, "y": 452, "label": "left", "land": [(0, 0, 4.5, 8.5, 15)]},
]

# Gateway cities and the island each dashed route runs to (map coords).
MAP_GATEWAYS = [
    {"name": "Toronto", "x": 96, "y": 58, "to": (455, 190)},
    {"name": "Miami", "x": 78, "y": 250, "to": (455, 190)},
    {"name": "New York", "x": 96, "y": 352, "to": (622, 275)},
    {"name": "Panama City", "x": 118, "y": 498, "to": (590, 490)},
]

# Approximate flight times (hours, planning estimates only) per origin, keyed by
# island name as it appears in GETTING_THERE. Used to populate the accordion detail.
APPROX_TIMES = {
    "Saint Martin / Sint Maarten": {"Toronto": "4h 45m", "New York": "4h 00m", "Miami": "3h 00m", "Panama City": "3h 00m"},
    "Anguilla": {"Toronto": "—", "New York": "4h 15m", "Miami": "3h 00m", "Panama City": "—"},
    "St Barths": {"Toronto": "—", "New York": "—", "Miami": "—", "Panama City": "—"},
    "Saba": {"Toronto": "—", "New York": "—", "Miami": "—", "Panama City": "—"},
    "Guadeloupe": {"Toronto": "—", "New York": "—", "Miami": "—", "Panama City": "—"},
    "Martinique": {"Toronto": "—", "New York": "—", "Miami": "—", "Panama City": "—"},
    "Dominica": {"Toronto": "—", "New York": "4h 45m", "Miami": "3h 30m", "Panama City": "—"},
    "Grenada": {"Toronto": "5h 20m", "New York": "5h 00m", "Miami": "3h 45m", "Panama City": "—"},
    "Saint Lucia": {"Toronto": "—", "New York": "—", "Miami": "—", "Panama City": "—"},
    "Barbados": {"Toronto": "5h 15m", "New York": "5h 00m", "Miami": "3h 45m", "Panama City": "3h 30m"},
}

# ---------------------------------------------------------------------------
# AIRLIFT — direct, nonstop scheduled flights only (client-supplied, Sept 2026).
#
# Drives the "Getting to Your Island" accordion (MODULE 2b): one dropdown per
# island, closed label "Direct Flights", open list of departure city + nonstop
# time, and the route diagram beside it. Connecting flights and boat transfers
# are deliberately absent from this section.
#
# routes: (departure city, nonstop time, seasonal) — seasonal renders "Seasonal*".
# boat:   (from island, crossing time) — the one sea transfer the client asks to
#         show here, for the two islands reached by boat from Saint Martin.
# note:   a line shown under the routes (St Barths has no long-haul service).
# ---------------------------------------------------------------------------
DIRECT_FLIGHTS = [
    {
        "name": "Saint Martin / Sint Maarten", "slug": "saint-martin", "code": "SXM",
        "routes": [
            ("Miami", "3h", False),
            ("New York / Newark", "4h", False),
            ("Atlanta", "3h 45", False),
            ("Charlotte", "3h 45", False),
            ("Orlando", "3h", False),
            ("Fort Lauderdale", "3h", False),
            ("Boston", "4h 15", False),
            ("Baltimore", "4h", False),
            ("Philadelphia", "4h", False),
            ("Washington", "4h", False),
            ("Chicago", "4h 45", False),
            ("Minneapolis", "5h", False),
            ("Toronto", "4h 45", False),
            ("Montreal", "4h 40", False),
            ("Panama City", "3h", False),
            ("Santo Domingo", "1h 20", False),
        ],
    },
    {
        "name": "Anguilla", "slug": "anguilla", "code": "AXA",
        "boat": ("Saint Martin", "25-30 min"),
        "routes": [
            ("Miami", "3h", False),
            ("Newark", "4h 15", False),
            ("Baltimore", "4h", False),
            ("Boston", "4h 30", False),
            ("Santo Domingo", "1h 30", False),
        ],
    },
    {
        "name": "St Barths", "slug": "st-barth", "code": "SBH",
        "boat": ("Saint Martin", "45-60 min"),
        "routes": [
            ("San Juan", "1h 5", False),
        ],
        "note": ("No direct scheduled flights are currently available from mainland USA, "
                 "Canada or Latin America."),
    },
    {
        "name": "British Virgin Islands · Tortola", "slug": "british-virgin-islands", "code": "EIS",
        "routes": [
            ("Miami", "3h", False),
            ("Santo Domingo", "1h 15", False),
        ],
    },
    {
        "name": "Grenada", "slug": "grenada", "code": "GND",
        "routes": [
            ("Miami", "3h 45", False),
            ("New York", "5h", False),
            ("Atlanta", "4h 30", False),
            ("Charlotte", "4h 30", False),
            ("Toronto", "5h 20", False),
            ("Georgetown, Guyana", "1h 30", False),
        ],
    },
    {
        "name": "Dominica", "slug": "dominica", "code": "DOM",
        "routes": [
            ("Miami", "3h 30", False),
            ("Newark", "4h 45", False),
        ],
    },
    {
        "name": "Barbados", "slug": "barbados", "code": "BGI",
        "routes": [
            ("Miami", "3h 45", False),
            ("New York / Newark", "5h", False),
            ("Atlanta", "4h 30", False),
            ("Charlotte", "4h 30", False),
            ("Boston", "5h 15", False),
            ("Philadelphia", "5h", False),
            ("Washington", "4h 45", False),
            ("Toronto", "5h 15", False),
            ("Montreal", "5h 30", False),
            ("Halifax", "5h", False),
            ("Panama City", "3h 30", False),
            ("Georgetown, Guyana", "1h 30", False),
        ],
    },
]

def _minutes(text):
    """'4h 45' / '3h' / '1h 20' -> minutes, for picking the shortest route."""
    hours, _, rest = text.partition("h")
    return int(hours.strip()) * 60 + (int(rest.strip()) if rest.strip() else 0)


# Short regional hops make poor headline routes for a North American buyer.
REGIONAL_GATEWAYS = {"Santo Domingo", "San Juan", "Georgetown, Guyana"}


def _direct_chip(island):
    """One 'DIRECT' chip for the regional map card, built from the flight table.

    Headlines the shortest long-haul gateway, falling back to a regional one
    when that is all the island has (St Barths)."""
    routes = island["routes"]
    longhaul = [r for r in routes if r[0] not in REGIONAL_GATEWAYS] or routes
    city, time, _ = min(longhaul, key=lambda r: _minutes(r[1]))
    note = f"nonstop from {city}" if len(routes) == 1 else f"{len(routes)} nonstop gateways, from {city}"
    return ("Direct", time, note)


# Every island with direct service leads its map card with that fact; the
# ferry / charter chips below it stay as the ways in from Saint Martin.
for _island in DIRECT_FLIGHTS:
    CONNECTIONS.setdefault(_island["slug"], [])
    CONNECTIONS[_island["slug"]] = [_direct_chip(_island)] + [
        chip for chip in CONNECTIONS[_island["slug"]] if chip[0] != "Direct"
    ]


AIRLIFT_LABEL = "Direct Flights"
AIRLIFT_SEASONAL_NOTE = "Seasonal*"

GETTING_THERE_DISCLAIMER = (
    "Flight times are approximate. Routes, frequencies and availability may vary "
    "according to season and airline schedules."
)

