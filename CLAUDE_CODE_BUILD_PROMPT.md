# BUILD PROMPT — Caribbean Incentive website (Flask + Bootstrap)

> **How to use this file.** Drop it in an empty folder, open Claude Code there, and say:
> *"Read CLAUDE_CODE_BUILD_PROMPT.md and build the whole site. Start with Phase 1."*
> Then work through the phases. The file also works as `CLAUDE.md` — rename it if you want Claude Code to auto-load it every session.

---

## 0. MISSION

Build **caribbean-incentive.com**: the English-language website for Caribbean Incentive, a boutique Destination Management Company (DMC) running corporate incentives, meetings, conferences and group programs across the Eastern Caribbean. Their hub is Saint Martin / Sint Maarten (SXM).

The audience is corporate event buyers and incentive planners in the US, Canada and Latin America. The site's single job is to make them submit an event brief.

**Structural reference:** `https://thedmcgreece.com` — the client explicitly asked for this site's structure, look and feel. Study it. Our navigation, section order and experience categories map onto it one-to-one.

**Interaction reference:** `https://tourisme-sumene-artense.com/?skipintro` — for motion feel: parallax layers, progressive reveal, editorial transitions.

**Do NOT resemble:** `https://caraibes-incentive.com` — that's the same company's French-market site for a different client base. Only the brand mark is shared.

This is going in front of the client as a demo. **Every page must look finished — no lorem ipsum, no empty states, no dead links.** All copy in this document is final, client-written text. Use it verbatim.

---

## 1. TECH STACK

| Layer | Choice | Notes |
|---|---|---|
| Server | **Python 3.11 + Flask 3.x** | App factory pattern, Blueprints |
| Templating | **Jinja2** | Heavy use of macros + partials |
| CSS framework | **Bootstrap 5.3** (CDN) | Grid, utilities, offcanvas, accordion, modal, collapse ONLY |
| Custom CSS | Hand-written, layered over Bootstrap | `brand.css` (tokens) + `components.css` |
| JS | **Vanilla ES6**, no framework, no build step | One file per module |
| Icons | Bootstrap Icons (CDN) | Used sparingly |
| Fonts | Google Fonts — Fraunces + Work Sans | |
| Forms | Flask-WTF + WTForms | CSRF on |
| Email | Flask-Mail (SMTP from `.env`) | |
| Env | python-dotenv | |

### Critical styling rule
**The finished site must not look like a Bootstrap template.** Use Bootstrap for layout mechanics and behaviour, then override its visual defaults completely:

- Kill default `border-radius` (we use `2px` max, or 0)
- Kill default button styles — rewrite `.btn-primary` / `.btn-outline-*` from our tokens
- Kill default `box-shadow` on cards, no `card` default borders
- No `container` default padding — we set our own gutters
- No Bootstrap blue anywhere
- Override `.accordion`, `.nav-tabs`, `.form-control` from scratch

If a reviewer can tell it's Bootstrap by looking, it's not done.

---

## 2. PROJECT STRUCTURE

Create exactly this:

```
caribbean-incentive/
├── app.py                      # create_app() factory, run block
├── config.py                   # Config classes, reads .env
├── requirements.txt
├── .env.example
├── README.md                   # setup + run instructions
│
├── content/                    # ALL copy and data lives here, never in templates
│   ├── __init__.py
│   ├── site.py                 # nav, global copy, CTAs, footer, contact details
│   ├── islands.py              # 7 destination pages + 10-row access table
│   ├── experiences.py          # the 9 categories
│   ├── services.py             # the 12-step journey + 2 service categories
│   ├── itinerary.py            # 5-day sample program
│   ├── pricing.py              # planning estimate model
│   └── media.py                # image/video registry — ONE file to swap real assets in
│
├── routes/
│   ├── __init__.py
│   ├── main.py                 # all page routes
│   └── inquiry.py              # POST handlers: brief, RFP, callback
│
├── forms.py                    # WTForms classes
│
├── templates/
│   ├── base.html
│   ├── partials/
│   │   ├── nav.html
│   │   ├── footer.html
│   │   ├── section_head.html   # macro: kicker + h2 + lede
│   │   ├── hero_video.html
│   │   ├── island_card.html    # macro
│   │   ├── map_region.html     # MODULE 2a
│   │   ├── getting_there.html  # MODULE 2b
│   │   ├── itinerary.html      # MODULE 4
│   │   ├── estimator.html      # MODULE 5
│   │   ├── inquiry_fab.html    # persistent discreet inquiry button
│   │   └── flash.html
│   ├── index.html
│   ├── where_it_all_begins.html
│   ├── designed_around_you.html
│   ├── connected.html
│   ├── islands_index.html
│   ├── island_detail.html      # MODULE 3 — one template, 7 islands
│   ├── journey.html
│   ├── endless_creations.html
│   ├── envision.html
│   ├── connect.html
│   └── 404.html
│
├── static/
│   ├── css/
│   │   ├── brand.css           # design tokens + type + Bootstrap overrides
│   │   └── components.css      # section + module styles
│   ├── js/
│   │   ├── nav.js
│   │   ├── hero.js             # MODULE 1
│   │   ├── map.js              # MODULE 2
│   │   ├── island.js           # MODULE 3
│   │   ├── itinerary.js        # MODULE 4
│   │   ├── estimator.js        # MODULE 5
│   │   └── motion.js           # reveal-on-scroll, parallax, cursor
│   ├── img/                    # see §11
│   └── video/
└── scripts/
    └── fetch_placeholders.py   # pulls demo imagery — see §11
```

---

## 3. DESIGN SYSTEM

Put these in `static/css/brand.css` as CSS custom properties. They carry forward from the approved prototype — **do not invent a new palette.**

```css
:root{
  /* ground */
  --paper:        #FBF8F3;   /* primary light ground */
  --paper-dim:    #F1EBDD;   /* alternating band */
  --wash:         #E8F2EF;   /* cool tinted band */
  --white:        #FFFFFF;

  /* dark ground */
  --ink:          #0D2B2E;   /* deep sea green — nav solid, dark sections */
  --ink-soft:     #123A3D;   /* raised surface on dark */

  /* type */
  --text:         #16241F;
  --muted:        #66766D;
  --line:         #DDD4C0;

  /* accents */
  --reef:         #2E8C82;   /* teal — links, active states */
  --reef-dark:    #1E5F58;
  --gold:         #C08A3E;   /* primary CTA */
  --gold-bright:  #D9A860;   /* hover, active markers, kickers on dark */
  --coral:        #E2704A;   /* used ONCE per page maximum */
}
```

