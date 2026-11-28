# Mercatura — International Data Standards


## 1. Purpose

The Mercatura platform is designed to operate across multiple languages, currencies, time zones and regional conventions. Therefore, data platform will integrate these differences without destroying the original business meaning of operational records.

The core governing principle being enforced is:

**Preserve local source truth, standardize explicitly, and derive enterprise representations without losing provenance.**

This document establishes international data handling policies. It does not require the operational source data estate simulator to implement additional regional business processes.

## 2. International reference standards

Mercatura will adopt established international standards wherever applicable instead of inventing proprietary representations.

| Concept | Standard or convention | Example |
|---|---|---|
| Country | ISO 3166-1 alpha-2 | GB, JP, CN |
| Currency | ISO 4217 | GBP, JPY, CNY |
| Language | ISO 639 | en, ja, zh |
| Language and regional context | BCP 47 | en-GB, ja-JP, zh-CN |
| Character encoding | UTF-8 | Multilingual Unicode text |
| Unicode normalization | Unicode Standard Annex #15 | NFC |
| Date representation | ISO 8601 | 2026-06-15 |
| Timestamp interchange | ISO 8601 with offset where applicable | 2026-06-15T09:00:00+01:00 |
| Time zone | IANA Time Zone Database | Europe/London |
| Telephone numbers | ITU-T E.164 where applicable | +447123456789 |
| Measurement units | SI and controlled unit codes | kg, m, L |
| Geographic coordinates | WGS 84 where applicable | Latitude and longitude |
| Regional formatting | Unicode CLDR | Locale-specific numbers and dates |

Market, country, language, locale, currency and time zone are explicitly separate concepts. They will not be collected together and treated as interchangeable identifiers.

For example, a commercial market may contain multiple languages, currencies or time zones. To authentically preserve the market information, naturally all its distinct regional attributes will be faithfully preserved and managed according to downstream data product requirements.

## 3. Layer responsibilities

| Concern | Landing and Bronze | Silver | Gold and serving |
|---|---|---|---|
| Language | Preserve native text | Derive normalized or translated attributes | Localized reporting labels |
| Currency | Preserve original amount and currency | Validate denomination and enrich with FX | Apply declared reporting-currency policy |
| Time | Preserve original date and timestamp semantics | Derive UTC and business-local representations | Apply reporting calendars |
| Units | Preserve original quantity and unit | Convert compatible units | Aggregate standardized measures |
| Geography | Preserve source address and location | Resolve standardized geographic identifiers | Geographic reporting hierarchies |
| Tax | Preserve available source amounts and classifications | Conform tax semantics where supported | Explicit gross, net and tax measures |
| Privacy | Restrict access to source-sensitive fields | Classify, minimize and pseudonymize where appropriate | Expose authorized analytical attributes |

Standardization will be reversible through retained source values and lineage.

## 4. Multilingual text and Unicode

### 4.1 Encoding

The current source exporter produces UTF-8 JSONL using:

```python
json.dumps(
    document,
    ensure_ascii=False,
    sort_keys=True,
    separators=(",", ":"),
)
```

Unicode characters are therefore written directly into source files.

Both escaped JSON Unicode sequences and literal UTF-8 characters are valid representations. The platform preserves the decoded character content regardless of representation.

Invalid source encoding will not be silently corrected by replacing characters.

### 4.2 Normalization

Visually identical strings may have different Unicode representations.

For example:

- `é` represented by U+00E9;
- `e` followed by the combining acute accent U+0301.

These representations can behave differently during equality comparisons, hashing and deduplication.

NFC is the default candidate for derived normalized text:

```python
import unicodedata

normalized_value = unicodedata.normalize("NFC", source_value)
```

Normalization policies shall be defined at field level rather than indiscriminately applied to every string column.

