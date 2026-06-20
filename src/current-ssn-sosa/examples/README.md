# Current SSN/SOSA examples

Current SSN/SOSA example instance data lives under `examples/sosa-instance-data/`.

These files are example/instance data for review and testing. They are not ontology imports, and they are not currently imported into the current SSN/SOSA editor ontology.

To parse-check all Turtle examples without modifying them, run:

```sh
make validate-examples
```

From the repository root, the same check can be run with:

```sh
make -C src validate-examples
```

The target writes only generated temporary parse outputs under `build/artifacts/`.