**Type**
- Display / headings: `'Fraunces', serif` — weight 400–500, **italic for all H1/H2/H3**, `letter-spacing: -0.01em`
- Body / UI: `'Work Sans', sans-serif` — 300/400/500/600
- Kickers (eyebrows): Work Sans, 13px, `--gold` on light / `--gold-bright` on dark, no uppercase transform needed — the client's labels are already caps

```html
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,500;0,9..144,600;1,9..144,400;1,9..144,500&family=Work+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
```

**Type scale**
| Role | Size | Face |
|---|---|---|
| Hero H1 | `clamp(32px, 6vw, 68px)` | Fraunces italic 400 |
| Section H2 | `clamp(28px, 4vw, 46px)` | Fraunces italic 400 |
| H3 | 26–28px | Fraunces italic 400 |
| Body | 15px / 1.55 | Work Sans 400 |
| Small / meta | 12.5–13px | Work Sans 400 |
| Kicker | 13px | Work Sans 400 |

**Spacing** — section vertical rhythm: `104px` top / `50px` bottom for section heads; `100–120px` between major sections. Max content width `1220px`, side gutter `32px` (24px under 900px, never below 16px).

**Buttons**
- `.btn-brand` — `background: var(--gold)`, `color: var(--ink)`, `padding: 15px 26px`, `border-radius: 2px`, hover → `--gold-bright` + `translateY(-1px)`
- `.btn-ghost` — `1px solid rgba(250,246,236,.55)`, transparent, white text (for dark grounds)
- `.btn-ghost-dark` — `1px solid var(--line)`, transparent, `--text` (for light grounds)

**Motion rules**
- All transitions `.25s–.9s ease`
- `prefers-reduced-motion: reduce` → clamp all animation/transition to `0.01ms`
- **Reveal-on-scroll must default to VISIBLE.** Add `.reveal-init` to `<html>` via JS first, then observe. If JS fails, content still shows. (This is how the prototype does it — keep that pattern.)
- Parallax: hero background and section media move at ~0.3× scroll speed. Use `transform: translate3d()`, never `background-attachment: fixed`.

---

## 4. ROUTES

| Route | Template | Nav label |
|---|---|---|
| `/` | `index.html` | — |
| `/where-it-all-begins` | `where_it_all_begins.html` | WHERE IT ALL BEGINS |
| `/designed-around-you` | `designed_around_you.html` | DESIGNED AROUND YOU |
| `/connected-to-the-caribbean` | `connected.html` | CONNECTED TO THE CARIBBEAN |
| `/explore-our-islands` | `islands_index.html` | EXPLORE OUR ISLANDS |
| `/explore-our-islands/<slug>` | `island_detail.html` | *(dropdown under above)* |
| `/your-caribbean-journey` | `journey.html` | YOUR CARIBBEAN JOURNEY |
| `/endless-creations` | `endless_creations.html` | ENDLESS CREATIONS |
| `/envision-your-experience` | `envision.html` | ENVISION YOUR EXPERIENCE |
| `/lets-connect` | `connect.html` | **LET'S CONNECT** *(CTA button, not a plain link)* |

POST endpoints: `/inquiry/brief`, `/inquiry/rfp`, `/inquiry/callback`.

**Nav behaviour:** fixed, transparent over the hero, gains `rgba(13,43,46,.95)` + blur + reduced padding on `scrollY > 60`. `EXPLORE OUR ISLANDS` opens a dropdown with the 7 islands. Under 992px → Bootstrap offcanvas from the right, dark ground, large Fraunces italic links.

---

## 5. CONTENT — `content/site.py`

```python
BRAND = "Caribbean Incentive"
TAGLINE = "Your People, Our Home, Caribbean Connection"
DOMAIN = "caribbean-incentive.com"
RFP_EMAIL = "karishma.singh@caraibes-incentive.com"

HERO = {
    "lines": ["Your People.", "Our Home.", "Caribbean Connection."],
    "primary_cta": ("Explore Our Islands", "/explore-our-islands"),
    "secondary_cta": ("Submit an Event Brief", "/lets-connect"),
    "scenes": [
        ("arrival", "Arrival at SXM — private terminal welcome"),
        ("meeting", "Off-site meetings, island-side"),
        ("gala",    "Gala dinner under the stars"),
        ("island",  "The islands themselves — the reason we do this"),
    ],
}
```

### Homepage intro
**H2:** `Inspired experiences and flawless execution for remarkable events across the Caribbean`

> Welcome to Caribbean Incentive, where every experience is thoughtfully designed to bring people together, spark emotion, and leave a lasting impression.
>
> Born in the Caribbean and guided by deep local expertise, we create seamless incentive programs, corporate events, conferences, and group journeys across some of the region's most captivating islands.
>
> Whether you are planning an unforgettable incentive escape, a meaningful executive retreat, or a multi-island experience, our team brings every detail to life with warmth, creativity, and care.

**Pull quote (larger, Fraunces italic):** `Your people. Our home. One unforgettable Caribbean experience.`

### WHERE IT ALL BEGINS
Kicker `WHERE IT ALL BEGINS` · H2 `The Essence of Caribbean Incentive`

> At Caribbean Incentive, we believe the most memorable events begin with a genuine connection to the destination, to its people, and to one another.
>
> As a boutique Caribbean DMC, we combine personal attention and creative flexibility with extensive destination knowledge and a trusted network of local partners.
>
> From the first idea to the final farewell, we become an extension of your team managing every detail with precision while making the entire experience feel effortless.

**Full page adds** — H2 `Your vision, brought to life with Caribbean warmth`

> At **Caribbean Incentive**, we create meaningful MICE programs and unforgettable group experiences across the Caribbean's most captivating islands.
>
> Our dedicated team combines international standards with genuine local insight. We understand the importance of culture, communication, and personal connection—allowing us to work seamlessly with clients and guests from around the world.
>
> From inspiring incentive journeys and executive retreats to conferences, celebrations, and multi-island programs, every experience is thoughtfully shaped around your people, your objectives, and the memories you want to create.
>
> With creativity, precision, and trusted relationships throughout the region, we take care of every detail—transforming ambitious ideas into beautifully executed Caribbean experiences.