| Operation | Default policy |
|---|---|
| NFC normalization | Permitted for derived comparison attributes |
| NFKC normalization | Restricted to approved matching use cases |
| Accent removal | Optional search enrichment only |
| Case folding | Field-specific matching enrichment |
| Whitespace trimming | Apply according to the source contract |
| Transliteration | Optional derived attribute |
| Translation | Optional business-facing enrichment |
| Source identifier normalization | Prohibited unless explicitly required by its contract |

Compatibility normalization, case folding and accent removal can collapse meaningful distinctions. Their output must not automatically become a unique business identifier.

### 4.3 Language and translation

Translation converts meaning between languages. Transliteration converts text between writing systems. Normalization standardizes character representation.

I am treating these individually as seperate processes for different operations.

| Source value | Possible derived value | Operation |
|---|---|---|
| 東京 | Tokyo | Transliteration or conventional place name |
| 折りたたみ式デスク | Folding desk | Translation |
| 王小明 | Wang Xiaoming | Transliteration |
| München | Munich | Conventional English place name |
| Decomposed accented character | Composed accented character | Unicode normalization |

Personal names, addresses and legal entity names will not be automatically replaced with translated values to preserve the authenticity of the source data.

Product descriptions and reporting labels may be translated where there is a genuine consumer requirement, such as display on a dashboard used by consumers that demand English language.

A future multilingual product model may contain:

| Field | Example |
|---|---|
| `product_id` | PRD-000423 |
| `product_name_native` | 折りたたみ式デスク |
| `language_tag` | ja-JP |
| `product_name_en` | Folding desk |
| `translation_method` | MACHINE |
| `translation_version` | 1 |
| `translation_review_status` | UNREVIEWED |

Translation output is being treated as data enrichment rather than source truth.

Machine-generated translations should retain their method, model or service version, and review status where relevant.

### 4.4 Search, collation and entity matching

Different languages have different sorting and comparison conventions.

The platform must distinguish:

- exact identifier equality
- Unicode-normalized equality
- locale-aware comparison
- fuzzy matching
- semantic similarity

A normalized name match alone is likely insufficient evidence that two customers represent the same person.

Raw content hashes and normalized content hashes must also remain conceptually distinct.

## 5. Currency and monetary representation

### 5.1 Monetary values

A monetary value consists of an amount and its denomination.

| Field | Example |
|---|---|
| `amount_local` | 700.00 |
| `currency_code` | CNY |

The original amount and currency remain unchanged when foreign exchange rates move.

Cross-currency aggregation is being prohibited until amounts have been converted using an appropriate reporting policy.

### 5.2 Currency precision

Currencies do not universally use two decimal places. Different currencies may have different decimal place conventions.

| Currency | Typical ISO 4217 minor-unit digits |
|---|---:|
| GBP | 2 |
| EUR | 2 |
| USD | 2 |
| CNY | 2 |
| NOK | 2 |
| RUB | 2 |
| PLN | 2 |
| JPY | 0 |
| KRW | 0 |

Minor unit conventions do not necessarily determine the internal precision required for intermediate calculations, unit prices, exchange rates or accounting allocations.

The platform must distinguish:

- source precision
- calculation precision
- settlement precision
- presentation precision
- rounding policy

Candidate Databricks storage types:

| Measure | Candidate type |
|---|---|
| Local monetary amount | DECIMAL(20, 4) |
| Exchange rate | DECIMAL(28, 12) |
| Intermediate converted amount | Explicit high-precision DECIMAL |
| Final GBP reporting amount | DECIMAL(20, 2), where appropriate |

These are some initial proposed types. Actual precision and scale qill be selected from after source profiling, maximum supported values and Spark decimal-arithmetic behaviour.

### 5.3 Rounding

Rounding must occur at an explicitly defined calculation boundary.

For example:

- individual transaction
- financial document
- settlement
- reporting period

Rounding individual transactions before aggregation may produce a different result from rounding the final aggregate. The applicable financial policy must determine which is correct. This will be investigated, determined, and documented.

## 6. Foreign exchange architecture

### 6.1 Reference-data model

