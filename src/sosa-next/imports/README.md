# Pinned forthcoming SOSA imports

This directory contains the local source closure used to develop and validate
the forthcoming SOSA-to-BFO/CCO mapping. These files are separate from the
dependencies used by the maintained current SSN/SOSA products.

## Upstream source

The following eight files are byte-for-byte copies from the W3C
`sdw-sosa-ssn` repository at commit:

`af425a0454ec00512a5ebfa2873fe35a077f5fda`

| Local file | SHA-256 |
|---|---|
| `sosa.ttl` | `a1875d19988b0bd17e5cd3a61f76440b6e0f7b1e07bd30237e6fb7341c170305` |
| `sosa-common.ttl` | `31bb4a6fb3d4b8b7612998744f73b5a8194d34ef866184460ed22dc0f78a91aa` |
| `sosa-observation.ttl` | `da6b3b2304a491c45a8822e70529f72c1d73606dda9a8b73b0c5360313ab30c3` |
| `sosa-actuation.ttl` | `18c840cba0a4e148048e6147cb2b5fa9b36bbf09dcb60802ce65d3ecfb3175c5` |
| `sosa-sampling.ttl` | `82e59f8354debaff6cdcb3e354397ea17318e4bc45dc7a8a005c1fa5404d2d70` |
| `sosa-deprecated.ttl` | `5a99055ea8938f0e9384b81ad3ac1b3eaa13aaf50c54e308cab9551c88392987` |
| `sosa-system.ttl` | `1ac64f168163b7e6139bf632a07e35112837a58021ff706688d2c626e9cc1caf` |
| `sample-relations.ttl` | `0f9c8561626e9c75cb364d3c0f6cdb3197e9e72b6727b095309fc3fb1d605e32` |

Do not edit these eight files directly. Any upstream update must replace the
relevant files from an explicitly selected commit and update the enforced
digests, tests, and this documentation in the same change.

## Local declaration overlay

`sosa-source-declaration-overlay.ttl` is maintained locally and is not an
upstream W3C file. Its SHA-256 is:

`5cee7b4c6799df0ebff5f4c503b7495fce67f940c53711a2aecfa6896f8d3af2`

The pinned upstream source uses `sosa:Battery` as an OWL class but does not
explicitly declare it as one. The overlay adds only that declaration so local
COMS source-term validation and OWL reasoning can treat the term according to
its upstream usage without modifying the pinned source.

## Resolution and validation

`../catalog-v001.xml` resolves the forthcoming SOSA module IRIs to these local
files. It also resolves the merged CCO/BFO dependency to the repository-level
`imports/cco.ttl`.

Run the governed workbook and HermiT validation with:

```bash
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=tools \
python tools/check_sosa_next_mapping.py
```

The checker enforces the source-file digests before parsing the workbook or
running reasoning.
