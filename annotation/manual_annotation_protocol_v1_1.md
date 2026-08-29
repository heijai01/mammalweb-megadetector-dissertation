# Manual Annotation Protocol

**Project:** MammalWeb MegaDetector Evaluation  
**Version:** 1.1  
**Date:** 29 July 2026  

## 1. Purpose

This protocol defines the manual ground-truth labels used to evaluate MegaDetector outputs for three target classes:

- human
- animal
- vehicle

The annotator must judge only the displayed image. MegaDetector confidence scores, predicted classes, bounding boxes, sampling strata, and neighbouring frames must remain hidden during annotation.

The same rules should be applied throughout the pilot and full annotation stages.

---

## 2. Unit of annotation

Manual ground truth is assigned at **image level** because MegaDetector is being evaluated at image level.

`sequence_id` is retained for sampling control and later interpretation, but neighbouring frames must not influence the manual label for the current image.

---

## 3. General annotation principles

1. Judge only what is visible in the current image.
2. Do not infer presence from another image in the same sequence.
3. Do not use MegaDetector predictions, confidence scores, or bounding boxes.
4. Partial visibility counts when the visible evidence is sufficient to identify the class.
5. Use `Uncertain` only for genuine ambiguity, not merely because an object is small or distant.
6. When several humans or vehicles are visible, record the highest applicable secondary score found anywhere in the image.
7. Notes are optional and should be used only when they explain an unusual or ambiguous decision.

---

## 4. Core presence labels

Each target class must receive one of:

- `Yes`
- `No`
- `Uncertain`

### 4.1 Human present

#### Yes

Label `Yes` when any real person is visibly present, including:

- a complete person;
- a visible body part such as a hand, leg, head, or torso;
- a distant or partially obscured person;
- a person behind glass;
- a person visibly sitting inside a vehicle;
- a clear reflection of a real person.

A visible driver means both:

- `Human present = Yes`
- `Vehicle present = Yes`

#### No

Label `No` for:

- mannequins;
- statues;
- dolls;
- scarecrows;
- photographs or posters;
- people shown only on a screen;
- clothing without a visible body part;
- shadows without a visible person.

#### Uncertain

Label `Uncertain` when a shape may be human but cannot reliably be distinguished from:

- vegetation;
- equipment;
- an animal;
- glare;
- blur;
- image noise;
- another artefact.

---

### 4.2 Animal present

#### Yes

Label `Yes` for any real non-human animal, including:

- wild mammals;
- livestock;
- pets;
- birds;
- reptiles;
- amphibians;
- clearly visible insects;
- a clearly visible animal carcass.

Partial animals count when the visible part is diagnostic, such as a recognisable head, leg, body, or tail.

#### No

Label `No` for:

- statues;
- toys;
- drawings;
- signs;
- footprints without the animal;
- vegetation or objects that merely resemble an animal.

#### Uncertain

Label `Uncertain` for:

- ambiguous eyeshine;
- indistinct limbs;
- vague silhouettes;
- shapes that cannot reliably be separated from vegetation or image noise.

No animal-welfare field is recorded.

---

### 4.3 Vehicle present

#### Yes

Label `Yes` for clearly visible transport vehicles, including:

- cars;
- vans;
- buses;
- trucks;
- tractors;
- agricultural vehicles;
- motorcycles;
- bicycles;
- all-terrain vehicles;
- trailers that are clearly recognisable as vehicle equipment.

A partially visible vehicle counts when enough is visible to identify it, such as:

- a recognisable cab;
- body shape;
- wheel arrangement;
- front or rear section.

#### No

Label `No` for:

- wheelbarrows;
- stationary machinery that is not used as transport;
- vehicle photographs;
- road signs;
- isolated lights or shapes with no reliable vehicle evidence.

#### Uncertain

Label `Uncertain` when only a possible wheel, light, reflection, or distant shape is visible and the vehicle class cannot be judged reliably.

---

## 5. Image quality

Each image must receive one image-quality label.

### Clear

The image is sufficiently sharp and illuminated to judge the three target classes without meaningful difficulty.

### Difficult but usable