Foreign exchange rates are external, time-dependent reference data.

They are not owned by OMS, PAYMENTS or the operational simulator.

A candidate canonical FX dataset is:

| Field | Meaning |
|---|---|
| `fx_rate_id` | Unique rate-record identifier |
| `from_currency` | Original currency |
| `to_currency` | Target currency |
| `rate_date` | Applicable business date |
| `rate_type` | Conversion-policy category |
| `exchange_rate` | Target currency units per one source currency unit |
| `provider` | Rate provider |
| `published_at` | Provider publication timestamp, if available |
| `ingested_at` | Platform acquisition timestamp |
| `rate_version` | Rate revision identifier |
| `rate_origin` | Observed, derived or simulated |
| `base_currency` | Provider base currency, where applicable |
| `quality_status` | Rate validation outcome |

The conversion convention is:

`amount_reporting = amount_local × exchange_rate`

For example, a CNY-to-GBP exchange rate represents GBP received per one CNY.

Rate direction must not be inferred from an ambiguous currency pair name.

### 6.2 FX rate types

| Rate type | Intended application |
|---|---|
| `DAILY_SPOT` | Transaction-date management reporting |
| `MONTHLY_AVERAGE` | Approved periodic financial analysis |
| `PERIOD_END` | Appropriate period-end balance reporting |
| `BUDGET` | Planning and performance comparison |
| `CONSTANT_CURRENCY` | Comparison that isolates exchange-rate effects |
| `SETTLEMENT` | Actual financial settlement where supplied |

Financial-accounting applications require an approved accounting policy. These categories alone do not establish compliance with IAS 21 or other reporting requirements.

### 6.3 Currency depreciation example

Assuming a Chinese transaction of CNY 700.

The following exchange rates are for illustrative purposes, and are not observed market rates.

| Scenario | Local amount | CNY-to-GBP rate | GBP equivalent |
|---|---:|---:|---:|
| Original transaction | CNY 700 | 0.1100 | £77.00 |
| Yuan depreciation | CNY 700 | 0.1000 | £70.00 |
| Yuan appreciation | CNY 700 | 0.1200 | £84.00 |

The local transaction remains CNY 700 in every scenario.

The GBP equivalent changes because of the conversion rate.

Historical transaction date reporting should not automatically change whenever a new daily exchange rate arrives.

Current rate valuation and constant currency analysis must be exposed as explicitly different analytical measures.

### 6.4 Triangulation

A provider may publish exchange rates against a common base currency instead of every possible currency pair.

For example:

`EUR → CNY`

`EUR → GBP`

A CNY-to-GBP rate can be derived as:

`CNY_TO_GBP = EUR_TO_GBP / EUR_TO_CNY`

Both component rates must originate from a compatible observation date, provider and rate type.

The derived rate must retain lineage to its component rates.

### 6.5 Missing exchange rates

Rates may be unavailable because of weekends, holidays, publication delays, provider coverage or restrictions on particular currencies.

| Scenario | Required treatment |
|---|---|
| Weekend or non-publication day | Previous approved observation within configured staleness limits |
| Delayed publication | Mark pending and retry or defer publication |
| Unsupported currency | Use an explicitly approved alternative provider or report missing coverage |
| Conflicting providers | Apply documented provider precedence |
| Zero or negative exchange rate | Reject as invalid |
| Excessively stale exchange rate | Block affected conversion or flag incomplete reporting |
| GBP-to-GBP conversion | Identity rate of 1 |
| Future simulated transaction | Use explicitly synthetic FX or defer observed-rate valuation |
| Revised historical rate | Version the correction and apply controlled reprocessing |


### 6.6 Observed versus simulated exchange rates

The Mercatura activity window extends through December 2026 and includes generated future operational consequences.

Historical providers cannot supply observed exchange rates for future dates.

The platform must distinguish:

- historical observed rates
- rates derived from observed rates
- synthetic scenario rates
- forecast or budget rates

Synthetic values must never be represented as historical market observations.

