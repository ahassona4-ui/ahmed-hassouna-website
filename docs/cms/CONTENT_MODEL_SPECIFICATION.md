# AH Website CMS — Content Model Specification v1.0

## 1. Purpose

تهدف هذه المواصفة إلى فصل المحتوى عن التصميم لاحقًا دون تغيير التصميم المعتمد أو الحقيقة المهنية. وهي تحدد نموذجًا موحدًا للمشروعات والمقالات، وقواعد العربية والإنجليزية، ودورة الحالة، والوسائط، وSEO، والتنقل، وضبط الادعاءات.

هذه المواصفة **تصميم غير تشغيلي** في Phase 2. لا تنشئ صفحات ولا تغير URLs ولا تُزيل `.nojekyll`.

---

## 2. Canonical Identity

| Field | Canonical Value |
|---|---|
| English name | Ahmed Hassouna |
| Arabic name | أحمد حسونة |
| English role | Operations & Business Systems Consultant |
| Arabic role | مستشار نظم العمليات والأعمال |
| Default language | Arabic |
| Arabic direction | RTL |
| English direction | LTR |

لا يجوز لأي محرر محتوى تغيير هذه القيم من داخل سجل مشروع أو مقال. تُدار لاحقًا من ملف إعدادات موقع مركزي بعد اعتماد مرحلة مناسبة.

---

## 3. Common Content Envelope

كل سجل محتوى يجب أن يحتوي على:

| Field | Type | Rule |
|---|---|---|
| `schema_version` | string | ثابت في هذه المرحلة: `1.0` |
| `content_type` | enum | `project` أو `article` |
| `status` | enum | `draft`, `under_review`, `published`, `archived` |
| `slug` | string | أحرف إنجليزية صغيرة وأرقام وشرطات فقط |
| `order` | integer | عدد صحيح موجب؛ يستخدم للترتيب عند الحاجة |
| `created_at` | datetime/null | لا يُخترع تاريخ غير موثق |
| `updated_at` | datetime/null | يُحدّث عند تعديل المحتوى |
| `owner` | string | ثابت: `Ahmed Hassouna` |
| `languages` | array | يجب أن تحتوي `ar` و`en` قبل النشر |
| `translation_state` | enum | `incomplete`, `ready_for_review`, `approved` |
| `review` | object | بيانات مراجعة المحتوى والادعاءات |

### 3.1 Slug Rules

- النمط: `^[a-z0-9]+(?:-[a-z0-9]+)*$`.
- فريد داخل نوع المحتوى.
- لا يبدأ أو ينتهي بشرطة.
- لا يحتوي على العربية أو مسافات أو underscores.
- بعد أول نشر يصبح ثابتًا.
- أي تغيير لاحق يحتاج قرار Redirect مستقل في مرحلة تنفيذية لاحقة.
- Slugs الحالية محفوظة كما هي.

### 3.2 Ordering Rules

- ترتيب المشروعات في Selected Work يعتمد على `order` تصاعديًا.
- ترتيب المقالات في Knowledge Center يعتمد أساسًا على `published_at` تنازليًا، ثم `order`.
- لا يجوز تكرار `order` بين العناصر المنشورة داخل القائمة نفسها.
- `order` لا يُستخدم كدليل زمني أو مهني.

---

## 4. Status Workflow

### 4.1 Stored Values and Display Labels

| Stored Value | Display Label |
|---|---|
| `draft` | Draft |
| `under_review` | Under Review |
| `published` | Published |
| `archived` | Archived |

### 4.2 Allowed Transitions

- `draft` → `under_review`
- `under_review` → `draft`
- `under_review` → `published`
- `published` → `under_review` عند فتح مراجعة منضبطة
- `published` → `archived`
- `archived` → `under_review`

لا يسمح بالانتقال المباشر من `draft` إلى `published`.

### 4.3 Publication Gate

لا يصبح السجل `published` إلا إذا:

1. اكتملت الحقول الإلزامية.
2. اكتملت العربية والإنجليزية.
3. كانت `translation_state = approved`.
4. كانت جميع الادعاءات `approved` أو `baseline_approved`.
5. لا توجد روابط صور مفقودة.
6. اجتاز slug وقواعد الترتيب.
7. أُكملت بيانات SEO المطلوبة.
8. لم يتغير اسم قدرة أو مسمى مهني معتمد.
9. لم تُضف أرقام أو نتائج بلا Evidence Reference.
10. سُجلت موافقة المراجع.

### 4.4 Runtime Intent for Later Phases

- Draft وUnder Review: لا يظهران للعامة.
- Published: يظهر في الصفحة والفهرس المناسب.
- Archived: يُزال من القوائم، مع الحفاظ على الرابط السابق وسياسة `noindex` لاحقًا ما لم تصدر موافقة خلاف ذلك.

هذه قواعد تصميمية؛ التطبيق الفعلي مؤجل.

---

## 5. Bilingual Field Rules

### 5.1 Localized Text Shape

الحقول العامة المترجمة تخزن بالشكل:

```yaml
field:
  ar: "النص العربي"
  en: "English text"
```