**Four values** (Fraunces italic headings, 2×2 grid, no card borders — hairline dividers only):

| Value | Copy |
|---|---|
| Exceptional Care | We approach every program with warmth and attention, delivering thoughtful service from the first conversation to the final farewell. |
| Creative Spirit | Every experience is individually designed, bringing together fresh ideas, authentic island character, and moments of genuine discovery. |
| Trusted Partnership | Transparency, reliability, and mutual respect are at the heart of every relationship we build. |
| Seamless Collaboration | We work as an extension of your team, bringing people, partners, and destinations together around one shared vision. |

**Our Signature Strengths** (5 items, numbered list with hairline rules):
1. Deep, firsthand knowledge of the Caribbean and the distinctive character of each island we represent.
2. A trusted network of exceptional local partners, unique venues, and memorable experiences across the region.
3. One dedicated team coordinating every element of your program, from creative concept and logistics to production and on-site delivery.
4. A flexible, personal approach shaped around your guests, your culture, and your objectives.
5. The ability to create seamless single-island and multi-destination programs throughout the Caribbean.

**Page closer** (dark band, large Fraunces italic, centred):
`Where Caribbean warmth meets flawless execution—and every experience is made personally yours.`

### Explore Our Caribbean (homepage destination section)
H2 `Explore Our Caribbean`
> Our reach extends across the Caribbean, from its iconic island destinations to its most secluded and authentic shores.

**Pull quote above the grid:**
> Rooted in the islands and guided by a genuine spirit of hospitality, we create exceptional Caribbean experiences that feel personal, seamless, and entirely your own.

**Right-hand note beside the heading:**
> Across every region, our unparalleled local knowledge and trusted partnerships transform your ambitions into unforgettable realities.

Grid of 7 island cards. Each card: full-bleed image, island name bottom-left, `DISCOVER MORE →` in a circular button bottom-right. Hover → image scales 1.05, overlay deepens. Click → `/explore-our-islands/<slug>`.

### DESIGNED AROUND YOU / WHAT WE DO
Kicker `WHAT WE DO` · H3 `Thoughtfully Created Around You`

> From seamless corporate gatherings to indulgent luxury escapes, our end-to-end destination management services across **the Caribbean** blend local authenticity with international sophistication.

> ⚠️ **The source brief says "across Greece" here — a copy-paste slip from the reference site. It must read "across the Caribbean." Flag this to the client but ship the corrected version.**

**Full page** — H2 `Crafted Exclusively for You`
> Every experience we create begins with you—your vision, your objectives, and the way you want your guests to feel.
>
> From inspiring incentive journeys and executive retreats to conferences, corporate celebrations, and multi-island programs, our complete destination management services combine authentic Caribbean warmth with international standards of excellence.
>
> We listen carefully, think creatively, and manage every detail with precision. Accommodation, transportation, dining, activities, entertainment, production, and on-site coordination are thoughtfully brought together to create one seamless and memorable experience.

### ENDLESS CREATIONS
Homepage teaser — kicker `WHY CHOOSE THE CARIBBEAN` · H2 `Endless Creations`
> The Caribbean is far more than a destination—it is a vibrant collection of islands where natural beauty, rich cultures and modern elegance come together, creating endless possibilities for inspiration, discovery and connection.

Full page — H3 `Your Caribbean Story`
> Sail between hidden coves. Dine beneath the stars. Discover vibrant island traditions. Celebrate beside the sea. Connect with local communities. Share moments that your guests will remember long after they return home.
>
> Every Caribbean Incentive experience is shaped around your people, your purpose, and the feeling you want to create—bringing together authentic island character and refined execution.

H2 `One Region. Endless Possibilities.`
> The Caribbean is more than a collection of beautiful islands. It is a world of contrasts, where cultures meet, landscapes transform, and every journey carries its own rhythm.
>
> With direct air access from the United States, Canada, and Latin America—and effortless connections between neighboring islands by boat—the region offers extraordinary possibilities for incentive travel, corporate gatherings, and multi-destination programs.
>
> Here, business feels more human, celebrations feel more meaningful, and every shared experience brings people closer together.

### ENVISION YOUR EXPERIENCE
H2 `Your Vision, Brought to Life`
> Every Caribbean program begins with an idea, a moment of connection, a sense of discovery, or an experience your guests will remember long after they return home.
>
> From the first arrival to the final farewell, explore how your vision could unfold through an inspiring sample itinerary, then create an initial planning estimate shaped around your destination, group and ambitions.

Sub-heads: `What a five-day Caribbean incentive could look like` and `Create your planning estimate`.

### LET'S CONNECT
H2 `Step beyond the expected. Beyond the familiar. Beyond the ordinary. Bring your people, we'll bring the Caribbean.`
> Whether you envision an inspiring corporate event, an unforgettable incentive journey or an intimate executive retreat that reveals the true spirit of the Caribbean, we are here to bring your vision to life. Share your ambitions with us, and we will thoughtfully tailor every detail to reflect your objectives, your people and your unique idea of extraordinary.
>
> Let's create moments that remain long after the journey ends. Bring your people, we'll bring the Caribbean and make it happen!

Form intro:
> Please fill out the form below to share your inquiry with us. Whether it's MICE, luxury travel, or something uniquely yours, we are ready to create exceptional experiences together.

---

## 6. CONTENT — `content/islands.py`

Seven islands get full pages. Structure each as a dict; `island_detail.html` renders all seven from this.

```python
ISLANDS = [
  {
    "slug": "saint-martin",
    "name": "Saint Martin",
    "full_name": "Saint Martin / Sint Maarten",
    "is_hub": True,
    "headline": "An island where two cultures meet, and every experience feels effortlessly Caribbean.",
    "intro": "French charm, Dutch energy, elegant beachfront venues and private villas create an inspiring setting for incentive programs, executive retreats and unforgettable gala dinners. From private sailing and island-hopping to culinary discoveries, team-building adventures and vibrant cultural encounters, Saint Martin combines sophistication, diversity and genuine Caribbean warmth.",
    "access": "Direct international flights",
    "suited_to": "Arrivals, welcome events, full programs",
    "map": {"x": 450, "y": 230},
    "connections": [],
  },
  # ... six more, below
]
```