### 6.7 Reproducibility

Converted financial values should retain sufficient metadata to reproduce the calculation.

Required concepts include:

- original amount and currency
- reporting amount and currency
- applied rate identifier
- applicable rate date
- rate type and provider
- conversion-policy version
- rounding policy

Historical restatement must be deliberate rather than an accidental consequence of overwriting the reference rate table.

## 7. Financial interpretation and constant-currency reporting

Multinational performance can change because of commercial activity, exchange-rate movements, or both.

| Measure | Meaning |
|---|---|
| Local revenue | Revenue in original transaction currency |
| Reported revenue | Revenue converted using the declared reporting policy |
| Constant-currency revenue | Revenue converted using a common comparison-period rate |
| FX impact | Difference attributable to the selected currency-conversion basis |

Constant-currency reporting will allow analysts to distinguish underlying commercial performance from translation effects.

For example, Chinese local-currency revenue may increase while reported GBP revenue decreases because CNY has depreciated sufficiently against GBP.

### Returns and refunds

A refund remains denominated in the original transaction currency under the current source model.

Different analytical purposes may use:

- the original sale conversion rate;
- the refund-date conversion rate;
- the actual settlement rate.

These policies must be identified separately.

A difference between sale-date and refund-date GBP equivalents must not automatically be classified as a refund arithmetic error.

## 8. Time zones and temporal conformance

### 8.1 Temporal concepts

| Concept | Meaning |
|---|---|
| Business date | Local calendar date relevant to the operational event |
| Local event timestamp | Event time in the originating location |
| UTC event timestamp | Globally comparable event instant |
| Source time zone | IANA zone identifying the applicable local time rules |
| Source offset | UTC offset supplied or resolved for the event |
| Effective time | Time at which a business state becomes valid |
| Publication time | Time when information becomes available |
| Extraction time | Time when data is acquired from the source |
| Ingestion time | Time when the platform processes the delivery |

A business date must not be converted into a fabricated midnight timestamp simply to impose a common data type.

### 8.2 Databricks temporal types

| Type | Intended interpretation |
|---|---|
| `DATE` | Calendar date without a time-of-day component |
| `TIMESTAMP` | An instant interpreted and displayed according to session timezone semantics |
| `TIMESTAMP_NTZ` | Local date and time without timezone interpretation |

Databricks does not preserve the original IANA zone identifier by storing an instant as a `TIMESTAMP`.

Where required, the originating timezone and local business date must be retained separately.

Pipeline sessions should use explicitly configured timezone settings, with UTC as the default candidate for instant-based processing.

### 8.3 Daylight saving time

Local timestamps can be ambiguous or nonexistent during daylight-saving transitions.

| Situation | Example in Europe/London |
|---|---|
| Ambiguous local time | 2026-10-25 01:30 occurs twice |
| Nonexistent local time | 2026-03-29 01:30 is skipped |

If a source supplies a timestamp without an offset during an ambiguous interval, the platform must not silently choose an interpretation without a documented resolution policy.

Depending on the source contract, records may require additional context, quarantine or explicitly flagged resolution.

### 8.4 Market timezone limitations

A market-level timezone is a simulation simplification.

Countries such as the United States and Russia contain multiple time zones.

Future production oriented contracts should prefer store, warehouse or event origin timezone information over a market wide default.

Market defaults may only be used when explicitly authorized by the relevant source contract.

### 8.5 Reporting dates

The same UTC instant may belong to different local business dates.

For example:

| Representation | Value |
|---|---|
| UTC instant | 2026-06-15 23:30 UTC |
| Tokyo local time | 2026-06-16 08:30 |
| Tokyo business date | 2026-06-16 |
| UTC calendar date | 2026-06-15 |

Local sales reporting should use the relevant local business date. Group reporting must declare its calendar and reporting cutoffs explicitly.

## 9. Regional calendars and localization

### 9.1 Formatting differences