The image contains blur, darkness, glare, weather, distance, or obstruction, but useful class judgements can still be made.

A dark image is not automatically unusable. An image where an animal is clearly visible despite darkness is `Difficult but usable`.

### Unusable

The image is:

- corrupted;
- blank;
- almost completely obscured; or
- too poor for any reliable class judgement.

When `Image quality = Unusable`, record:

- `Human present = Uncertain`
- `Animal present = Uncertain`
- `Vehicle present = Uncertain`

---

## 6. Human-specific secondary labels

Complete these fields only when:

`Human present = Yes`

When no human is present, these fields must remain blank rather than being stored as zero.

When several people are visible, record the highest applicable score in the image.

### 6.1 Human recognisability

#### 0 — Not recognisable

No meaningful identifying information is visible.

Examples:

- tiny or distant person;
- face not visible;
- back turned;
- heavily obscured;
- blurred silhouette;
- only a limb or small body part visible.

#### 1 — Potentially recognisable

Some identifying information may be visible.

Examples:

- partial or blurred face;
- reasonably visible clothing;
- visible body shape;
- distinctive features;
- a person who may be recognisable to someone familiar with them.

#### 2 — Clearly recognisable

The face or other identifying detail is sufficiently clear that recognition is realistically possible.

Recognisability concerns identification, not simply whether a human is visible.

---

### 6.2 Child or vulnerable person visible

Record one of:

- `No`
- `Yes`
- `Uncertain`

Use `Yes` when a child or visibly vulnerable person is clearly present.

Use `Uncertain` when age or vulnerability may be relevant but cannot be judged reliably.

This field does **not** imply that a safeguarding concern exists. For example:

- child visible in an ordinary situation  
  → `child_or_vulnerable_person_visible = Yes`  
  → `safeguarding_risk = 0`

---

### 6.3 Human privacy risk

#### 0 — None or minimal

Use only when:

- no meaningful identifying detail is visible; and
- no sensitive or private context is present.

#### 1 — Moderate

Use when:

- a person is potentially or clearly recognisable in an ordinary context; or
- a non-recognisable person appears in a potentially private context; or
- visible personal behaviour or contextual information may warrant review.

A clearly recognisable person in an ordinary public setting will normally receive:

- `human_recognisability = 2`
- `human_privacy_risk = 1`

#### 2 — High

Use when:

- a recognisable person appears in a clearly private or sensitive setting;
- intimate, medical, or strongly personal information is visible;
- the image should receive priority privacy review.

A clear face does not automatically create privacy risk level 2.

---

### 6.4 Safeguarding risk

#### 0 — None apparent

No visible safeguarding concern.

The presence of a child or vulnerable person alone does not automatically create a safeguarding concern.

#### 1 — Possible concern

The image warrants cautious review because of possible:

- vulnerability;
- distress;
- danger;
- inappropriate circumstances;
- uncertainty that prevents confidently dismissing a concern.

#### 2 — Clear concern

There is clear evidence of serious:

- vulnerability;
- danger;
- distress;
- injury;
- exploitation; or
- another situation requiring priority review.

---

## 7. Vehicle-specific secondary labels

Complete these fields only when:

`Vehicle present = Yes`

When no vehicle is present, these fields must remain blank.

When several vehicles are visible, record the highest applicable score in the image.

### 7.1 Vehicle identifiability

#### 0 — Not identifiable

No meaningful identifying information is visible.

Examples:

- no registration plate visible;
- plate is too small, blurred, blocked, or overexposed;
- generic vehicle with no useful markings.

#### 1 — Potentially identifiable

Identification may be possible with effort.

Examples:

- part of a registration plate may be readable;
- company logo is visible;
- fleet number is partly visible;
- unusual markings or distinctive damage are visible.

#### 2 — Clearly identifiable

The vehicle can realistically be traced or identified.

Examples:

- registration plate clearly readable;
- clear fleet or asset number;
- clearly readable company or owner information;
- highly distinctive identifiers.

A clearly visible vehicle does not automatically receive level 2.

---

### 7.2 Vehicle privacy risk

#### 0 — None or minimal

No meaningful identifying information or sensitive context is present.

#### 1 — Moderate