Full data for the remaining six — **copy verbatim**:

| slug | name | headline | intro |
|---|---|---|---|
| `st-barth` | St. Barth | An island where understated elegance, exclusivity and Caribbean beauty come naturally. | Iconic hotels, private villas and exceptional beachfront venues create an inspiring setting for executive retreats, luxury incentives and intimate celebrations. From private yacht journeys and refined dining to exclusive island experiences and sunset events, St Barth brings sophistication, impeccable service and unforgettable Caribbean moments to every program. |
| `anguilla` | Anguilla | An island where barefoot elegance, pristine beauty and genuine Caribbean warmth come together. | Exceptional beachfront resorts, private villas and secluded venues create an inspiring setting for executive retreats, incentive programs and elegant celebrations. From private sailing and island-hopping to culinary experiences, wellness activities and barefoot gala dinners, Anguilla offers effortless sophistication, warm hospitality and unforgettable moments for every program. |
| `british-virgin-islands` | British Virgin Islands | An archipelago where private-island luxury, adventure and the freedom of the sea come together. | Exclusive resorts, secluded villas and spectacular waterfront venues create an inspiring setting for incentive programs, executive retreats and elegant celebrations. From private yacht journeys and island-hopping to sailing regattas, beachfront dining and team adventures, the British Virgin Islands bring exclusivity, connection and unforgettable Caribbean experiences to every program. |
| `dominica` | Dominica | An island where untamed nature, adventure and authentic Caribbean spirit come alive. | Rainforest retreats, dramatic landscapes and secluded natural settings create an inspiring backdrop for incentive programs, executive escapes and meaningful team experiences. From waterfall hikes and river adventures to wellness rituals, cultural encounters and immersive outdoor dining, Dominica brings connection, discovery and unforgettable energy to every program. |
| `grenada` | Grenada | An island where lush landscapes, rich flavours and authentic Caribbean warmth come together. | Elegant beachfront resorts, historic estates and tropical gardens create an inspiring setting for incentive programs, executive retreats and memorable celebrations. From sailing and waterfall adventures to spice discoveries, culinary experiences and beachfront gala dinners, Grenada brings natural beauty, cultural richness and genuine island character to every program. |
| `barbados` | Barbados | An island where timeless elegance, vibrant culture and genuine Caribbean warmth come together. | Luxury beachfront resorts, historic estates and exceptional venues create an inspiring setting for incentive programs, executive retreats and memorable celebrations. From private sailing and island adventures to immersive culinary experiences, cultural discoveries and elegant gala dinners, Barbados brings sophistication, energy and authentic island character to every program. |

**Order on the page:** Saint Martin, St. Barth, Anguilla, British Virgin Islands, Dominica, Grenada, Barbados.

**Section closer:** `Wherever the journey takes you, your guests will be welcomed with genuine Caribbean warmth.`

### Per-island connection data (for the map cards)

```python
CONNECTIONS = {
  "anguilla":               [("Ferry","20–25 min","frequent daily crossings"), ("Flight","10 min","private / charter")],
  "st-barth":               [("Ferry","45–60 min","scheduled daily"),          ("Flight","10 min","scheduled, several carriers")],
  "british-virgin-islands": [("Ferry","~2 hrs","via connection"),              ("Flight","30–40 min","charter recommended")],
  "barbados":               [("Flight","~2.5–3 hrs","via San Juan / Antigua")],
  "dominica":               [("Flight","~2–2.5 hrs","via Antigua / San Juan")],
  "grenada":                [("Flight","~2.5–3 hrs","via San Juan / Antigua")],
}
```

### Access table — `GETTING_THERE` (10 rows, MODULE 2b)

Note this list is **longer than the 7 destination pages** — it includes islands we serve but don't feature. That's intentional.

```python
GETTING_THERE = [
  ("Saint Martin / Sint Maarten", "Direct flight",            "saint-martin"),
  ("Anguilla",                    "Fly or boat via SXM",      "anguilla"),
  ("St Barths",                   "Fly or boat via SXM",      "st-barth"),
  ("Saba",                        "Fly or boat via SXM",      None),
  ("Guadeloupe",                  "Direct flight",            None),
  ("Martinique",                  "Direct flight",            None),
  ("Dominica",                    "Via regional connection",  "dominica"),
  ("Grenada",                     "Direct flight",            "grenada"),
  ("Saint Lucia",                 "Direct flight",            None),
  ("Barbados",                    "Direct flight",            "barbados"),
]

ORIGINS = ["Toronto", "New York", "Miami", "Panama City"]
```

**Mandatory disclaimer under the table:**
> Tap an island to see approximate flight times by origin city. Times are planning estimates based on typical routings, not live flights — confirm exact flights with your team before quoting a client.

---

## 7. CONTENT — `content/experiences.py` (the 9 categories)

Section opener:
> From private sailing adventures and vibrant culinary discoveries to meaningful cultural encounters and unforgettable celebrations, every Caribbean experience is thoughtfully designed around your people and your purpose.

**Layout (match the reference site exactly):** each category is a Fraunces italic heading, 2–4 paragraphs, and a **horizontally scrollable strip of 6 images**. On the homepage, the same 9 appear as a grid of **circular thumbnails with captions**.

```python
EXPERIENCES = [
  {"slug":"curated-experiences","title":"Curated Experiences","body":[...]},
  ...
]
```

**1. Curated Experiences**
> True luxury is not simply about where you go, it is about **how an experience makes you feel** and the memories that remain long after the journey ends.
>
> Every experience we create is an invitation to discover the true spirit of the Caribbean: its welcoming people, remarkable landscapes, rich cultures, vibrant flavors, and effortless way of life.
>
> Whether we are designing an inspiring incentive program, an executive retreat, a corporate celebration, or a multi-island journey, every detail is thoughtfully curated to **reward, connect, and inspire**.

**2. Caribbean Legacy**
> Discover the stories, cultures, and traditions that have shaped the Caribbean.
>
> Explore historic towns with knowledgeable local storytellers, visit centuries-old estates, discover beautifully preserved architecture, and experience the music, art, and traditions that give each island its distinctive identity.
>
> From the colorful streets of the French and Dutch Caribbean to the fascinating heritage of the region's smaller islands, every encounter offers your guests an authentic connection to the destination—and to the people who call it home.

