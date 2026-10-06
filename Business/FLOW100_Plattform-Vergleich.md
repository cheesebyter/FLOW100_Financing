# FLOW100 – Plattformen für Integrations-Apps (Stand 11.09.2026)

Fit = Einschätzung für Andy (.NET/REST, CH/DACH, 8 h/Woche), Skala 1–5.

| Plattform | Markt | Grösse / Nachfrage | Gebühr | Einstiegshürde | Skill-Fit | Fit |
|---|---|---|---|---|---|---|
| bexio | CH | 100'000+ KMU, 1'000+ Treuhandpartner, 100+ Apps | nicht öffentlich | Listing ab 10 Kunden / 20 aktiven Usern, App in 2 Sprachen | REST + OpenID Connect | 5 |
| Lexware Office | DE | 450'000+ Kunden, ca. 1 von 5 nutzt Integrationen | nicht öffentlich | Integrationspartner ab 1 erfolgreichem API-Projekt | REST | 4.5 |
| Microsoft 365 (Outlook/Teams) | global | sehr gross, Einkauf oft über IT | 3 % bei Verkauf über Microsoft Marketplace | Entra ID + SaaS Fulfillment API | .NET/Azure ideal | 4 |
| Shopify | global/DACH | sehr gross, stark umkämpft | 0 % bis USD 1 Mio., USD 19 einmalig | Review, Billing API Pflicht | Backend frei wählbar | 3.5 |
| Atlassian (Jira/Confluence) | global | kaufkräftige Tech-Teams, umkämpft | Forge: 0 % bis USD 1 Mio. (lifetime), danach 17 %; Connect 25 % | Forge läuft auf JavaScript/Node | mittel | 3 |
| DATEV-Marktplatz | DE | Steuerberater-Ökosystem | keine Gebühr genannt | Schnittstellen-Partner ab 25 Kunden | mittel | 3 (später) |
| Xero | global (EN) | gross in AU/NZ/UK | API-Abo: gratis bis 5 Verbindungen, AUD 35 bis 50, AUD 245 bis 1'000 | Kosten wachsen mit Kundenzahl | REST | 2.5 |
| monday.com | global | mittel | 0 % bis USD 200k, danach 15 % | JS-SDK | mittel | 2.5 |
| Abacus | CH | Mittelstand, partnergetrieben | nicht öffentlich | Vertrieb stark über Abacus-Partner | REST | 2.5 |
| WooCommerce | global | sehr gross | 30 % an Woo (70 % an dich) | PHP/WordPress-Plugin | schwach | 2.5 |
| Shopware | DE | DACH-Mittelstand | nicht öffentlich | PHP/Symfony-Plugin | schwach | 2 |
| HubSpot, Pipedrive, Salesforce, Zoho | global | gross | – | ausgeschlossen bis Arbeitsvertrag geklärt (CRM) | – | – |
| Zapier, Make, n8n | global | – | – | kein Verkaufskanal, nur Zusatz-Sichtbarkeit | – | – |

## Empfehlung: ein Kern, mehrere Adapter

1. **bexio (CH) zuerst:** Heimvorteil, DE/FR, weniger Konkurrenz. Hier werden die ersten 10 Kunden gewonnen.
2. **Lexware Office (DE) als zweiter Adapter:** Rund 4,5× so viele Kunden, derselbe Kern-Workflow.
3. **Outlook-Add-in als Eingangskanal:** Beleg aus der E-Mail per Klick an bexio oder Lexware schicken.
4. **DATEV später:** Erst ab 25 Kunden möglich, dann als Ausbau für Steuerberater in DE.

Offen im Desk-Check:

- Gebühren und Bedingungen bei bexio und Lexware direkt beim Partner-Team anfragen.
- Bei Lexware prüfen, ob eine Multi-Kunden-App die Partner-API (OAuth) statt der Public API braucht.

## Quellen
- bexio Marketplace Partner: https://www.bexio.com/en-CH/marketplace/become-a-marketplace-partner
- Lexware Office Integrationspartner: https://www.lexware.de/partner/modelle/integrationspartner/
- Microsoft Marketplace Transact: https://learn.microsoft.com/en-us/partner-center/marketplace-offers/marketplace-commercial-transaction-capabilities-and-considerations
- Shopify Revenue Share: https://shopify.dev/docs/apps/launch/distribution/revenue-share
- Atlassian Revenue Share 2026: https://www.atlassian.com/blog/development/updates-to-marketplace-revenue-share-2026
- DATEV FAQ Softwarehersteller: https://www.datev.de/web/de/berufsgruppenuebergreifend/ueber-datev/portfolio/oekosystem/partnering/datev-marktplatz/faq-fuer-softwarehersteller
- Xero Developer Pricing: https://developer.xero.com/pricing
- monday.com Billing: https://developer.monday.com/apps/docs/subscriptions-payments-and-billing
- Abacus Marketplace: https://www.abacus.ch/abacus-marketplace/produkte
- Woo Marketplace: https://developer.woocommerce.com/docs/woo-marketplace/getting-started/
- Lexware Office API vs. Partner API: https://bome.net/lexware-office-api-vs-lexware-partner-api-wo-liegt-der-unterschied/