### 5.2 Required Pairing

قبل النشر يجب أن تتوافر النسختان في:

- العنوان.
- الملخص.
- وصف القدرة المبنية.
- السياق.
- خطوات المنهجية.
- الأدلة والنتائج وحدود الادعاء.
- العناوين والنصوص داخل المقال.
- Alt text وCaption للصور ذات المعنى.
- SEO title وSEO description.

### 5.3 Translation Governance

- لا يُسمح بأن تكون الإنجليزية ترجمة تضيف ادعاءً غير موجود بالعربية أو العكس.
- الأرقام والوحدات والفترات الزمنية يجب أن تتطابق معنويًا.
- أسماء الشركات والعملاء تبقى بالصورة المعتمدة ولا تُترجم ترجمة حرة.
- أسماء القدرات لا تُعاد صياغتها دون اعتماد.
- اتجاه الصفحة يُستنتج من اللغة؛ لا يُدخل يدويًا في كل سجل.
- لا يعتمد Published على fallback آلي بين اللغتين.
- الترجمة الآلية، إن استُخدمت لاحقًا، تنتج Draft فقط ولا تعتبر Approved.

---

## 6. Project Content Model

### 6.1 Identity and Listing

| Field | Type | Required |
|---|---|---|
| `project_id` | string | Yes |
| `slug` | string | Yes |
| `status` | enum | Yes |
| `order` | integer | Yes |
| `featured` | boolean | Yes |
| `title.ar` / `title.en` | string | Yes |
| `organization` | string | Yes |
| `period` | string | Yes |
| `category.ar` / `category.en` | string | Yes |
| `status_label.ar` / `status_label.en` | string | Yes |

`project_id` must match `^AH-PRJ-[0-9]{3}$`, is unique, and never changes after assignment.

### 6.2 Narrative Structure

Required bilingual sections:

- `summary`
- `built_capability`
- `context`
- `method.diagnosis`
- `method.design`
- `method.stabilization`
- `evidence.evidence_basis`
- `evidence.documented_impact`
- `evidence.claim_boundaries`
- `evidence.transferable_value`

هذه البنية تحافظ على التسلسل الحالي: Diagnosis → Design → Stabilization.

### 6.3 Featured and Index Rules

- `published && featured` يظهر في Selected Work Carousel.
- `published` يظهر في Project Index.
- `draft`, `under_review`, `archived` لا تظهر في Carousel أو Index.
- الترتيب تصاعدي حسب `order`.
- لا يجوز أن يؤدي إلغاء `featured` إلى حذف صفحة المشروع نفسها.

### 6.4 Project Navigation

لا تُخزن روابط previous/next يدويًا. تُحسب من قائمة المشروعات المنشورة المرتبة:

- Previous = العنصر المنشور السابق في `order`.
- Next = العنصر المنشور التالي في `order`.
- لا يوجد دوران تلقائي من الأخير إلى الأول.
- رابط العودة = Selected Work section.
- حالة AR/EN يجب أن تبقى محفوظة أثناء التنقل.
- الرابط الدائم مشتق من slug فقط ولا يتغير بسبب order.

---

## 7. Article Content Model

### 7.1 Identity

| Field | Type | Required |
|---|---|---|
| `article_id` | string | Yes |
| `slug` | string | Yes |
| `status` | enum | Yes |
| `title.ar` / `title.en` | string | Yes |
| `summary.ar` / `summary.en` | string | Yes |
| `lead.ar` / `lead.en` | string | Yes |
| `sections[]` | array | Yes |
| `author` | string | Yes |
| `published_at` | date/null | Conditional |
| `updated_at` | date/null | No |

`article_id` must match `^AH-ART-[0-9]{3}$`.

### 7.2 Article Sections

كل عنصر في `sections`:

- `section_id`: ثابت داخل المقال.
- `heading.ar`, `heading.en`.
- `body.ar`, `body.en`.
- `order`: عدد صحيح موجب.

يمكن إضافة أكثر من فقرة لاحقًا من خلال Rich Text، لكن لا يسمح بإدراج JavaScript أو iframe أو inline style داخل المحتوى.

### 7.3 Knowledge Center Rules

- `published` فقط يظهر في Knowledge Center.
- الترتيب: `published_at` تنازليًا، ثم `order`.
- المقالات الحالية لا تحصل على تواريخ مختلقة؛ تُسجل كـLegacy Date Pending حتى توفر مرجع معتمد.
- رابط العودة لمركز المعرفة ورابط العودة للرئيسية يولدان من القالب لاحقًا ولا يخزنان داخل المقال.

---

## 8. Media Model

### 8.1 Media Object

| Field | Rule |
|---|---|
| `src` | مسار نسبي داخل المستودع |
| `type` | `image` فقط في النطاق الحالي |
| `alt.ar` / `alt.en` | مطلوبان للصورة ذات المعنى |
| `caption.ar` / `caption.en` | اختياريان لكن متلازمان |
| `credit` | اختياري |
| `order` | مطلوب داخل gallery |
| `decorative` | boolean |