**3. Island Flavors**
> Experience the Caribbean through its flavors, aromas, and warm tradition of sharing food around the table.
>
> Enjoy elegant beachfront dinners, private chef experiences in beautiful villas, colorful market visits, and hands-on cooking workshops inspired by generations of island recipes.
>
> Meet local chefs, farmers, fishermen, rum makers, and culinary artisans who bring the region's character to life. From refined Caribbean cuisine to relaxed toes-in-the-sand celebrations, every dining experience is designed to create connection, conversation, and lasting memories.

**4. Across Sand & Sea**
> Adventure feels different in the Caribbean.
>
> Sail between neighboring islands aboard a private yacht, cruise along hidden coastlines by catamaran, or discover secluded beaches accessible only from the sea. For something more exhilarating, take to the water by speedboat, enjoy a private regatta, or explore the extraordinary marine world beneath the surface.
>
> On land, journey through tropical rainforests, volcanic landscapes, natural pools, and panoramic mountain trails. From 4×4 island adventures to scenic helicopter flights above turquoise waters, each experience combines discovery and excitement with comfort, elegance, and effortless organization.

**5. Crafted in the Caribbean**
> Connect with the creative spirit of the Caribbean through personal encounters with local artists, designers, musicians, and craftspeople.
>
> Step inside intimate studios and galleries, discover traditional techniques passed down through generations, or participate in private workshops inspired by the colors and natural materials of the islands.
>
> These meaningful exchanges allow guests to experience the Caribbean beyond its beautiful landscapes—revealing the creativity, character, and stories at the heart of each destination.

**6. Unique Team-Building Experiences**
> Bring your people together through energizing experiences inspired by the landscapes, cultures, and playful spirit of the Caribbean.
>
> Compete in a private sailing regatta, take on an island discovery challenge, participate in lively beach games, or collaborate in a Caribbean cooking competition. Teams can also reconnect through guided hikes, water-based challenges, conservation activities, or customized adventures created around your company's values.
>
> Every activity is designed to encourage **teamwork, communication, and shared achievement**—while creating genuine moments of laughter and connection.

**7. Quiet Island Moments**
> In the Caribbean, wellbeing comes naturally.
>
> Begin the day with sunrise yoga on a secluded beach, experience a private meditation surrounded by tropical gardens, or unwind with treatments inspired by local botanicals and traditional island remedies.
>
> From restorative spa rituals and mindful nature walks to quiet moments aboard a yacht, we create space for your guests to pause, recharge, and reconnect.
>
> These peaceful experiences offer the perfect balance to an active program, leaving every guest feeling renewed and cared for.

**8. The Art of Execution**
> Discover a side of the Caribbean that few visitors have the opportunity to experience.
>
> Enjoy private access to remarkable villas and historic estates, meet celebrated chefs and local personalities, or experience an intimate performance in an unforgettable setting.
>
> Go behind the scenes with artists, conservationists, rum makers, marine experts, and cultural storytellers who share their worlds with warmth and authenticity.
>
> These privileged encounters turn an itinerary into something deeply personal—creating stories your guests will continue sharing long after they return home.

**9. Sustainability & Authenticity**
> Our love for the Caribbean comes with a responsibility to protect its natural beauty, celebrate its cultures, and support the communities that make every experience possible.
>
> We work with trusted local partners to incorporate responsible choices throughout our programs—from locally sourced dining and community-led experiences to conservation initiatives, eco-conscious activities, and opportunities to give back.
>
> Every experience is thoughtfully designed to create a positive connection between guests and destination, ensuring that the beauty and spirit of our islands can be enjoyed for generations to come.

**Section closer** (dark band, large Fraunces italic):
> We transform every event and incentive program into a collection of meaningful moments—where Caribbean warmth meets thoughtful creativity, and every detail is brought beautifully to life.

---

## 8. CONTENT — `content/services.py`

Two groupings, then an **immersive 12-step arrival-to-departure journey**.

```python
SERVICE_CATEGORIES = [
  ("Corporate & MICE Excellence", [
      "Corporate Meetings", "Incentive Travel Programs", "International Conferences",
      "Product Launches & Brand Activations", "Executive Retreats",
      "Gala Dinners & Private Events", "Complete Event Production & Logistics"]),
  ("Curated Luxury Travel", [
      "Tailor-Made Itineraries", "Exclusive Villa & 5-Star Hotel Stays",
      "Private Transfers", "Curated Experiences & Local Experts",
      "Gastronomic Journeys", "Wellness & Cultural Immersions"]),
]

JOURNEY = [
  ("01","Airport Welcome","Meet & greet and seamless private transfers on arrival."),
  ("02","Transportation","Ground, ferry and charter logistics between islands."),
  ("03","Meetings & Conferences","Venues and full production for the working sessions."),
  ("04","Activities & Team Building","Curated experiences suited to the group and island."),
  ("05","Private Boats & Yachts","Charter excursions and on-water experiences."),
  ("06","Decoration & Event Design","Theming and production for every occasion."),
  ("07","Audiovisual & Production","Technical delivery for meetings and events."),
  ("08","Restaurants & Private Dining","From casual island fare to private chef dinners."),
  ("09","Entertainment","Live music, local performers, and evening programming."),
  ("10","Corporate Gifting","Locally sourced gifts and amenities."),
  ("11","On-site Management","Our team present throughout, start to finish."),
  ("12","Departure Assistance","Smooth transfers and send-off for every traveller."),
]
```

**Immersive presentation for `JOURNEY`:** a horizontal scroll-snap strip on a dark ground (`--ink`), each panel `flex: 0 0 190px`, `--ink-soft` background, gold index number, hairline right border. On desktop, hijack vertical scroll into horizontal movement while the section is pinned (use `position: sticky` + `transform: translateX()` driven by scroll progress — **not** a scroll-jacking library). On mobile it's a plain swipeable strip. Hovering a panel expands it to reveal an image.

Section head: kicker `WHAT WE HANDLE` · H2 `A journey from arrival to departure` · lede `Scroll to see every service woven into the program, in the order your group experiences it.`

---

## 9. CONTENT — `content/itinerary.py` (MODULE 4)

