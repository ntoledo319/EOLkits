"""Lead screening (store.py, "lead screening"): every submission is stored; the
status only decides the owner alert.

The fixtures are synthetic. Each one mirrors a pattern seen in the lead bus's
real submissions from June to September 2026 (prize and crypto link spam, the
one-line "what is your price" template in many languages, product and vendor
pitches, empty bot posts, bursts), with made-up names, addresses and ids. The
negative controls are the genuine inquiries screening must never hold back.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from datetime import UTC, datetime, timedelta

import pytest
from eolkits_grace.store import SPAM_LINK_HOSTS, lead_message_key, screen_lead_content

# ---- form shapes the Toledo sites post -------------------------------------- #


def contact(message: str, **extra: str) -> dict[str, str]:
    """toledotechnologies.com/contact (current version)."""
    return {
        "service": "general",
        "context": "Direct contact inquiry",
        "topic": "other",
        "budget": "not-sure",
        "message": message,
        **extra,
    }


def old_contact(message: str) -> dict[str, str]:
    """toledotechnologies.com/contact before July 2026."""
    return {"topic": "bug-fix", "budget": "15k-50k", "timeline": "2-weeks", "message": message}


def partner(agency_name: str, agency_website: str = "", notes: str = "q7x2rm") -> dict[str, str]:
    fields = {"context": "White-label engineering inquiry", "agency_name": agency_name}
    if agency_website:
        fields["agency_website"] = agency_website
    fields["notes"] = notes
    return fields


def care(work_description: str) -> dict[str, str]:
    return {
        "context": "Care plan fit inquiry",
        "system_type": "other",
        "plan_interest": "not-sure",
        "work_description": work_description,
    }


def discovery(goal: str) -> dict[str, str]:
    return {"budget": "not-sure", "timeline": "exploring", "goal": goal}


def status_of(fields, email: str = "someone@example.com") -> str:
    return screen_lead_content(email=email, fields=fields).status


# ---- spam: stored, never alerted -------------------------------------------- #

PRIZE_HEADLINES = [
    "THE $27,000,000 JACKPOT IS A ROUTE TO RICHES",
    "A SINGLE CLICK COULD SECURE THE $27,000,000 JACKPOT",
    "Step Into Luck with the $30,000,000 Jackpot",
    "A $25,000 promo code is your golden ticket",
    "Get hooked up with a $25,000 promo code",
    "ACHIEVE $1,500 PER DAY OR MORE THROUGH CRYPTO OPTIONS TRADING",
    "EARN $1,500 PER DAY OR MORE BY VALIDATING TRANSACTIONS ON POS CHAINS",
    "BE THE RANDOM WINNER OF THE PLAYSTATION 5 PRO 2TB",
    "An PlayStation 5 Pro 2TB award is being presented",
    "THE PLAYSTATION 5 PRO 2TB IS THE FANTASTIC REWARD",
    "BE THE SWEEPSTAKES WINNER OF LAMBORGHINI AVENTADOR",
    "The Lamborghini Aventador is the astonishing premium",
    "YOU ARE A NANOSECOND FROM WINNING LAMBORGHINI AVENTADOR",
    "IMPORTANT! 1.3426 BTC IS YOURS FOR WITHDRAWAL ACT QUICKLY",
    "URGENT MESSAGE! TAKE THE BENEFIT OF YOUR 1.3426 BTC",
]


@pytest.mark.parametrize("headline", PRIZE_HEADLINES)
def test_prize_and_crypto_link_spam(headline):
    # As received: the headline, then a Telegraph page or a shortener.
    for link in (
        "https://telegra.ph/Win-the-jackpot-today-Message-ID-000001-09-01",
        "https://cut.gl/Zx9Qa",
    ):
        for form in (contact(f"{headline} {link}"), old_contact(f"{headline} {link}")):
            assert status_of(form) == "spam", (headline, link)


@pytest.mark.parametrize("headline", PRIZE_HEADLINES)
def test_spam_wording_alone_catches_a_new_shortener(headline):
    """The next campaign will use a host nobody has listed yet."""
    verdict = screen_lead_content(
        email="x@example.com", fields=contact(f"{headline} https://brand-new-short.example/k3Jd")
    )
    assert verdict.status == "spam"
    assert verdict.reason.startswith("link with ")


@pytest.mark.parametrize("host", SPAM_LINK_HOSTS)
def test_every_listed_spam_host_with_neutral_wording(host):
    for text in (f"Please see https://{host}/aB3dE", f"see {host}/aB3dE", f"https://go.{host}/x"):
        verdict = screen_lead_content(email="x@example.com", fields=contact(text))
        assert verdict == ("spam", f"link to a known spam host ({host})"), text


def test_telegraph_crypto_spam_in_the_partner_form():
    for name in (
        "📈 Transfer of funds to your name. RECEIVE >>> "
        "graph.org/TRANSACTION-01-01-1?hs=0a1b2c3d4e5f& <<< 📈",
        "🤑 Transfer of funds to your name. Receive a funds transfer >>> "
        "graph.org/TRANSACTION-01-01-1?hs=0a1b2c3d4e5f& <<< 🤑",
        "📈 Top Up 169.30 USDT -> graph.org/BALANCE-1234567-USD-01-01-1?hs=0a1b2c& 📈",
        "📆 Transaction to you.Continue > graph.org/BALANCE-12345-US-DOLLARS-01-01-2?hs=0a1b& <<< 📆",
    ):
        form = partner(name, "graph.org/BALANCE-12345-US-DOLLARS-01-01-2")
        assert status_of(form) == "spam", name
        # The wording is enough even on a host that is not listed.
        unlisted = partner(name.replace("graph.org", "pages.example"), "")
        assert status_of(unlisted) == "spam", name


def test_fake_exchange_transfer_on_a_status_page_host():
    form = partner(
        "🔓 Transfer № E1234 from Coinbase. GET =>> "
        "examplesup.statuspage.io/#about-this-site?hs=0a1b2c&  🔓",
        "examplesup.statuspage.io/#about-this-site",
    )
    assert screen_lead_content(email="x@example.com", fields=form) == (
        "spam",
        "link with crypto spam wording",
    )


def test_html_and_forum_link_markup_is_spam():
    for message in (
        "аренда авто <a href=https://car-rental.example/>аренда авто</a>",
        '<A  class="x" HREF="https://casino.example">best</a>',
        "<a href='//pills.example/buy'>cheap</a>",
        "[url=https://pills.example]cheap[/url]",
    ):
        assert screen_lead_content(email="x@example.com", fields=contact(message)) == (
            "spam",
            "HTML link markup",
        )


def test_quoted_html_with_relative_links_is_not_link_markup():
    """A visitor may paste a piece of their own page; link spam always points
    at another site."""
    for message in (
        'Our nav has <a class="nav" href="/about">About</a> and it breaks on iPhone. '
        "Can you fix?",
        'The footer link <a href="#contact">Contact</a> jumps to the wrong part of the page.',
    ):
        assert screen_lead_content(email="x@example.com", fields=contact(message)) == ("ok", "")


def test_campaign_wording_needs_a_link_after_it_in_the_same_field():
    """Every campaign put its link right after its phrase, in the same field."""
    headline = "THE $27,000,000 JACKPOT IS A ROUTE TO RICHES"
    link = "https://brand-new-short.example/k3Jd"
    assert status_of(contact(f"{headline} {link}")) == "spam"
    # The phrase alone, the visitor's own link before it, or the link in
    # another field (the Website field of the Fit Check, say) is not the spam.
    assert status_of(contact(headline)) == "ok"
    assert status_of(contact(f"Our site {link} shows this banner: {headline}")) == "ok"
    assert status_of(contact(headline, website=link)) == "ok"
    fit_check = {
        "service": "Delphi Fit Check",
        "website": "https://lotto-results.example",
        "goal": "Our banner reads 'the $10,000,000 jackpot' and must stay on the new site",
    }
    assert status_of(fit_check) == "ok"


def test_loan_offer_with_a_link_is_spam_and_without_one_is_a_pitch():
    offer = (
        "Dear Sirs/ma, Take advantage of our limited time loan offer and gain vital access to "
        "a flexible repayment plan. Instant approval, No collateral required. To proceed, "
        "kindly reply to this email with your confirmation. Don't miss out."
    )
    assert status_of(contact(offer + " Apply: https://loans.example/apply")) == "spam"
    assert screen_lead_content(email="x@example.com", fields=contact(offer)) == (
        "suspect",
        "sales pitch wording",
    )


# ---- suspect: still alerted, subject prefixed "Likely spam: " ---------------- #

PRICE_ONE_LINERS = [
    "Hi, მინდოდა ვიცოდე თქვენი ფასი.",  # Georgian
    "Hallo, ek wou jou prys ken.",  # Afrikaans
    "Sveiki, es gribēju zināt savu cenu.",  # Latvian
    "Sveiki, aš norėjau sužinoti jūsų kainą.",  # Lithuanian
    "Ciao, volevo sapere il tuo prezzo.",  # Italian
    "Ola, quería saber o seu prezo.",  # Galician
    "Hola, quería saber tu precio..",  # Spanish
    "Γεια σου, ήθελα να μάθω την τιμή σας.",  # Greek
    "Salam, qiymətinizi bilmək istədim.",  # Azerbaijani
    "Ողջույն, ես ուզում էի իմանալ ձեր գինը.",  # Armenian
    "Hi, ego volo scire vestri pretium.",  # Latin
    "Hallo, ich wollte Ihren Preis wissen.",  # German
    "Bonjour, je voulais connaître votre prix.",  # French
    "Здравствуйте, я хотел узнать вашу цену.",  # Russian
    "Merhaba, fiyatınızı öğrenmek istedim.",  # Turkish
    "Hei, halusin tietää hinnan.",  # Finnish
    "你好，我想知道你们的价格。",  # Chinese
    "Hi, I wanted to know your price.",
    "What are your prices?",
]


@pytest.mark.parametrize("message", PRICE_ONE_LINERS)
def test_one_line_price_question_in_any_language(message):
    verdict = screen_lead_content(email="someone@gmail.example", fields=contact(message))
    assert verdict == ("suspect", "one-line price question")


PITCHES = {
    "product with discount": (
        "Good Morning\r\n\r\nI wanted to reach out and let you know about our new dog harness. "
        "It's easy to put on in 2 seconds.\r\n\r\nGet yours today with 50% OFF: "
        "https://harness.example\r\n\r\nFREE Shipping - TODAY ONLY!\r\n\r\nThank You,\r\n\r\nJo"
    ),
    "second product": (
        "Hi,\r\n\r\nI hope you're doing well. I wanted to let you know about our new travel "
        "backpacks.\r\n\r\nOrder yours now at 50% OFF with FREE Shipping: http://bags.example"
    ),
    "posture gadget": (
        "Hey\r\n\r\nLooking to improve your posture? Our corrector is here to help!\r\n\r\n"
        "Grab it today at a fantastic 60% OFF: https://posture.example\r\n\r\n"
        "Plus, enjoy FREE shipping for today only! Don't miss out on this amazing deal."
    ),
    "contact-form ads": (
        "Good morning! example-studio.test,\r\nI recently visited example-studio.test and "
        "wanted to share something that might interest you.\r\nCompanies regularly use "
        "contact pages to share their offers.\r\nLet us know if this looks relevant.\r\n"
        "Telegram - https://t.me/ExampleChannel\r\nWhatsApp https://wa.me/+10000000000\r\n"
        "We only use chat for communication."
    ),
    "redesign agency": (
        "Hi, I'm Sam from an agency. We help businesses redesign their websites. I took a "
        "quick look at your site and saw a few opportunities to improve the design. I'd be "
        "happy to share a few quick ideas. Grab a time here: https://calendar.agency.example/"
    ),
    "developer matching": (
        "Hi,\n\nLooking for a development partner? We match you with top-rated, vetted "
        "development companies from our network. No cost, no obligation to move forward.\n\n"
        "See how it works → https://www.matching.example/"
    ),
    "freelance writer": (
        "Hey! Do you have any use for a freelance writer? I have a decade of experience and "
        "I'm currently looking for new opportunities. You can book a time with me: "
        "https://calendly.com/example-writer/30min"
    ),
}


@pytest.mark.parametrize("name", PITCHES)
def test_unsolicited_pitches_are_suspect(name):
    verdict = screen_lead_content(email="rep@vendor.example", fields=contact(PITCHES[name]))
    assert verdict == ("suspect", "sales pitch wording")


def test_a_pitch_in_the_partner_notes_field_is_suspect():
    form = partner("Sam Rivera", notes=PITCHES["developer matching"])
    assert status_of(form, "sam@matching.example") == "suspect"


def test_sent_from_the_studio_own_domain_is_suspect():
    pitch = screen_lead_content(
        email="sales@toledotechnologies.com", fields=contact(PITCHES["product with discount"])
    )
    assert pitch == ("suspect", "sales pitch wording; sent from the studio's own domain")
    plain = screen_lead_content(
        email="Someone@Apps.ToledoTechnologies.com",
        fields=contact("Testing the form after the update, please ignore this one."),
    )
    assert plain == ("suspect", "sent from the studio's own domain")
    assert status_of(contact("Testing the checkout copy, ignore."), "a@eolkits.com") == "suspect"
    # A look-alike domain is not the studio's.
    assert (
        status_of(contact("We need a new site for our shop."), "a@nottoledotechnologies.com")
        == "ok"
    )


@pytest.mark.parametrize(
    "form",
    [
        {},
        {"service": "general", "context": "Direct contact inquiry"},
        {"service": "general", "context": "Direct contact inquiry", "message": "   "},
        care("kq3vzr"),
        discovery("w8ptsd"),
        contact("Hello"),
        contact("", topic="mobile", budget="15k-50k"),
    ],
    ids=[
        "no fields",
        "hidden fields only",
        "blank",
        "care token",
        "discovery token",
        "hello",
        "choices",
    ],
)
def test_empty_submissions_are_suspect(form):
    assert screen_lead_content(email="x@example.com", fields=form) == (
        "suspect",
        "empty or one-word message",
    )


# ---- negative controls: genuine inquiries stay ok --------------------------- #

GENUINE = {
    "own site, budget, pricing": contact(
        "Hi, we're a 12-person accounting firm. Our WordPress site "
        "(https://www.example-cpa.com) is slow and hard to update. Budget is around "
        "$15,000-$20,000 and we'd like to launch this fall. What would pricing look like?"
    ),
    "price with substance": contact(
        "Hi, what's your price to migrate a 40-page Squarespace site to something we own?"
    ),
    "price question, longer": contact(
        "Hello! I'd like to know your price for a care plan. We have a small Next.js app on "
        "Vercel and nobody to look after it since our developer left."
    ),
    "spanish with substance": contact("Hola, quería saber el precio de una tienda online."),
    "budget numbers": old_contact(
        "Budget is $25,000. We need the booking flow rebuilt and live by March 1."
    ),
    "crypto startup": contact(
        "We're a small crypto payments startup (https://example-pay.io) and need our "
        "marketing site rebuilt before a funding announcement."
    ),
    "promo codes": contact(
        "Our Shopify checkout needs to accept a promo code per customer group. Store: "
        "https://shop.example.com"
    ),
    "rewards club": contact(
        "We need a members page where our rewards club shows each month's prize: "
        "https://club.example.org"
    ),
    "arcade jackpot": contact(
        "We build jackpot displays for family arcades and want a dashboard to manage them; "
        "see https://arcade.example"
    ),
    "lender": contact(
        "We're a community lender. Our loan application page must pass an accessibility "
        "review. Site: https://lender.example"
    ),
    "telegram contact": contact(
        "Need a Telegram bot that posts our store's new arrivals. Reach me at "
        "https://t.me/example_owner"
    ),
    "visited and booking": contact(
        "Hi, I visited your website and would like to book a call about our WordPress site."
    ),
    "agency partner": partner(
        "Northwind Studio",
        "https://northwind.example",
        "We help businesses with branding and need a dev partner for two client builds. "
        "Can we book a call?",
    ),
    "care plan": care("Our Django app needs security updates and someone on call."),
    "discovery": discovery("Replace our spreadsheet quoting with a small internal tool"),
    "fit check": {
        "service": "Delphi Fit Check",
        "context": "First-step brief; cost, page count, access, and launch window collected "
        "during the paid assessment",
        "offer": "$750 fixed; 100% upfront; 50% credited toward the kickoff Project "
        "Retainer within 30 days",
        "website": "https://my-shop.example",
        "platform": "WordPress",
    },
    "migration audit": {
        "service": "Website Migration Audit",
        "offer": "$1,500 fixed; 100% upfront; qualifying project within 30 days receives a "
        "50% credit",
        "website": "https://old-site.example",
        "goal": "Move off Wix and keep our search rankings",
    },
    "mobile checkboxes": {
        "platform": "iOS native, Android native",
        "summary": "Need an MVP in 8 weeks",
    },
    "short but specific": contact("Can you fix our broken contact form?"),
    "shop sale": contact(
        "Our Black Friday 20% off sale crashed the site and we lost orders. Can we book a "
        "call this week?"
    ),
    "shipping rules": contact(
        "We need free shipping rules for orders over $50 in our Shopify store. Can we get it "
        "done by May?"
    ),
    "our launch": contact(
        "Wanted to let you know about our launch plans: the site must be ready by June. "
        "Can we book a call?"
    ),
    "freelancers partnering": partner(
        "Two freelance developers",
        "https://pair.example",
        "We're looking for new projects to partner on with a studio like yours. Book a call?",
    ),
    "one-word-looking url": {"website": "https://acme-bakery.example"},
    "chinese inquiry": contact("我们需要一个新的网站，大约十个页面。"),
    "automation blueprint": {
        "context": "Five-field Automation Blueprint inquiry",
        "workflow_to_automate": "Weekly grade reports for our school",
    },
    # Genuine inquiries on the topics the spam campaigns borrow, each with a
    # link to the visitor's own site. None of them uses a campaign's phrase.
    "design awards": contact(
        "Have you won any design awards? We want a premium site; ours is https://firm.example"
    ),
    "won me over": contact(
        "Loved the case study at https://toledotechnologies.com/work - you won me over. We "
        "need a new site for our bakery."
    ),
    "won our business": contact(
        "After reading your blog at www.toledotechnologies.com/blog you've won our business - "
        "we need a Shopify rebuild."
    ),
    "remittance app": contact(
        "We're building an app for international funds transfer between small businesses. "
        "Current site: https://acme-remit.com. Can you help with the MVP?"
    ),
    "payroll transfers": contact(
        "Our platform handles the transfer of funds for payroll; see https://payco.example. "
        "Need a dashboard rebuild."
    ),
    "payment notification": contact(
        "Our payment app sends a notification 'transaction to you' - site https://pay.example "
        "needs rework"
    ),
    "wallet app": contact(
        "Our wallet app shows '0.5 BTC is yours' after purchase and lets users top up 50 USDT; "
        "landing page https://wallet.example"
    ),
    "wallet flow": contact(
        "Our wallet flow is: top up 50 USDT -> confirm -> done. The current app is at "
        "https://wallet.example"
    ),
    "rental marketplace": contact(
        "Hosts on our platform earn $1,500 per day or more from bookings; we need the listing "
        "pages rebuilt: https://stays.example"
    ),
    "crypto education": contact(
        "Our crypto trading education site claims users earn $1,500 per day or more; we need "
        "a compliance review of https://edu.example"
    ),
    "charity raffle": contact(
        "Our charity raffle needs a page that announces the lucky winner each month. Current "
        "site: https://kids-charity.org"
    ),
    "giveaway tool": contact(
        "We run weekly giveaways on https://ourshop.example and need a tool that picks a "
        "random winner and emails them."
    ),
    "sweepstakes page": contact(
        "We host a sweepstakes each month and need the sweepstakes winner page rebuilt: "
        "https://promo.example"
    ),
    "esports prize": contact(
        "We're giving away a PlayStation 5 as the prize at our esports tournament and need a "
        "signup site like https://ourleague.gg"
    ),
    "car dealer": contact(
        "We sell pre-owned Lamborghini models and our award-winning showroom needs a new "
        "inventory site: https://exotics.example"
    ),
    "casino promo": contact(
        "We run a licensed online casino; our promo page for free spins at "
        "https://casino.example is broken on mobile."
    ),
    "loyalty rewards": contact(
        "We want a 'claim your reward' flow for our coffee loyalty app, see https://beans.example"
    ),
    "equipment lender": contact(
        "We're a small business lender offering instant approval on equipment loans. Our site "
        "https://lendco.example needs a redesign."
    ),
    "microloans": contact(
        "We offer microloans with no collateral to farmers. Please rebuild https://agri-loans.example"
    ),
    "loan offer page": contact(
        "We need a new loan offer page on https://creditunion.example with a calculator."
    ),
    "fit check loan flow": {
        "service": "Delphi Fit Check",
        "offer": "$750 fixed",
        "website": "https://mybank.example",
        "platform": "WordPress",
        "goal": "Add an instant approval flow for our loan offer page",
    },
    "fit check remittance": {
        "service": "Delphi Fit Check",
        "website": "https://remit-app.example",
        "goal": "Build a funds transfer MVP for immigrants sending money home",
    },
    # Outreach manners alone are how real prospects write too.
    "polite prospect": contact(
        "Hope this email finds you well. We'd like to book a call about a new website for our "
        "dental practice. Let us know if you have time next week."
    ),
    "visited, call, whatsapp": contact(
        "Hi, I visited your website. Can we book a call? I prefer WhatsApp."
    ),
}


@pytest.mark.parametrize("name", GENUINE)
def test_genuine_inquiries_are_ok(name):
    assert screen_lead_content(email="person@example.com", fields=GENUINE[name]) == ("ok", "")


def test_the_email_address_itself_is_not_judged_as_the_message():
    fields = {
        "email": "jackpot.winner@example.com",
        "message": "We need a site; see https://a.example",
    }
    assert status_of(fields, "jackpot.winner@example.com") == "ok"
    fields = {"email": "someone@telegra.ph", "message": "Please send me a quote for a new logo."}
    assert status_of(fields, "someone@telegra.ph") == "ok"


def test_screening_stays_fast_on_hostile_64kb_input():
    """The lead endpoint accepts 64 KiB; no rule may go quadratic on it."""
    size = 64 * 1024
    hostile = [
        "<a " * (size // 3),
        "1" * size + " btc",
        "a." * (size // 2),
        "win " * (size // 4) + "lamborghini",
        "lamborghini " * (size // 12),
        "transfer no " * (size // 12),
        "transfer no 1" * (size // 13),
        "top up 1 btc " * (size // 13),
        "top up 1 btc -> " + "a." * (size // 2),
        "top up 1 btc ->" * (size // 15),
        "playstation 5 " * (size // 14),
        "transaction to you." * (size // 19),
        "$10,000 jackpot " * (size // 16),
        "<a href=" * (size // 8),
        "<a " + "x" * size,
        "visited " + "a" * size,
        "$1," + "000," * (size // 4),
        "x" * size,
        "graph.org" * (size // 9),
        "fiyat" * (size // 5),
    ]
    for text in hostile:
        started = time.perf_counter()
        screen_lead_content(email="x@example.com", fields=contact(text))
        screen_lead_content(email="x@example.com", fields=text)  # stored text, cut short
        assert time.perf_counter() - started < 1.5, text[:20]


def test_message_key_ignores_picked_options_and_case():
    one = json.dumps(old_contact("Hello THERE, need a site"))
    two = json.dumps({**old_contact("hello there,   need a site"), "topic": "feature"})
    assert lead_message_key(one) == lead_message_key(two) == ("hello there, need a site", True)
    assert lead_message_key(json.dumps(care("kq3vzr"))) == ("", False)
    assert lead_message_key('{"message": "cut sho') == ('{"message": "cut sho', True)


# ---- duplicates: judged against earlier rows, in the insert transaction ------ #


@pytest.fixture
def store(fresh_import, tmp_path):
    return fresh_import("eolkits_grace.store").Store(tmp_path / "leads.sqlite3")


def _capture(store, email: str, fields: dict[str, str], **kw) -> tuple[str, str]:
    lead = store.record_screened_lead(email=email, fields={"email": email, **fields}, **kw)
    return lead.status, lead.reason


def test_a_burst_of_identical_submissions_alerts_once(store):
    form = contact("We need a booking page for our clinic within six weeks.")
    got = [_capture(store, "visitor@example.com", form) for _ in range(5)]
    assert got[0] == ("ok", "")
    assert got[1:] == [
        ("duplicate", "repeat of lead 1 within 10 minutes"),
        ("duplicate", "repeat of lead 2 within 10 minutes"),
        ("duplicate", "repeat of lead 3 within 10 minutes"),
        ("duplicate", "repeat of lead 4 within 10 minutes"),
    ]
    assert len(store.recent_leads(100)) == 5  # all stored


def test_simultaneous_identical_submissions_alert_once(store):
    """The duplicate check and the insert share one IMMEDIATE transaction, so
    requests arriving at the same moment are still judged one after another."""
    form = contact("We need a booking page for our clinic within six weeks.")
    barrier = threading.Barrier(6)
    results: list[str] = []

    def submit() -> None:
        barrier.wait()
        results.append(_capture(store, "visitor@example.com", form)[0])

    threads = [threading.Thread(target=submit) for _ in range(6)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=60)
    assert sorted(results) == ["duplicate"] * 5 + ["ok"]
    assert len(store.recent_leads(100)) == 6


def test_a_burst_of_identical_spam_is_spam_every_time(store):
    for topic in ("feature", "codebase", "bug-fix", "bug-fix", "nonprofit"):
        form = old_contact("IMPORTANT! 1.3426 BTC IS YOURS FOR WITHDRAWAL https://shorto.link/Ab1")
        assert _capture(store, "bot@example.net", {**form, "topic": topic})[0] == "spam"


def test_a_bot_hitting_three_forms_in_a_minute(store):
    email = "bot@forms-bot.example"
    assert _capture(store, email, care("kq3vzr"), product="New Care Plan Inquiry") == (
        "suspect",
        "empty or one-word message",
    )
    assert _capture(store, email, discovery("w8ptsd"), product="New Discovery Routing Inquiry") == (
        "duplicate",
        "repeat of lead 1 within 10 minutes",
    )
    spam = partner(
        "📈 Transfer of funds to your name. RECEIVE >>> graph.org/TRANSACTION-01-01-1 <<< 📈",
        "graph.org/TRANSACTION-01-01-1",
    )
    assert _capture(store, email, spam, product="New Partner Inquiry")[0] == "spam"


def test_an_empty_follow_up_after_a_pitch_is_a_duplicate(store):
    email = "sam@agency.example"
    assert _capture(store, email, contact(PITCHES["redesign agency"]))[0] == "suspect"
    empty = {"service": "general", "context": "Direct contact inquiry"}
    assert _capture(store, email, empty) == ("duplicate", "repeat of lead 1 within 10 minutes")


def test_a_real_follow_up_on_another_form_is_not_a_duplicate(store):
    email = "dana@example.com"
    assert _capture(store, email, contact("Our app crashes on login since the update."))[0] == "ok"
    follow_up = care("We would also like a monthly care plan once the crash is fixed.")
    assert _capture(store, email, follow_up) == ("ok", "")


def test_the_same_message_after_ten_minutes_is_not_a_duplicate(store):
    form = contact("Please send me a quote for a five-page website.")
    first = store.record_screened_lead(email="a@example.com", fields=form).id
    with store.connect() as conn:
        conn.execute(
            "UPDATE leads SET ts = ? WHERE id = ?",
            ((datetime.now(UTC) - timedelta(minutes=10, seconds=5)).isoformat(), first),
        )
    assert _capture(store, "a@example.com", form) == ("ok", "")


def test_duplicates_need_the_same_address(store):
    form = contact("Please send me a quote for a five-page website.")
    assert _capture(store, "a@example.com", form)[0] == "ok"
    assert _capture(store, "b@example.com", form)[0] == "ok"
    assert _capture(store, "b@example.com", {})[0] == "duplicate"
    assert _capture(store, "c@example.com", {}) == ("suspect", "empty or one-word message")


def test_address_case_and_spaces_do_not_hide_a_duplicate(store):
    form = contact("Please send me a quote for a five-page website.")
    assert _capture(store, " Visitor@Example.COM ", form)[0] == "ok"
    assert _capture(store, "visitor@example.com", form)[0] == "duplicate"


def test_a_long_message_cut_short_in_storage_still_deduplicates(store):
    form = contact("We need help with our platform. " * 400)
    assert _capture(store, "long@example.com", form)[0] == "ok"
    assert _capture(store, "long@example.com", form)[0] == "duplicate"
    other = contact("A different, equally long request about our intranet. " * 300)
    assert _capture(store, "long@example.com", other)[0] == "ok"


def test_a_failing_rule_keeps_the_lead_ok(store, monkeypatch, fresh_import, caplog):
    store_module = __import__(type(store).__module__, fromlist=["x"])

    def broken(**_):
        raise RuntimeError("rule bug")

    monkeypatch.setattr(store_module, "screen_lead_content", broken)
    monkeypatch.setattr(store_module, "lead_message_key", broken)
    assert _capture(store, "a@example.com", contact("x")) == ("ok", "not screened (rule error)")
    assert _capture(store, "a@example.com", contact("x")) == ("ok", "not screened (rule error)")
    assert len(store.recent_leads(10)) == 2
    assert "lead screening failed" in caplog.text
    assert "duplicate check failed" in caplog.text


# ---- the migration ---------------------------------------------------------- #

OLD_COLUMNS = ("id", "ts", "email", "name", "product", "source", "fields", "notified")


def _old_database(path, *, with_notified: bool = True) -> list[tuple]:
    """A `leads` table as production has it before lead screening (abd1519e),
    or as it was before notify-hardening. Returns the rows as written."""
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE leads (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL, "
        "email TEXT NOT NULL, name TEXT, product TEXT, source TEXT, fields TEXT"
        + (", notified INTEGER NOT NULL DEFAULT 0" if with_notified else "")
        + ")"
    )
    conn.execute("CREATE INDEX idx_leads_ts ON leads(ts)")
    rows = [
        (
            "2026-06-19T10:05:00+00:00",
            "bot@example.net",
            "Bot",
            "Contact",
            "site",
            json.dumps(old_contact("THE $27,000,000 JACKPOT https://telegra.ph/x-1")),
            1,
        ),
        (
            "2026-07-01T09:00:00+00:00",
            "dana@example.com",
            "Dana",
            "Apps",
            "apps",
            json.dumps(contact("We need an internal tool for scheduling.")),
            0,
        ),
        ("2026-07-02T09:00:00+00:00", "x@example.com", None, None, None, '{"message": "cut', 1),
    ]
    for row in rows:
        values = row if with_notified else row[:-1]
        columns = "ts, email, name, product, source, fields" + (
            ", notified" if with_notified else ""
        )
        conn.execute(
            f"INSERT INTO leads({columns}) VALUES ({', '.join('?' for _ in values)})", values
        )
    conn.commit()
    conn.close()
    return rows


def _snapshot(path, columns=OLD_COLUMNS) -> list[tuple]:
    conn = sqlite3.connect(path)
    try:
        return conn.execute(f"SELECT {', '.join(columns)} FROM leads ORDER BY id").fetchall()
    finally:
        conn.close()


def test_migration_adds_status_and_changes_nothing_else(fresh_import, tmp_path):
    Store = fresh_import("eolkits_grace.store").Store
    db = tmp_path / "prod.sqlite3"
    _old_database(db)
    before = _snapshot(db)

    store = Store(db)  # runs init(): the migration
    assert _snapshot(db) == before  # every old value, byte for byte
    assert [(row["status"], row["status_reason"]) for row in reversed(store.recent_leads(10))] == [
        ("ok", None)
    ] * 3
    assert store.has_lead_status()
    Store(db)  # idempotent: a second start changes nothing
    Store(db).init()
    assert _snapshot(db, (*OLD_COLUMNS, "status", "status_reason")) == [
        (*row, "ok", None) for row in before
    ]
    # An old row still owed an alert stays in the re-send queue, as before.
    assert [row["email"] for row in store.unnotified_leads()] == ["dana@example.com"]
    # New submissions are screened.
    assert store.record_screened_lead(email="n@example.com", fields={}).status == "suspect"


def test_migration_of_a_table_from_before_notify_hardening(fresh_import, tmp_path):
    Store = fresh_import("eolkits_grace.store").Store
    db = tmp_path / "older.sqlite3"
    _old_database(db, with_notified=False)
    store = Store(db)
    rows = list(reversed(store.recent_leads(10)))
    assert [(r["notified"], r["status"]) for r in rows] == [(1, "ok")] * 3
    assert store.count_unnotified() == 0


def test_rolled_back_code_can_still_write_to_a_migrated_table(fresh_import, tmp_path):
    """If the deploy is rolled back, the previous code inserts without the new
    columns; the defaults make its rows ordinary 'ok' leads."""
    Store = fresh_import("eolkits_grace.store").Store
    db = tmp_path / "prod.sqlite3"
    _old_database(db)
    Store(db)
    conn = sqlite3.connect(db)
    conn.execute(
        "INSERT INTO leads(ts, email, name, product, source, fields) VALUES (?, ?, ?, ?, ?, ?)",
        (datetime.now(UTC).isoformat(), "old-code@example.com", None, None, None, "{}"),
    )
    conn.commit()
    row = conn.execute(
        "SELECT status, status_reason, notified FROM leads ORDER BY id DESC"
    ).fetchone()
    conn.close()
    assert row == ("ok", None, 0)


# ---- owner alerts ----------------------------------------------------------- #

PRICE = {
    "email": "quote@example.org",
    "product": "Apps",
    "message": "Ciao, volevo sapere il tuo prezzo.",
}
REAL = {
    "email": "dana@example.com",
    "product": "Apps",
    "message": "Our booking site needs online payments before the holidays.",
}
SPAM = {
    "email": "lucky@example.net",
    "product": "Apps",
    "message": "THE $27,000,000 JACKPOT IS YOURS https://telegra.ph/Win-000001-09-01",
}


def test_alerts_follow_the_status(load_grace):
    mod, client = load_grace()
    for form in (REAL, PRICE, SPAM, REAL):
        assert client.post("/api/v1/lead", data=form).status_code == 200
    rows = {row["id"]: row for row in mod.store.recent_leads(10)}
    assert [rows[i]["status"] for i in (1, 2, 3, 4)] == ["ok", "suspect", "spam", "duplicate"]
    assert [(e["subject"], e["key"].split("-")[2]) for e in mod.sent_emails] == [
        ("New lead: Apps", "1"),
        ("Likely spam: New lead: Apps", "2"),
    ]
    ok_html, suspect_html = (e["html"] for e in mod.sent_emails)
    assert "Screened as likely spam" not in ok_html
    assert "Screened as likely spam: one-line price question." in suspect_html
    assert ok_html == mod._lead_email_html(
        "Apps", "", {"email": REAL["email"], "message": REAL["message"]}
    )
    assert [rows[i]["notified"] for i in (1, 2, 3, 4)] == [1, 1, 0, 0]
    # Nothing is owed: spam and duplicates are not in the re-send queue.
    assert mod.store.count_unnotified() == 0
    assert mod.resend_unnotified_leads() == {"attempted": 0, "still_unnotified": 0}
    assert len(mod.sent_emails) == 2


def test_the_resend_sweep_skips_spam_and_keeps_the_suspect_prefix(load_grace, monkeypatch):
    mod, client = load_grace()
    from eolkits_grace.email import EmailDeliveryError

    def outage(settings, **_):
        raise EmailDeliveryError("provider down", retryable=True)

    monkeypatch.setattr(mod, "send_email", outage)
    for form in (PRICE, SPAM, SPAM, REAL):
        client.post("/api/v1/lead", data=form)
    assert mod.store.count_unnotified() == 2  # the suspect and the ok lead

    sent: list[dict] = []
    monkeypatch.setattr(mod, "send_email", lambda settings, **kw: sent.append(kw) or {"ok": 1})
    assert mod.resend_unnotified_leads() == {"attempted": 2, "still_unnotified": 0}
    assert [e["subject"] for e in sent] == ["Likely spam: New lead: Apps", "New lead: Apps"]
    assert "Screened as likely spam: one-line price question." in sent[0]["html"]
    assert mod.resend_unnotified_leads() == {"attempted": 0, "still_unnotified": 0}
    assert [r["notified"] for r in reversed(mod.store.recent_leads(10))] == [1, 0, 0, 1]


def test_an_unreadable_status_still_alerts(load_grace, monkeypatch):
    mod, client = load_grace()

    def broken(lead_id):
        raise sqlite3.OperationalError("database is locked")

    monkeypatch.setattr(mod.store, "lead_screen", broken)
    assert client.post("/api/v1/lead", data=SPAM).json() == {"ok": True, "lead_id": 1}
    assert [e["subject"] for e in mod.sent_emails] == ["New lead: Apps"]


def test_screening_is_logged_without_visitor_details(load_grace, caplog):
    mod, client = load_grace()
    with caplog.at_level("INFO", logger="eolkits_grace"):
        client.post("/api/v1/lead", data=SPAM)
    assert "LEAD 1 stored as spam (link to a known spam host (telegra.ph)); owner not alerted" in (
        caplog.text
    )
    assert SPAM["email"] not in caplog.text and "JACKPOT" not in caplog.text


def test_retention_does_not_count_spam_as_never_alerted(load_grace, caplog):
    mod, client = load_grace(EOLKITS_LEAD_RETENTION_DAYS="30")
    for form in (SPAM, SPAM, REAL):
        client.post("/api/v1/lead", data=form)
    with mod.store.connect() as conn:
        conn.execute(
            "UPDATE leads SET ts = ?, notified = 0",
            ((datetime.now(UTC) - timedelta(days=45)).isoformat(),),
        )
    with caplog.at_level("INFO", logger="eolkits_grace"):
        assert mod.purge_expired_leads() == 3
    assert "1 purged lead(s) had never been alerted to the owner" in caplog.text
