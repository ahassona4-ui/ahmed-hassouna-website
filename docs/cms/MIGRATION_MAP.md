# Phase 2 — Existing Content Migration Map

## Governing Principle

الترحيل المستقبلي يجب أن يكون **lossless**: يُنقل النص الحالي كما هو أولًا، ثم تخضع أي إعادة صياغة لمراجعة مستقلة. لا تُخترع تواريخ أو صور أو نتائج أو Evidence References.

## Projects

| Project ID | Current File | Approved Slug | Arabic Title | English Title | Organization | Period | Order | Featured | Migration Status |
|---|---|---|---|---|---|---:|---:|---|---|
| AH-PRJ-001 | `projects/production-capacity.html` | `production-capacity` | تحسين الطاقة الإنتاجية وكفاءة الموارد البشرية | Production Capacity & Workforce Productivity | Expert Engineering Industries | 2025 | 1 | true | Ready for structured extraction |
| AH-PRJ-002 | `projects/warehouse-governance.html` | `warehouse-governance` | حوكمة المخازن وضبط استهلاك الخامات | Warehouse Governance & Material Yield System | Expert Engineering Industries | 2025 | 2 | true | Ready for structured extraction |
| AH-PRJ-003 | `projects/quality-prevention.html` | `quality-prevention` | هندسة الجودة والوقاية | Preventive Quality Management System | Expert Engineering Industries | 2024–2025 | 3 | true | Ready for structured extraction |
| AH-PRJ-004 | `projects/azora-transformation.html` | `azora-transformation` | AZORA — تحليل الأعمال وحوكمة التحول التشغيلي | AZORA — Operational Transformation & Governance | AZORA Agricultural Operations Platform | 2025–2026 | 4 | true | Ready for structured extraction |
| AH-PRJ-005 | `projects/operational-knowledge.html` | `operational-knowledge` | توحيد التشغيل واستدامة المعرفة | Operational Knowledge System | Sinastra / Asia Egypt | 2016–2025 | 5 | true | Ready for structured extraction |

### Current Project Media Mapping

| Project ID | Existing Asset |
|---|---|
| AH-PRJ-001 | `assets/projects/production.svg` |
| AH-PRJ-002 | `assets/projects/warehouse.svg` |
| AH-PRJ-003 | `assets/projects/quality.svg` |
| AH-PRJ-004 | `assets/projects/azora.svg` |
| AH-PRJ-005 | `assets/projects/knowledge.svg` |

### Project Migration Controls

- `project_id`, slug, titles, organization, period and current visual asset are preserved.
- Current displayed claims are migrated as `baseline_approved`.
- Quantitative and formal-status claims must receive internal `evidence_refs` before runtime migration is accepted.
- Previous/Next links are not migrated as fields; they are recomputed from published order.
- Current URLs remain unchanged.

## Articles

| Article ID | Current File | Approved Slug | Arabic Title | English Title | Order | Published Date | Migration Status |
|---|---|---|---|---|---:|---|---|
| AH-ART-001 | `articles/business-logic-before-tools.html` | `business-logic-before-tools` | لماذا يسبق منطق العمل الأداة؟ | Why Business Logic Must Come Before the Tool | 1 | Not evidenced in RC4.4 | Ready; date pending |
| AH-ART-002 | `articles/erp-ownership.html` | `erp-ownership` | لماذا تفشل مشروعات ERP عند غموض الملكية؟ | Why ERP Projects Fail When Ownership Is Unclear | 2 | Not evidenced in RC4.4 | Ready; date pending |
| AH-ART-003 | `articles/measuring-reality.html` | `measuring-reality` | لماذا أبدأ بقياس الواقع؟ | Why I Start by Measuring Reality | 3 | Not evidenced in RC4.4 | Ready; date pending |

### Article Migration Controls

- لا يُخترع `published_at`.
- المقالات الحالية بلا Cover image؛ تُهاجر بقيمة `cover: null`.
- ترتيب Knowledge Center الحالي يحفظ مؤقتًا بواسطة `order`.
- العناوين والفقرات الثنائية تُستخرج كما هي.
- روابط العودة والتنقل لا تُخزن داخل المحتوى.
- Current URLs remain unchanged.

## Source-to-Field Extraction Map

| Current HTML Source | Target Field |
|---|---|
| `.project-id` | `project_id` |
| `.project-title[data-ar/data-en]` | `title.ar/en` |
| `.project-alt-title[data-ar/data-en]` | secondary/title verification |
| `.project-submeta` | organization, period, category, status_label |
| `.built-capability p` | `built_capability.ar/en` |
| context section paragraph | `context.ar/en` |
| method cards 01/02/03 | diagnosis/design/stabilization |
| evidence cards | evidence_basis/documented_impact/claim_boundaries/transferable_value |
| article `h1[data-ar/data-en]` | `title.ar/en` |
| `.hero-copy[data-ar/data-en]` | `lead.ar/en` |
| article h2 + following paragraph(s) | `sections[]` |
| existing meta description | initial SEO description candidate, review required |

## Deferred Questions for Later Gate

1. اعتماد تواريخ نشر المقالات الحالية.
2. تحديد ما إذا كانت صور غلاف المقالات ستصبح إلزامية للمقالات الجديدة فقط.
3. ربط Evidence References الداخلية دون نشرها.
4. سياسة Redirect إذا تغير slug مستقبلًا.
5. الحد الأقصى النهائي لعدد صور Gallery.