إذا كانت `decorative = true` يكون alt فارغًا في العرض، ولا تستخدم الصورة لنقل معلومة أساسية.

### 8.2 Planned Storage

- Profile: `assets/profile/`
- Projects: `assets/projects/`
- Articles: `assets/articles/`
- Controlled uploads: `assets/uploads/`

إنشاء هذه البنية تشغيليًا مؤجل.

### 8.3 File Rules

- الامتدادات المسموحة تصميميًا: `.webp`, `.jpg`, `.jpeg`, `.png`, وSVG المعتمد.
- لا Hotlink خارجي افتراضيًا.
- لا Data URI.
- اسم الملف lowercase-kebab-case.
- Cover image مدعومة ولكنها ليست إلزامية للمقالات الحالية؛ إذا وُجدت تصبح alt وSEO sharing image rules واجبة.
- Gallery ترتيبها صريح ولا يعتمد على اسم الملف.

---

## 9. SEO and Sharing Model

لكل مشروع ومقال:

- `seo.title.ar`, `seo.title.en`
- `seo.description.ar`, `seo.description.en`
- `seo.og_image` اختياري
- `seo.canonical_path`
- `seo.robots` بقيمة محكومة بيئيًا لاحقًا

### Recommended Validation

- SEO title: 30–70 حرفًا.
- SEO description: 80–180 حرفًا.
- canonical path يبدأ `/projects/` أو `/articles/` بحسب النوع.
- OG image، إن وُجدت، يجب أن تكون داخل المستودع.
- بيئة Preview الحالية تبقى noindex حتى قرار Release مستقل.

---

## 10. Claim Governance

### 10.1 Principle

نموذج المحتوى لا ينشئ حقائق. وظيفته حفظ النص المعتمد، مرجعه، وحدوده.

### 10.2 Claim Record

كل ادعاء كمي، زمني، حالة إغلاق، شهادة، نطاق مسؤولية، أو نتيجة يحتاج سجلًا:

| Field | Values / Rule |
|---|---|
| `claim_id` | معرف فريد داخل السجل |
| `claim_type` | `qualitative`, `quantitative`, `status`, `credential`, `scope` |
| `text.ar` / `text.en` | النصان المتكافئان |
| `evidence_refs` | واحد أو أكثر للادعاءات الحساسة |
| `boundary.ar` / `boundary.en` | حدود الإسناد |
| `approval_state` | `pending`, `verified`, `baseline_approved`, `approved`, `rejected` |
| `approved_by` | مطلوب عند approval |
| `approved_at` | مطلوب عند approval |

### 10.3 Controls

- لا ينشر `pending` أو `rejected`.
- كل رقم يحتاج evidence reference.
- كل Status Claim مثل “Formally Closed” يحتاج مرجع حوكمة.
- النص الحالي في RC4.4 يُهاجر حرفيًا ويُوسم `baseline_approved`.
- تعديل claim baseline يفتح Under Review.
- لا تُعرض Evidence References الداخلية للعامة افتراضيًا.
- Claims bilingual يجب أن تتطابق في الرقم والنطاق والفترة والسببية.
- Claim boundaries جزء إلزامي عندما يمكن فهم النتيجة كسبب منفرد أو تعميم غير مدعوم.

---

## 11. Validation Severity

### Errors — block publication

- Missing Project/Article ID.
- Invalid or duplicate slug.
- Missing Arabic or English required field.
- Invalid status transition.
- Quantitative/status claim without evidence.
- Broken media path.
- Duplicate published order.
- Canonical identity mismatch.
- Missing SEO title/description.
- Published item with translation state not approved.

### Warnings — require review

- SEO length outside recommendation.
- Missing optional cover.
- Legacy article date pending.
- Very long title.
- Gallery item without caption.
- Archived content still featured.
- Organization spelling differs from approved migration source.

---

## 12. Reserved Values

### Content Types

- `project`
- `article`

### Status Values

- `draft`
- `under_review`
- `published`
- `archived`

### Translation States

- `incomplete`
- `ready_for_review`
- `approved`

### Claim Approval States

- `pending`
- `verified`
- `baseline_approved`
- `approved`
- `rejected`

### Claim Types

- `qualitative`
- `quantitative`
- `status`
- `credential`
- `scope`

---

## 13. Immutability Rules

بعد أول نشر:

- `project_id` و`article_id` لا يتغيران.
- slug لا يتغير دون Redirect Decision.
- Evidence Reference لا يُحذف إذا كان يدعم claim منشورًا؛ يستبدل بسجل مراجعة.
- تاريخ أول نشر لا يُعاد كتابته.
- تغيير organization أو period أو claim يحتاج Under Review.

---

## 14. Phase Boundaries

هذه المواصفة لا تصرح بـ:

- إنشاء `_config.yml`.
- إنشاء collections أو layouts/includes.
- تحويل HTML إلى Markdown.
- إضافة `.pages.yml`.
- ربط Pages CMS.
- إضافة GitHub Actions.
- تغيير Permalinks أو الموقع الحي.
- بدء Phase 3.

التطبيق التشغيلي ينتظر بوابة اعتماد مستقلة.
