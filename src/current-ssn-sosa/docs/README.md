# Current SSN/SOSA source notes

The current mapping authority is `mappings/SSN2BFO-COMS.xlsx`; the integrated ontology and four maintained modules are generated from it. The former current-track editor, direct-mapping shells, development catalog, and hierarchy-projection analysis have been retired rather than preserved as aliases.

This source directory retains only example data and its explicit parse-validation target. Validation resolves the maintained project modules and the pinned local dependencies directly, so it requires no development XML catalog. The full flattened merged CCO/BFO file `imports/cco.ttl` is a validation dependency, not a placeholder or mapping authority.

The separate `sosa-next` scaffold remains intentionally inactive and unchanged. Formal release packages generate their own byte-governed package-relative catalog. Persistent-IRI deployment, redirects, and actual publication remain future work; no compatibility promise or actual release is created here.