| Concept | Example representations | Policy |
|---|---|---|
| Decimal number | 1,234.56; 1.234,56 | Parse using explicit source-format rules |
| Date | 15/06/2026; 06/15/2026 | Require a declared date pattern |
| Currency symbol | £, $, ¥ | Resolve denomination from explicit currency context |
| Negative amount | -100; (100) | Parse according to source format |
| Telephone | Domestic and international formats | Preserve source; derive normalized value |
| Postal code | Numeric or alphanumeric | Store as string |
| Identifier | 000123 | Preserve leading zeros |
| Personal name | Different component ordering | Avoid universal Western naming assumptions |

Locale determines representation conventions. It does not independently establish currency, nationality or identity.

### 9.2 Calendar reference data

A conventional enterprise date dimension should be supplemented by market specific calendar information.

A candidate calendar model contains:

| Field | Meaning |
|---|---|
| `calendar_date` | Calendar date |
| `market_code` | Applicable market |
| `calendar_type` | Retail, public holiday, banking or fiscal |
| `is_weekend` | Applicable weekend indicator |
| `is_public_holiday` | Holiday indicator |
| `holiday_name_native` | Native holiday label |
| `holiday_name_en` | Optional standardized label |
| `is_business_day` | Business-day indicator for this calendar |
| `fiscal_year` | Applicable fiscal year |
| `fiscal_period` | Applicable fiscal reporting period |
| `calendar_version` | Reference-data version |

Retail trading calendars, financial market calendars and supplier working calendars must not automatically be treated as identical.

## 10. Units of measure

Operational quantities should have an explicit unit where multiple unit interpretations are possible.

| Source measure | Standardized measure |
|---|---|
| 5000 g | 5 kg |
| 250 cm | 2.5 m |
| 750 ml | 0.75 L |

Conversions must preserve dimensional compatibility.

Mass cannot be converted into volume without additional information such as density.

Packaging conversions are frequently product-specific:

`1 case = 12 individual units`

This must not be treated as a universal conversion factor.

A future unit-conversion reference may contain:

| Field | Purpose |
|---|---|
| `from_unit` | Source measurement unit |
| `to_unit` | Target measurement unit |
| `conversion_factor` | Applicable conversion |
| `conversion_offset` | Offset where required |
| `product_id` | Product-specific conversion scope |
| `effective_from` | Conversion validity start |
| `effective_to` | Conversion validity end |

The current WMS ledger uses operational product-unit quantities. Richer packaging and measurement semantics are deferred until required.

## 11. Tax, geography and regional business rules

| Concern | Required treatment |
|---|---|
| Tax-inclusive versus tax-exclusive prices | Explicit price classification |
| VAT and sales tax | Retain applicable jurisdiction and tax semantics |
| Historical tax-rate changes | Effective-dated reference data |
| Product tax classifications | Product and jurisdiction-specific reference data |
| Addresses | Preserve native address lines and regional components |
| Administrative geography | Use standardized identifiers and versioned mappings |
| Postal codes | Country-specific validation rather than universal regex |
| Telephone numbers | Country-aware parsing with preservation of original value |
| Product availability | Distinguish regulatory eligibility from physical stock |
| International procurement | Distinguish product cost from duties, freight and landed cost |

The Phase 1 source estate does not contain sufficient data to calculate comprehensive taxation, landed costs or statutory financial statements.

These capabilities must not be implied by downstream reporting.

## 12. Privacy and regional data governance

International customer-level processing may be subject to regional legal requirements, contractual restrictions and organisational policies.

The current centralized UK development environment contains synthetic data and is not evidence that the equivalent production architecture would be appropriate for real multinational customer data.

Future production-oriented controls should support:

| Control | Purpose |
|---|---|
| Data classification | Identify personal and sensitive attributes |
| Regional processing policy | Determine permitted processing locations |
| Cross-border transfer policy | Control authorized data movement |
| Column masking | Restrict access to sensitive attributes |
| Row-level filtering | Restrict records by authorized scope |
| Pseudonymization | Reduce unnecessary exposure of direct identifiers |
| Retention policy | Enforce permitted storage duration |
| Deletion workflows | Support applicable deletion obligations |
| Access auditing | Establish accountability |