```python
ITINERARY = [
  ("Day 1","Arrival & welcome reception","Private terminal welcome, transfers to accommodation, and an evening welcome reception to open the program."),
  ("Day 2","Meeting & island experience","Morning working session at a dedicated venue, followed by an afternoon island excursion for the group."),
  ("Day 3","Team-building & private dinner","A guided team-building activity followed by a private dinner at a distinctive island venue."),
  ("Day 4","Catamaran experience & gala evening","A full-day catamaran excursion along the coast, followed by a gala evening to close the program."),
  ("Day 5","Departure assistance","Leisure morning, private transfers, and full departure coordination for every traveller."),
]
```

Kicker: `INSPIRATION, NOT A FIXED PACKAGE`
Note under the panel: `This is a sample structure only — every program is built from scratch around your group's goals, dates and destinations.`

---

## 10. CONTENT — `content/pricing.py` (MODULE 5)

```python
TIERS = [
  ("classic", "Classic — quality properties, core experiences",        260),
  ("premium", "Premium — upgraded properties, private experiences",    420),
  ("ultra",   "Ultra-luxury — villas, exclusive access",               850),
]

ISLAND_FACTOR = {
  "saint-martin": 1.00, "anguilla": 1.15, "st-barth": 1.35,
  "british-virgin-islands": 1.20, "barbados": 1.00,
  "dominica": 0.90, "grenada": 0.95,
}

CORE_FEE = 353          # per person: group dining + core activities

ADDONS = [
  ("transfers",     "Ground & inter-island transfers",  35),
  ("boat",          "Private boat charter / day cruise", 80),
  ("gala",          "Gala dinner & themed event",       100),
  ("decor",         "Décor & event production",          50),
  ("entertainment", "Entertainment & live performance",  70),
  ("concierge",     "Full concierge staffing",          100),
]

def estimate(island, tier_rate, nights, pax, addons):
    per_person = round((tier_rate * nights + CORE_FEE) * ISLAND_FACTOR[island] + sum(addons))
    return per_person, per_person * pax
```

**Verify against the client's own worked example:** Saint Martin · 60 people · 4 nights · Premium · transfers + boat + gala + décor → **$2,298 per person, $137,880 total.** If your numbers don't land there, the constants are wrong.

**Mandatory disclaimer:**
> Base package includes accommodation, group dining, and core activities. Add-ons above are priced per person on top. Excludes airfare. Final pricing depends on dates and availability.

CTA under the total: `TURN THIS INTO A REAL PROPOSAL` → prefills and scrolls to the event brief form.

---

## 11. THE FIVE INTERACTIVE MODULES

These are the build. Everything else is layout.

### MODULE 1 — Cinematic hero (`hero_video.html` + `hero.js`)

- Full-viewport `<video autoplay muted loop playsinline preload="metadata" poster="...">` with a Caribbean loop: destinations, events, sunset, party, meetings.
- Gradient overlay: `linear-gradient(0deg, rgba(8,20,21,.65), rgba(8,20,21,.1) 45%, rgba(8,20,21,.35))`
- H1 animates in **line by line** — each line in a `<span>` with `overflow:hidden`, inner `<em>` starting at `translateY(100%)`, animating to `0` with staggered delays `.15s / .32s / .49s`.
- CTAs fade in at `.9s`.
- Bottom-left: rotating scene caption (from `HERO["scenes"]`). Bottom-right: 4 thin dash indicators, clickable, auto-advance every 5s, pause on hover.
- Bottom-left below caption: `— Scroll` indicator.
- **Reduced motion / no video:** fall back to the poster still, no animation, H1 visible immediately.
- Cap video at ~6 MB. Serve `.mp4` (H.264) + `.webm`.

### MODULE 2a — Regional map (`map_region.html` + `map.js`)

The client was explicit: *"the final objective is to have a map of the region with all of the destinations. You should be able to click on each destination and there will be information."* And: *"Be creative on how you do the map, it should be nice and simple."*

- Dark section (`--ink`), inline **SVG** `viewBox="0 0 900 560"`.
- Draw faint concentric rings radiating from SXM to suggest reach without pretending to be a real chart.
- Each island = a `<g class="isle-dot">` with a pulsing outer circle, a solid core circle, and a `<text>` label. SXM is the hub — gold core, larger pulse.
- Dashed gold `<path>` routes from SXM to each island. Animate with `stroke-dasharray`/`stroke-dashoffset` so the route **draws itself** when its island is hovered or selected.
- **Click an island →** an information card slides open below the map containing:
  - Island name (Fraunces italic)
  - One-line intro
  - The connection chips from `CONNECTIONS` — e.g. `FERRY 20–25 min / frequent daily crossings`
  - **`Explore destination →`** button routing to `/explore-our-islands/<slug>`
- Section head: kicker `WHERE WE WORK` · H2 `Where will your story begin?` · lede `Move through our Caribbean. Select an island, then discover how your guests arrive and connect.`
- Hint under the map: `Layout is illustrative, not to nautical scale — travel times are planning estimates.`
- Keyboard accessible: each island is `tabindex="0"`, responds to Enter/Space, has `aria-label`.
- Mobile: map scales down; below 768px, replace the SVG with a vertical list of island rows that open the same card.

### MODULE 2b — Getting to Your Island (`getting_there.html`)

Two columns. Left: a Bootstrap accordion (fully restyled — hairline rules, no boxes, chevron on the right) with the 10 `GETTING_THERE` rows. Each row shows island name (Fraunces) left, access label (`Direct flight` / `Fly or boat via SXM` / `Via regional connection`) right in `--gold`. Expanding reveals approximate times from each of the four `ORIGINS`.

Right: a light SVG route diagram — origin city dots (Toronto, New York, Miami, Panama City) on the left, island dots on the right, dashed connecting lines with small aircraft glyphs at the midpoints. Selecting an accordion row highlights its routes.

Kicker `GETTING TO YOUR ISLAND`. Disclaimer from §6 sits under the accordion.

### MODULE 3 — Immersive destination page (`island_detail.html` + `island.js`)

**This is the biggest piece.** The reference site's destination pages are just a hero and a gallery — the client explicitly wants past that, borrowing the pattern from a yacht-charter site: click a destination and you get named sub-sections you move between without leaving the page.

Page structure:

