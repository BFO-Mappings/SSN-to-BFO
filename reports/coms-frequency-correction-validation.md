# COMS Frequency Mapping Correction Validation

## Original And Corrected Expressions

Original `Sheet1!17` target:

```text
bfo:Function and bfo:has_realization some cco:PlannedAct and bfo:has_occurrent_part some (cco:Frequency and cco:prescribed_by some cco:ArtifactFunctionSpecification)
```

Corrected `Sheet1!17` target:

```text
bfo:Function and bfo:has_realization some (cco:PlannedAct and bfo:has_occurrent_part some (cco:Frequency and cco:prescribed_by some cco:ArtifactFunctionSpecification))
```

The original expression parsed as a top-level intersection of:

- `bfo:Function`
- `bfo:has_realization some cco:PlannedAct`
- `bfo:has_occurrent_part some (cco:Frequency and cco:prescribed_by some cco:ArtifactFunctionSpecification)`

That placed `bfo:has_occurrent_part` directly on a `bfo:Function`. The corrected expression scopes the occurrent-part restriction inside the `bfo:has_realization` filler.

## Semantic Support Check

- `bfo:Function` is the intended top-level type, matching the current validated `SSN2BFO.ttl` axiom.
- `bfo:has_realization` is the intended relation from the function.
- `cco:PlannedAct` is the intended realization filler.
- `bfo:has_occurrent_part` applies to the planned act, not directly to the function.
- `cco:Frequency` is the intended occurrent-part/profile class.
- `cco:prescribed_by some cco:ArtifactFunctionSpecification` is scoped to `cco:Frequency`.

The corrected COMS expression normalizes to the same structure as the current validated `SSN2BFO.ttl` mapping for `ssn-system:Frequency`.

## Variant Results

| Variant | Expression source | Closure triples | HermiT return code | Named unsat count | Named unsat set | `ssn-system:Frequency` satisfiable |
|---|---|---:|---:|---:|---|---|
| V0 | current spreadsheet expression before correction | 15584 | 1 | 1 | `ssn-system:Frequency` | no |
| V1 | corrected parenthesized realization filler | 15588 | 0 | 0 | clean | yes |
| V2 | current validated `SSN2BFO.ttl` Frequency mapping, expressed in COMS-equivalent generated candidate form | 15588 | 0 | 0 | clean | yes |
| V3 | corrected expression without `cco:prescribed_by some cco:ArtifactFunctionSpecification` | 15579 | 0 | 0 | clean | yes |

## Normalized Variant Expressions

V0 normalized expression:

```text
ObjectIntersectionOf(ObjectSomeValuesFrom(http://purl.obolibrary.org/obo/BFO_0000054 https://www.commoncoreontologies.org/ont00000228) ObjectSomeValuesFrom(http://purl.obolibrary.org/obo/BFO_0000117 ObjectIntersectionOf(ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001920 https://www.commoncoreontologies.org/ont00000118) https://www.commoncoreontologies.org/ont00001047)) http://purl.obolibrary.org/obo/BFO_0000034)
```

V1 normalized expression:

```text
ObjectIntersectionOf(ObjectSomeValuesFrom(http://purl.obolibrary.org/obo/BFO_0000054 ObjectIntersectionOf(ObjectSomeValuesFrom(http://purl.obolibrary.org/obo/BFO_0000117 ObjectIntersectionOf(ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001920 https://www.commoncoreontologies.org/ont00000118) https://www.commoncoreontologies.org/ont00001047)) https://www.commoncoreontologies.org/ont00000228)) http://purl.obolibrary.org/obo/BFO_0000034)
```

V2 normalized expression:

```text
ObjectIntersectionOf(ObjectSomeValuesFrom(http://purl.obolibrary.org/obo/BFO_0000054 ObjectIntersectionOf(ObjectSomeValuesFrom(http://purl.obolibrary.org/obo/BFO_0000117 ObjectIntersectionOf(ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001920 https://www.commoncoreontologies.org/ont00000118) https://www.commoncoreontologies.org/ont00001047)) https://www.commoncoreontologies.org/ont00000228)) http://purl.obolibrary.org/obo/BFO_0000034)
```

V3 normalized expression:

```text
ObjectIntersectionOf(ObjectSomeValuesFrom(http://purl.obolibrary.org/obo/BFO_0000054 ObjectIntersectionOf(ObjectSomeValuesFrom(http://purl.obolibrary.org/obo/BFO_0000117 https://www.commoncoreontologies.org/ont00001047) https://www.commoncoreontologies.org/ont00000228)) http://purl.obolibrary.org/obo/BFO_0000034)
```

## Applied Change

Only the `ssn-system:Frequency` row in `mappings/SSN2BFO-COMS.xlsx` was updated. No other spreadsheet mapping was changed to reduce generated-vs-current differences.

## Regenerated Candidate Result

- Generated ontology: `generated/SSN2BFO-from-COMS.ttl`
- Generated triple count: 800
- Candidate full-closure triple count: 15588
- HermiT return code: 0
- `owl:Nothing` count: 0
- Named unsat count/set: 0 / clean
- `SSN2BFO.ttl` was not modified.