Exact legal and regulatory requirements will be assessed separately for the actual operating jurisdictions and processing activities.

## 13. Reference-data requirements

International conventions should be represented through governed reference datasets rather than permanently embedded in transformation logic.

| Candidate dataset | Responsibility | Priority |
|---|---|---|
| `ref_market` | Commercial market definitions | High |
| `ref_country` | Country identifiers and geography | High |
| `ref_currency` | Currency codes and minor-unit conventions | High |
| `ref_fx_rate` | Dated exchange rates and rate provenance | High |
| `ref_locale` | Language and regional formatting policies | High |
| `ref_timezone` | Approved timezone identifiers and mappings | High |
| `ref_market_calendar` | Market-specific reporting and trading calendars | Medium |
| `ref_unit_of_measure` | Controlled measurement-unit definitions | Medium |
| `ref_unit_conversion` | General and product-specific conversions | Medium |
| `ref_geography` | Geographic hierarchy and conformance | Medium |
| `ref_tax_rule` | Effective-dated taxation rules | Deferred |
| `ref_translation` | Versioned multilingual enrichment | Deferred |

Reference data requires its own source contracts, freshness expectations, provenance, versioning and quality checks.

## 14. Metadata-driven ingestion and data quality

Internationalization policies will eventually be represented via versioned metadata rather than hardcoded assumptions distributed across a multitude of ingestion notebooks.

The metadata-driven framework will distinguish ingestion settings from downstream conformance and analytical policies.

| Metadata category | Candidate attributes | Responsibility |
|---|---|---|
| Encoding | `encoding`, `invalid_byte_policy` | MDDI |
| Source format | `date_format`, `decimal_separator`, `grouping_separator` | MDDI |
| Locale | `default_locale`, `locale_column` | MDDI and conformance |
| Temporal | `source_timezone`, `timezone_column`, `timestamp_semantics` | MDDI and conformance |
| Monetary | `currency_column`, `precision`, `scale` | Source contract and MDDQ |
| Normalization | `unicode_form`, `target_field` | Silver conformance |
| Translation | `target_language`, `translation_policy` | Enrichment |
| FX | `rate_type`, `provider_policy`, `maximum_staleness` | Financial conformance |
| Measurement | `unit_column`, `canonical_unit` | Silver conformance |
| Governance | `classification`, `residency_policy`, `retention_policy` | Governance and execution |

An example illustrative metadata configuration for OMS orders is:

```yaml
dataset: oms.orders
contract_version: 1

ingestion:
  format: jsonl
  encoding: utf-8
  invalid_byte_policy: reject_and_quarantine

temporal:
  fields:
    order_date:
      semantic_type: business_date
      format: "%Y-%m-%d"
    cancelled_at:
      semantic_type: instant

monetary:
  currency_column: currency
  amount_columns:
    - order_total
  preserve_original: true

conformance:
  preserve_source_values: true
  market_column: market_code

quality:
  rule_sets:
    - general_integrity
    - oms_integrity
    - monetary_integrity
```

A separate reporting policy may define:

```yaml
policy_id: management_revenue_gbp
policy_version: 1

currency_conversion:
  target_currency: GBP
  source_currency_column: currency
  amount_column: order_total
  rate_date_column: order_date
  rate_type: DAILY_SPOT

  missing_rate_policy:
    strategy: previous_approved_rate
    max_calendar_days: 4
    on_exhaustion: block_affected_publication

  preserve_rate_lineage: true
  permit_synthetic_rates: false
```

These configurations are just examples rather than implemented interfaces, but they are a start, and match other general metadata driven framework implementations.

The four-day fallback limit is a candidate policy requiring validation against provider publication patterns and business requirements.