Potentially identifying information is visible, or the vehicle appears in a possibly private context.

Example:

- readable registration plate on an ordinary public road.

#### 2 — High

A clearly readable identifier appears in a sensitive or private context where disclosure could meaningfully reveal a person's:

- identity;
- home;
- movements;
- activity.

Example:

- clearly readable registration plate beside a private residence in a sensitive context.

Vehicle identifiability and vehicle privacy risk must be recorded separately.

---

## 8. Notes

Notes are optional.

Use notes only when they explain an unusual decision, for example:

- `Possible human behind windscreen`
- `Only animal eyeshine visible`
- `Human-shaped object may be a scarecrow`
- `Image corrupted`
- `Readable registration plate near private residence`

Avoid notes for ordinary clear cases.

---

## 9. Automatic review flag

Set `needs_review = True` when any of the following applies:

- any presence label is `Uncertain`;
- image quality is `Unusable`;
- human recognisability is `1` or `2`;
- human privacy risk is `1` or `2`;
- child or vulnerable person visible is `Yes` or `Uncertain`;
- safeguarding risk is `1` or `2`;
- vehicle privacy risk is `2`.

Otherwise set `needs_review = False`.

---

## 10. Derived human categories

These categories should be derived after annotation rather than selected manually in the app.

### Safeguarding-sensitive human

Set when:

- `child_or_vulnerable_person_visible` is `Yes` or `Uncertain`; or
- `safeguarding_risk >= 1`

### Privacy-sensitive human

Set when:

- `human_recognisability >= 1`; or
- `human_privacy_risk >= 1`

and the image is not already classified as safeguarding-sensitive.

### Benign human

Set when:

- `manual_human_present = Yes`;
- `human_recognisability = 0`;
- `human_privacy_risk = 0`;
- `child_or_vulnerable_person_visible = No`;
- `safeguarding_risk = 0`

These derived categories allow threshold performance to be compared for:

- all human images;
- benign human images;
- privacy-sensitive human images;
- safeguarding-sensitive human images.

---

## 11. Primary-analysis treatment

For the main class-specific calculations:

- `Yes` = positive manual ground truth;
- `No` = negative manual ground truth;
- `Uncertain` = excluded from the primary class-specific calculation;
- `Unusable` images = excluded from primary calculations.

The numbers of uncertain and unusable annotations must be reported rather than silently removed.

Vehicle privacy and identifiability are secondary descriptive analyses and do not determine the main MegaDetector threshold.

---

## 12. Annotation fields

The annotation application should save:

- `annotation_queue_id`
- `annotation_status`
- `manual_human_present`
- `manual_animal_present`
- `manual_vehicle_present`
- `annotation_quality`
- `human_recognisability`
- `child_or_vulnerable_person_visible`
- `human_privacy_risk`
- `safeguarding_risk`
- `vehicle_identifiability`
- `vehicle_privacy_risk`
- `notes`
- `protocol_version`
- `annotator_id`
- `annotation_started_at`
- `annotated_at`
- `annotation_duration_seconds`
- `is_repeat_annotation`
- `needs_review`

Human-specific fields remain blank when `manual_human_present != Yes`.

Vehicle-specific fields remain blank when `manual_vehicle_present != Yes`.

---

## 13. Pilot and protocol freeze

The first 50 images will be annotated using the same Streamlit application intended for the full dataset.

After the pilot:

1. inspect uncertain and unusable rates;
2. review ambiguous decisions;
3. confirm that all response categories are practical;
4. adjust wording only where necessary;
5. freeze the final protocol before continuing.

The first 50 annotations may remain in the final dataset when no material definition changes are made.

If the definitions change materially, the pilot images should be re-annotated.

---

## 14. Blinded repeat-annotation check

After the first full annotation pass, randomly select approximately 5% of the images for blinded re-annotation.

Repeated images should:

- use new queue IDs;
- not be identified as repeats in the interface;
- be mixed into a later annotation session;
- be compared with the original labels after completion.

Agreement should be reported for:

- human presence;
- animal presence;
- vehicle presence.

Secondary-field agreement may also be summarised where sample sizes permit.