1. **Full-bleed hero** — island image with slow Ken Burns zoom, island name in large Fraunces italic, headline beneath, scroll cue.
2. **Intro band** — the island's `intro` paragraph, large, generous leading, max 60ch, on `--paper`.
3. **Sticky sub-navigation** — three tabs, sticks below the main nav once scrolled past:
   - **THE ISLAND**
   - **GASTRONOMY**
   - **EXPERIENCES**
   Active tab underlined in `--gold-bright`. Clicking smooth-scrolls to the panel; scrolling updates the active tab (IntersectionObserver).
4. **Three panels**, each: a large lead image, 2–3 paragraphs, and a row of **expanding cards** (3–4 per panel). A card shows an image + title collapsed; clicking expands it in place to reveal a description. Only one open at a time. `prefers-reduced-motion` → instant.
5. **"Getting here"** strip — this island's row from `CONNECTIONS`, plus a link back to the map.
6. **Next island** — full-width image band linking to the next island in `ISLANDS` order, wrapping at the end.
7. **CTA band** — `Let's Create Your Caribbean Experience` → `/lets-connect`.

Write the panel copy per island from the island's own character (Saint Martin = French/Dutch duality; Dominica = rainforest and rivers; Grenada = spice and estates; etc.). Keep each panel to 2–3 short paragraphs — the client asked for *"short, emotional copy instead of long introductory paragraphs."*

### MODULE 4 — Five-day itinerary (`itinerary.html` + `itinerary.js`)

Pill tabs `Day 1 … Day 5`. Active pill = `--ink` fill, white text. Clicking swaps a two-column panel: image left (4:3), day label + Fraunces italic title + description right. Cross-fade the image on change (~.4s). Panel sits on `--white` with a `1px solid var(--line)` border, `2px` radius. Auto-advance is **off** — this one is user-driven.

Add a small `Get a Planning Estimate →` pill anchored bottom-right of the panel that scrolls to Module 5.

### MODULE 5 — Planning estimate (`estimator.html` + `estimator.js`)

Two-panel layout, **live-updating** — no wizard, no steps, no submit button to see the number.

**Left panel** (`--paper-dim`, `~55%`):
- Island — `<select>` from `ISLANDS`, value shown in `--gold` at the right of the label
- Group size — range slider, 10–300, step 5, live value right-aligned as `60 people`
- Nights on-island — range slider, 2–10, live value as `4 nights`
- Program tier — `<select>` from `TIERS`
- `Add to your program` — six checkboxes from `ADDONS`, each with `+$XX/pp` right-aligned in `--gold`

**Right panel** (`--ink`, `~45%`, white text):
- Label `ESTIMATED PROGRAM TOTAL`
- Total in large Fraunces italic `--gold-bright`, formatted `$137,880`, `font-variant-numeric: tabular-nums`
- Beneath: `≈ $2,298 per person`
- Then the disclaimer from §10
- Then the `TURN THIS INTO A REAL PROPOSAL` button

Recalculate on every `input` event. Animate the total counting up over ~400ms when it changes (skip under reduced motion). Heading above: `Get a ballpark number in 30 seconds.` Sub: `Tap a destination above, or set your own — the estimate updates live.`

**Also keep** the persistent floating pill from the prototype (`inquiry_fab.html`): bottom-right, `--ink` background, gold dot, `Get a Planning Estimate`. On click it scrolls to Module 5 on `/envision-your-experience`, or navigates there from other pages. This satisfies the brief's *"persistent but discreet inquiry button."*

---

## 12. FORMS & INTEGRATIONS

Three entry points on `/lets-connect`, presented as three tabs.

### Tab 1 — Submit an Event Brief
Fields (all required except the last two):

| Field | Type |
|---|---|
| Company | text |
| Contact name | text |
| E-mail | email |
| Phone | tel |
| Country | text |
| Type of request | select — *Corporate Retreat · Corporate Incentive · Meeting or Summit · Brand Activation* |
| Group size | number |
| Preferred dates | text (`e.g. March 2027`) |
| Average budget | select — *Under $100k · $100k–250k · $250k–500k · $500k+ · Not sure yet* |
| Tell us about your event | textarea |

**Destination: Sellsy CRM.** We have no API credentials yet, so:
- Build `services/sellsy.py` with a `create_opportunity(payload)` function.
- Read `SELLSY_CLIENT_ID` / `SELLSY_CLIENT_SECRET` from `.env`.
- **If credentials are absent, log the payload and write it to `instance/submissions.jsonl`, then return success.** The demo must never show an error.
- Map at minimum: contact name, e-mail, country, average budget (the four the client named), plus everything else as opportunity notes.

### Tab 2 — Upload an RFP
PDF upload (`.pdf` only, max 10 MB) + name, e-mail, company. Sends the file as an attachment to `karishma.singh@caraibes-incentive.com` via Flask-Mail. If SMTP isn't configured, save to `instance/rfps/` and log it.

### Tab 3 — Schedule a Call
Two options side by side:
- **Book a time** — embed a Microsoft Bookings iframe. URL comes from `TEAMS_BOOKING_URL` in `.env`; if unset, render a styled placeholder card reading *"Booking calendar — connect your Microsoft Bookings page"* so the demo still looks intentional.
- **WhatsApp** — `https://wa.me/<WHATSAPP_NUMBER>` button. If unset, hide the button, don't show a broken link.

All three: CSRF protected, client-side validation with custom (non-Bootstrap-blue) invalid styles, honeypot field for bots, success shown as an in-page confirmation panel that replaces the form — **not** a redirect, **not** a Bootstrap alert.

### Contact block (beside the form)
Fraunces italic `Contact Us`, then E-MAIL / CALL US / ADDRESS rows with thin icons. Use the RFP email as the general address until the client supplies a general one, and mark phone/address as `TBC` placeholders in `site.py` with a comment.

---

## 13. IMAGERY & VIDEO — read this before Phase 1

This is the one thing that will make or break the demo, and the client hasn't supplied assets.

Create `content/media.py` as a **single registry**, so swapping in real photography later is a one-file change:

```python
MEDIA = {
  "hero_video":      "video/hero.mp4",
  "hero_poster":     "img/hero-poster.jpg",
  "island.saint-martin.hero": "img/islands/saint-martin/hero.jpg",
  "island.saint-martin.the-island": [...],
  ...
}
def img(key): ...   # returns url_for('static', ...) with a graceful fallback
```