Ingestion is not to become responsible for every international business transformation. MDDI acquires and parses data, MDDQ validates it, and conformance and reporting policies determine appropriate derived representations.

## 15. Acceptance criteria

The following scenarios should form part of future international-data integration tests.

| Test ID | Scenario | Expected result |
|---|---|---|
| INT-001 | Chinese, Japanese, Korean and Cyrillic text passes through ingestion | Original Unicode content retained |
| INT-002 | Composed and decomposed accented text is normalized | Derived NFC values compare correctly |
| INT-003 | Native personal name is transliterated | Original name remains unchanged |
| INT-004 | Invalid UTF-8 source payload | Rejected or quarantined according to contract |
| INT-005 | Postal code contains leading zeros | Leading zeros retained |
| INT-006 | Ambiguous locale-specific date | No silent date interpretation |
| INT-007 | JPY transaction | Currency-aware precision and presentation |
| INT-008 | Mixed-currency transaction aggregation | Prevented until appropriate conversion |
| INT-009 | CNY exchange rate depreciates | Local value unchanged; relevant reporting valuation changes |
| INT-010 | FX rate is missing | Explicit missing-rate policy applied |
| INT-011 | FX rate is stale | Affected conversion rejected or flagged |
| INT-012 | RUB absent from selected provider | Approved fallback or explicit incomplete coverage |
| INT-013 | Future transaction has no observed rate | No fabricated observed FX value |
| INT-014 | Historical FX rate is revised | Versioned correction and controlled reprocessing |
| INT-015 | Currency pair is triangulated | Derived rate retains component lineage |
| INT-016 | Sale and refund use different FX dates | Difference is attributable to declared conversion policy |
| INT-017 | Ambiguous DST timestamp | Explicit resolution or quarantine |
| INT-018 | Nonexistent DST timestamp | No silent invalid-time acceptance |
| INT-019 | UTC event crosses local midnight | Correct local business date |
| INT-020 | Date-only event is ingested | No fabricated time-of-day precision |
| INT-021 | Two compatible measurement units are aggregated | Explicit conversion applied |
| INT-022 | Incompatible units are aggregated | Invalid calculation prevented |
| INT-023 | Product-specific packaging conversion changes | Correct effective-dated conversion selected |
| INT-024 | Regional public holiday affects business-day calculation | Applicable calendar used |
| INT-025 | Sensitive multilingual field is restricted | Unauthorized consumers cannot access it |
| INT-026 | Machine translation is updated | Native text and prior enrichment provenance retained |
| INT-027 | International metadata configuration is invalid | Rejected before pipeline execution |


## 16. Implementation priorities

| Stage | International-data capability |
|---|---|
| Source data estate generation — Complete | Multilingual source generation, UTF-8 export, explicit currencies, Decimal values, market timezone configuration |
| Source contracts | Encoding, locale, temporal semantics, precision and nullability declarations |
| Landing and Bronze | Source preserving ingestion and encoding validation |
| Silver foundations | Canonical codes, Unicode normalization and temporal conformance |
| Reference-data ingestion | Currency metadata, FX rates and market calendars |
| Gold modelling | GBP reporting, local currency reporting and constant currency measures |
| MDDI and MDDQ | Configurable international parsing, validation and policy enforcement |
| Governance expansion | Regional access, privacy and retention controls |
| Optional enrichment | Translation, advanced entity matching and geographic conformance, Global map dashboard |

## 17. Standards and technical references

- Unicode Standard Annex #15: https://www.unicode.org/reports/tr15/
- Unicode CLDR: https://cldr.unicode.org/
- IANA Time Zone Database: https://www.iana.org/time-zones
- ISO currency codes: https://www.iso.org/iso-4217-currency-codes.html
- ECB exchange-rate reference data: https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html
- IAS 21: The Effects of Changes in Foreign Exchange Rates.
- Azure Databricks timezone conversion: https://learn.microsoft.com/en-us/azure/databricks/sql/language-manual/functions/convert_timezone

