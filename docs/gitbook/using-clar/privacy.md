# Privacy & De-identification

CLAR is designed with patient privacy as a first principle.

## What happens to your document

1. **Upload** — your file is transmitted over HTTPS to the CLAR backend.
2. **Text extraction** — text is extracted from your PDF or image.
3. **De-identification** — before any analysis, a de-identification step removes personal details: names, dates of birth, addresses, phone numbers, National ID numbers, and other identifiers recognised by standard medical privacy frameworks.
4. **Analysis** — only the de-identified text is sent for analysis.
5. **Deletion** — your original document is not stored. It exists in memory only for the duration of the request.

## What CLAR does not store

- Your original document
- Your raw report text
- Any personal identifiers extracted during de-identification

## What CLAR does store (per session)

- The structured findings returned from analysis, held in memory for the duration of your browser session
- A report ID used to anchor chat responses to your specific report

## Authentication

CLAR uses [Clerk](https://clerk.com) for authentication. CLAR does not store passwords. Your identity is managed entirely by Clerk's infrastructure.

## A note on LLM providers

CLAR uses a third-party large language model for analysis. The de-identified text of your report is sent to this provider as part of the analysis request. The provider's data processing terms apply to this data. CLAR does not share personally identifiable information with any LLM provider.

---

CLAR is not a HIPAA-covered entity. If you have concerns about sharing your medical data, please consult the privacy disclosures of each service provider listed above before uploading.