**For the demo, source free Caribbean imagery:**
1. Write `scripts/fetch_placeholders.py` that downloads from **Pexels** (free API key, generous limits) using per-slot search terms — e.g. `"saint martin caribbean beach"`, `"caribbean gala dinner"`, `"catamaran sailing caribbean"`, `"rainforest waterfall dominica"` — and saves them to the exact paths in `MEDIA`.
2. Hero video: grab a Caribbean aerial/beach loop from **Pexels Videos** or **Coverr**, trim to ~20s, compress to under 6 MB, generate a poster frame with `ffmpeg`.
3. Every `<img>` gets `loading="lazy"` (except above-the-fold), explicit `width`/`height` to stop layout shift, and `object-fit: cover`.

**Do not ship `picsum.photos` placeholders to a client demo** — grey abstract squares will read as unfinished. Real Caribbean photography, even stock, sells the concept.

**Tell the client** in your handover that ~95 images are needed for the real build: 54 experience gallery images (9 × 6), 21 destination panels (7 × 3), 7 destination heroes, 7 homepage cards, 5 itinerary days. Their existing photography and the French site are the first place to look.

---

## 14. DECISIONS ALREADY TAKEN (don't re-litigate these mid-build)

The source brief contradicts itself in a few places. These are resolved as follows — flag them to the client, but build this way:

| Issue | Decision |
|---|---|
| **Island count** — brief lists 7, prototype has 8 (with Saba), access table lists 10 | **7 full destination pages.** Saba, Guadeloupe, Martinique and Saint Lucia appear **only** in the Getting to Your Island access table. Adding a page later = one dict entry. |
| **"across Greece"** in the WHAT WE DO copy | Typo from the reference site. Ship **"across the Caribbean."** |
| **Long copy vs "short, emotional copy"** | Use the client's supplied paragraphs on the deep pages (they wrote them). On the **homepage and destination panels**, trim to the first 1–2 sentences — that's where the brief's "short, emotional copy" instruction applies. |
| **"Copy the website"** for services | Use both: the two service categories as the framing, and the 12-step journey as the immersive module. |
| **Missing "first landing page file"** | Rebuild Module 5 from the p.26 screenshot spec in §10. Don't wait for the file. |
| **Sellsy / Teams / WhatsApp credentials** | Build against `.env` with safe local fallbacks (§12). Demo works without any of them. |
| **Language** | English only. Structure `content/` so a `fr` variant could be added without touching templates. |
| **Logo** | Use a Fraunces italic wordmark `Caribbean Incentive` as a placeholder. Footer note: `Logo placeholder — replace with brand mark`. |

---

## 15. BUILD ORDER

Work in phases. **Run the app and check the browser at the end of each phase.**

**Phase 1 — Skeleton**
`app.py`, `config.py`, `requirements.txt`, `.env.example`, all of `content/`, `base.html`, `nav.html`, `footer.html`, `brand.css` with every token, all routes returning stub pages. Nav and footer working on every route. *Checkpoint: every URL loads, nav is styled, no Bootstrap blue anywhere.*

**Phase 2 — Homepage**
Hero (Module 1), intro, Where It All Begins teaser, Explore Our Caribbean grid, services journey strip, experiences circle grid, Endless Creations teaser, CTA band. *Checkpoint: homepage is demo-quality top to bottom.*

**Phase 3 — Module 2**
Regional map + Getting to Your Island, on `/connected-to-the-caribbean` and embedded on the homepage. *Checkpoint: clicking every island opens a card; every "Explore destination" link resolves.*

**Phase 4 — Module 3**
`island_detail.html` + all 7 islands with their three panels written. `islands_index.html`. *Checkpoint: all 7 pages complete, sticky sub-nav works, no lorem.*

**Phase 5 — Modules 4 & 5**
`/envision-your-experience` with the itinerary and the live estimator. Verify the $2,298 / $137,880 worked example. *Checkpoint: sliders update the total live.*

**Phase 6 — Content pages**
`/where-it-all-begins`, `/designed-around-you`, `/your-caribbean-journey` (all 9 experiences with galleries), `/endless-creations`.

**Phase 7 — Forms**
`/lets-connect`, all three tabs, WTForms, fallback storage, success panels.

**Phase 8 — Polish**
`motion.js` (reveal-on-scroll, parallax, cursor), mobile pass at 375px, reduced-motion pass, 404 page, meta tags + Open Graph, favicon, `README.md`.

---

## 16. ACCEPTANCE CHECKLIST

Before you call it done:

- [ ] Every nav link resolves; no 404s; no `href="#"`
- [ ] All 7 island pages complete with 3 written panels each
- [ ] All 9 experience categories present with full copy and 6-image strips
- [ ] Map: every island clickable, keyboard accessible, card opens, CTA routes correctly
- [ ] Getting to Your Island: 10 rows, disclaimer present
- [ ] Estimator: Saint Martin / 60 / 4 nights / Premium / transfers+boat+gala+décor = **$2,298 pp, $137,880 total**
- [ ] All three forms submit and show a success panel with no credentials configured
- [ ] Nothing reads as a Bootstrap default — check buttons, cards, accordion, form controls, focus rings
- [ ] `prefers-reduced-motion: reduce` disables all animation; content still fully visible
- [ ] No content hidden at `opacity: 0` waiting on an observer
- [ ] 375px wide: no horizontal scroll, nav offcanvas works, map falls back to list, estimator stacks
- [ ] No `picsum.photos` anywhere
- [ ] No text reads "Greece"
- [ ] Every `<img>` has `alt`, `loading`, `width`, `height`
- [ ] Lighthouse: Performance > 80, Accessibility > 95
- [ ] `README.md` explains setup, `.env` keys, and how to swap in real assets

---

## 17. FIRST MESSAGE TO CLAUDE CODE

Paste this to start:

> Read `CLAUDE_CODE_BUILD_PROMPT.md` in full before writing any code. Then build **Phase 1** exactly as specified in §15 — the Flask skeleton, the complete `content/` package with all copy from §5–§10 transcribed verbatim, `base.html` with nav and footer, and `brand.css` with every design token from §3. All routes should return a working stub page. Do not start Phase 2. When Phase 1 is done, run the app, confirm every route loads, and show me the file tree.
