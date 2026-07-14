# COMS Generated vs Current Mapping Diff

This report compares mapping-bearing axioms and, separately, domain/range property-typing axioms in `generated/SSN2BFO-from-COMS.ttl` against `SSN2BFO.ttl`. The candidate is not loaded together with the current ontology.

## Summary

| Item | Count |
|---|---:|
| mappings present in both | 38 |
| mappings only in generated candidate | 4 |
| mappings only in current validated ontology | 30 |
| class-expression differences | 2 |
| object-property mapping differences | 0 |
| property-chain differences | 0 |
| domain axioms present in both | 0 |
| domain axioms only in generated candidate | 0 |
| domain axioms only in current validated ontology | 22 |
| domain target differences | 0 |
| range axioms present in both | 0 |
| range axioms only in generated candidate | 0 |
| range axioms only in current validated ontology | 0 |
| range target differences | 0 |
| current local domain/range basis axioms absent from candidate | 22 |
| spreadsheet rows intentionally producing no mapping | 5 |

## Mappings Present In Both

- `class` `sosa:ActuatableProperty` `rdfs:subClassOf` `ObjectUnionOf(ObjectIntersectionOf(ObjectSomeValuesFrom(http://purl.obolibrary.org/obo/BFO_0000132 http://www.w3.org/ns/sosa/FeatureOfInterest) http://purl.obolibrary.org/obo/BFO_0000144) ObjectIntersectionOf(ObjectSomeValuesFrom(http://purl.obolibrary.org/obo/BFO_0000197 http://www.w3.org/ns/sosa/FeatureOfInterest) http://purl.obolibrary.org/obo/BFO_0000020))`
- `class` `sosa:Actuation` `owl:equivalentClass` `ObjectIntersectionOf(ObjectSomeValuesFrom(http://www.w3.org/ns/sosa/actsOnProperty http://www.w3.org/ns/sosa/ActuatableProperty) https://www.commoncoreontologies.org/ont00000228)`
- `class` `sosa:FeatureOfInterest` `owl:equivalentClass` `ObjectUnionOf(ObjectIntersectionOf(ObjectSomeValuesFrom(http://www.w3.org/ns/sosa/isFeatureOfInterestOf ObjectUnionOf(http://www.w3.org/ns/sosa/Actuation http://www.w3.org/ns/sosa/Sampling https://www.commoncoreontologies.org/ont00000345)) http://purl.obolibrary.org/obo/BFO_0000015) ObjectIntersectionOf(ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001936 ObjectUnionOf(http://www.w3.org/ns/sosa/Actuation http://www.w3.org/ns/sosa/Sampling https://www.commoncoreontologies.org/ont00000345)) http://purl.obolibrary.org/obo/BFO_0000040))`
- `class` `sosa:ObservableProperty` `rdfs:subClassOf` `ObjectUnionOf(ObjectIntersectionOf(ObjectSomeValuesFrom(http://purl.obolibrary.org/obo/BFO_0000132 http://www.w3.org/ns/sosa/FeatureOfInterest) http://purl.obolibrary.org/obo/BFO_0000144) ObjectIntersectionOf(ObjectSomeValuesFrom(http://purl.obolibrary.org/obo/BFO_0000197 http://www.w3.org/ns/sosa/FeatureOfInterest) http://purl.obolibrary.org/obo/BFO_0000020))`
- `class` `sosa:Observation` `rdfs:subClassOf` `ObjectIntersectionOf(ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001777 ObjectIntersectionOf(https://www.commoncoreontologies.org/ont00000037 https://www.commoncoreontologies.org/ont00000345)) https://www.commoncoreontologies.org/ont00000228)`
- `class` `sosa:Platform` `owl:equivalentClass` `ObjectIntersectionOf(ObjectSomeValuesFrom(http://www.w3.org/ns/sosa/hosts http://www.w3.org/ns/ssn/System) http://purl.obolibrary.org/obo/BFO_0000040)`
- `class` `sosa:Result` `owl:equivalentClass` `ObjectIntersectionOf(ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001816 ObjectUnionOf(http://www.w3.org/ns/sosa/Actuation http://www.w3.org/ns/sosa/Observation http://www.w3.org/ns/sosa/Sampling)) ObjectUnionOf(http://purl.obolibrary.org/obo/BFO_0000040 https://www.commoncoreontologies.org/ont00000958))`
- `class` `sosa:Sample` `owl:equivalentClass` `ObjectIntersectionOf(ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001936 http://www.w3.org/ns/sosa/Sampling) http://purl.obolibrary.org/obo/BFO_0000040)`
- `class` `sosa:Sampling` `owl:equivalentClass` `ObjectIntersectionOf(ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001920 http://www.w3.org/ns/sosa/Procedure) ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001986 http://www.w3.org/ns/sosa/Sample) https://www.commoncoreontologies.org/ont00000228)`
- `class` `sampling:RelationshipNature` `rdfs:subClassOf` `https://www.commoncoreontologies.org/ont00000958`
- `class` `sampling:SampleRelationship` `rdfs:subClassOf` `https://www.commoncoreontologies.org/ont00000958`
- `class` `ssn:Deployment` `owl:equivalentClass` `ObjectIntersectionOf(ObjectSomeValuesFrom(http://www.w3.org/ns/ssn/deployedOnPlatform http://purl.obolibrary.org/obo/BFO_0000040) ObjectSomeValuesFrom(http://www.w3.org/ns/ssn/deployedSystem http://www.w3.org/ns/ssn/System) https://www.commoncoreontologies.org/ont00000228)`
- `class` `ssn:Input` `rdfs:subClassOf` `https://www.commoncoreontologies.org/ont00000958`
- `class` `ssn:Output` `rdfs:subClassOf` `https://www.commoncoreontologies.org/ont00000958`
- `class` `ssn:Property` `owl:equivalentClass` `ObjectUnionOf(http://purl.obolibrary.org/obo/BFO_0000020 http://purl.obolibrary.org/obo/BFO_0000144)`
- `class` `ssn:Stimulus` `owl:equivalentClass` `ObjectIntersectionOf(ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001803 http://www.w3.org/ns/sosa/Observation) https://www.commoncoreontologies.org/ont00000978)`
- `class` `ssn:System` `owl:equivalentClass` `ObjectIntersectionOf(ObjectSomeValuesFrom(http://www.w3.org/ns/ssn/implements http://www.w3.org/ns/sosa/Procedure) http://purl.obolibrary.org/obo/BFO_0000040)`
- `class` `ssn-system:Accuracy` `rdfs:subClassOf` `ObjectIntersectionOf(ObjectSomeValuesFrom(http://purl.obolibrary.org/obo/BFO_0000054 ObjectIntersectionOf(ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001801 ObjectIntersectionOf(ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001904 ObjectIntersectionOf(ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001920 https://www.commoncoreontologies.org/ont00000118) https://www.commoncoreontologies.org/ont00000592)) https://www.commoncoreontologies.org/ont00000853)) http://purl.obolibrary.org/obo/BFO_0000015)) http://purl.obolibrary.org/obo/BFO_0000034)`
- `class` `ssn-system:Condition` `rdfs:subClassOf` `ObjectIntersectionOf(ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001884 https://www.commoncoreontologies.org/ont00000127) ObjectUnionOf(http://purl.obolibrary.org/obo/BFO_0000020 http://purl.obolibrary.org/obo/BFO_0000144))`
- `class` `ssn-system:DetectionLimit` `rdfs:subClassOf` `ObjectIntersectionOf(ObjectSomeValuesFrom(http://purl.obolibrary.org/obo/BFO_0000054 ObjectIntersectionOf(ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001801 ObjectIntersectionOf(ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001904 ObjectIntersectionOf(ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001920 https://www.commoncoreontologies.org/ont00000118) https://www.commoncoreontologies.org/ont00000592)) https://www.commoncoreontologies.org/ont00000853)) http://purl.obolibrary.org/obo/BFO_0000015)) http://purl.obolibrary.org/obo/BFO_0000034)`
- `class` `ssn-system:Drift` `rdfs:subClassOf` `ObjectIntersectionOf(ObjectSomeValuesFrom(http://purl.obolibrary.org/obo/BFO_0000054 ObjectIntersectionOf(ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001801 ObjectIntersectionOf(ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001904 ObjectIntersectionOf(ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001920 https://www.commoncoreontologies.org/ont00000118) https://www.commoncoreontologies.org/ont00000731)) https://www.commoncoreontologies.org/ont00000853)) http://purl.obolibrary.org/obo/BFO_0000015)) http://purl.obolibrary.org/obo/BFO_0000034)`
- `class` `ssn-system:Frequency` `rdfs:subClassOf` `ObjectIntersectionOf(ObjectSomeValuesFrom(http://purl.obolibrary.org/obo/BFO_0000054 ObjectIntersectionOf(ObjectSomeValuesFrom(http://purl.obolibrary.org/obo/BFO_0000117 ObjectIntersectionOf(ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001920 https://www.commoncoreontologies.org/ont00000118) https://www.commoncoreontologies.org/ont00001047)) https://www.commoncoreontologies.org/ont00000228)) http://purl.obolibrary.org/obo/BFO_0000034)`
- `class` `ssn-system:Latency` `rdfs:subClassOf` `ObjectIntersectionOf(ObjectSomeValuesFrom(http://purl.obolibrary.org/obo/BFO_0000054 ObjectIntersectionOf(ObjectSomeValuesFrom(http://purl.obolibrary.org/obo/BFO_0000199 ObjectIntersectionOf(ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001920 https://www.commoncoreontologies.org/ont00000118) http://purl.obolibrary.org/obo/BFO_0000008)) ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001777 https://www.commoncoreontologies.org/ont00000660) ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001777 https://www.commoncoreontologies.org/ont00000978) https://www.commoncoreontologies.org/ont00000228)) http://purl.obolibrary.org/obo/BFO_0000034)`
- `class` `ssn-system:MaintenanceSchedule` `rdfs:subClassOf` `ObjectIntersectionOf(ObjectSomeValuesFrom(http://purl.obolibrary.org/obo/BFO_0000054 ObjectIntersectionOf(ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001834 ObjectIntersectionOf(ObjectSomeValuesFrom(http://purl.obolibrary.org/obo/BFO_0000056 ObjectIntersectionOf(ObjectSomeValuesFrom(http://purl.obolibrary.org/obo/BFO_0000117 ObjectIntersectionOf(ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001920 https://www.commoncoreontologies.org/ont00000319) https://www.commoncoreontologies.org/ont00001047)) https://www.commoncoreontologies.org/ont00000950)) http://purl.obolibrary.org/obo/BFO_0000020)) https://www.commoncoreontologies.org/ont00000004)) http://purl.obolibrary.org/obo/BFO_0000016)`
- `class` `ssn-system:OperatingPowerRange` `rdfs:subClassOf` `ObjectIntersectionOf(ObjectSomeValuesFrom(http://purl.obolibrary.org/obo/BFO_0000054 ObjectIntersectionOf(ObjectSomeValuesFrom(http://purl.obolibrary.org/obo/BFO_0000117 ObjectIntersectionOf(ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001920 https://www.commoncoreontologies.org/ont00000319) https://www.commoncoreontologies.org/ont00000503)) http://purl.obolibrary.org/obo/BFO_0000015)) http://purl.obolibrary.org/obo/BFO_0000034)`
- `class` `ssn-system:OperatingProperty` `rdfs:subClassOf` `ObjectIntersectionOf(ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001920 https://www.commoncoreontologies.org/ont00000319) ObjectUnionOf(http://purl.obolibrary.org/obo/BFO_0000020 http://purl.obolibrary.org/obo/BFO_0000144))`
- `class` `ssn-system:OperatingRange` `rdfs:subClassOf` `ObjectIntersectionOf(ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001920 https://www.commoncoreontologies.org/ont00000319) ObjectUnionOf(http://purl.obolibrary.org/obo/BFO_0000020 http://purl.obolibrary.org/obo/BFO_0000144))`
- `class` `ssn-system:Precision` `rdfs:subClassOf` `ObjectIntersectionOf(ObjectSomeValuesFrom(http://purl.obolibrary.org/obo/BFO_0000054 ObjectIntersectionOf(ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001801 ObjectIntersectionOf(ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001904 ObjectIntersectionOf(ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001920 https://www.commoncoreontologies.org/ont00000118) https://www.commoncoreontologies.org/ont00001256)) https://www.commoncoreontologies.org/ont00000853)) http://purl.obolibrary.org/obo/BFO_0000015)) http://purl.obolibrary.org/obo/BFO_0000034)`
- `class` `ssn-system:Resolution` `rdfs:subClassOf` `ObjectIntersectionOf(ObjectSomeValuesFrom(http://purl.obolibrary.org/obo/BFO_0000054 ObjectIntersectionOf(ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001801 ObjectIntersectionOf(ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001904 ObjectIntersectionOf(ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001920 https://www.commoncoreontologies.org/ont00000118) https://www.commoncoreontologies.org/ont00000731)) https://www.commoncoreontologies.org/ont00000853)) http://purl.obolibrary.org/obo/BFO_0000015)) http://purl.obolibrary.org/obo/BFO_0000034)`
- `class` `ssn-system:ResponseTime` `rdfs:subClassOf` `ObjectIntersectionOf(ObjectSomeValuesFrom(http://purl.obolibrary.org/obo/BFO_0000054 ObjectIntersectionOf(ObjectSomeValuesFrom(http://purl.obolibrary.org/obo/BFO_0000199 ObjectIntersectionOf(ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001920 https://www.commoncoreontologies.org/ont00000118) http://purl.obolibrary.org/obo/BFO_0000008)) ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001777 https://www.commoncoreontologies.org/ont00000660) ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001777 https://www.commoncoreontologies.org/ont00000978) https://www.commoncoreontologies.org/ont00000228)) http://purl.obolibrary.org/obo/BFO_0000034)`
- `class` `ssn-system:Selectivity` `rdfs:subClassOf` `ObjectIntersectionOf(ObjectSomeValuesFrom(http://purl.obolibrary.org/obo/BFO_0000054 ObjectIntersectionOf(ObjectSomeValuesFrom(http://purl.obolibrary.org/obo/BFO_0000057 ObjectIntersectionOf(ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001920 https://www.commoncoreontologies.org/ont00000118) http://purl.obolibrary.org/obo/BFO_0000002)) https://www.commoncoreontologies.org/ont00000228)) http://purl.obolibrary.org/obo/BFO_0000034)`
- `class` `ssn-system:SurvivalProperty` `rdfs:subClassOf` `ObjectIntersectionOf(ObjectSomeValuesFrom(http://purl.obolibrary.org/obo/BFO_0000054 ObjectIntersectionOf(ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001819 ObjectIntersectionOf(ObjectSomeValuesFrom(http://purl.obolibrary.org/obo/BFO_0000055 ObjectIntersectionOf(ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001920 https://www.commoncoreontologies.org/ont00000319) https://www.commoncoreontologies.org/ont00000177)) http://purl.obolibrary.org/obo/BFO_0000015)) http://purl.obolibrary.org/obo/BFO_0000015)) http://purl.obolibrary.org/obo/BFO_0000034)`
- `class` `ssn-system:SystemCapability` `rdfs:subClassOf` `ObjectIntersectionOf(ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001884 https://www.commoncoreontologies.org/ont00000127) ObjectUnionOf(http://purl.obolibrary.org/obo/BFO_0000020 http://purl.obolibrary.org/obo/BFO_0000144))`
- `class` `ssn-system:SystemLifetime` `rdfs:subClassOf` `ObjectIntersectionOf(ObjectSomeValuesFrom(http://purl.obolibrary.org/obo/BFO_0000054 ObjectIntersectionOf(ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001819 ObjectIntersectionOf(ObjectSomeValuesFrom(http://purl.obolibrary.org/obo/BFO_0000055 ObjectIntersectionOf(ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001920 https://www.commoncoreontologies.org/ont00000319) https://www.commoncoreontologies.org/ont00000177)) http://purl.obolibrary.org/obo/BFO_0000015)) https://www.commoncoreontologies.org/ont00001213)) http://purl.obolibrary.org/obo/BFO_0000034)`
- `object_property` `sosa:actsOnProperty` `rdfs:subPropertyOf` `https://www.commoncoreontologies.org/ont00001834`
- `object_property` `sosa:hasResult` `rdfs:subPropertyOf` `https://www.commoncoreontologies.org/ont00001986`
- `object_property` `sosa:usedProcedure` `rdfs:subPropertyOf` `https://www.commoncoreontologies.org/ont00001920`
- `object_property` `ssn-system:qualityOfObservation` `rdfs:subPropertyOf` `https://www.commoncoreontologies.org/ont00001986`

## Only In Generated Candidate

- `class` `ssn-system:Sensitivity` `rdfs:subClassOf` `ObjectIntersectionOf(ObjectSomeValuesFrom(http://purl.obolibrary.org/obo/BFO_0000054 ObjectIntersectionOf(ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001801 ObjectIntersectionOf(ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001904 ObjectIntersectionOf(ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001920 https://www.commoncoreontologies.org/ont00000118) https://www.commoncoreontologies.org/ont00001022)) https://www.commoncoreontologies.org/ont00000853)) http://purl.obolibrary.org/obo/BFO_0000015)) http://purl.obolibrary.org/obo/BFO_0000034)`
- `object_property` `sampling:hasSampleRelationship` `rdfs:subPropertyOf` `https://www.commoncoreontologies.org/ont00001801`
- `object_property` `sampling:natureOfRelationship` `rdfs:subPropertyOf` `https://www.commoncoreontologies.org/ont00001808`
- `object_property` `sampling:relatedSample` `rdfs:subPropertyOf` `https://www.commoncoreontologies.org/ont00001808`

## Only In Current Validated Ontology

- `class` `sosa:Actuator` `rdfs:subClassOf` `ObjectIntersectionOf(ObjectSomeValuesFrom(http://purl.obolibrary.org/obo/BFO_0000196 ObjectIntersectionOf(ObjectSomeValuesFrom(http://purl.obolibrary.org/obo/BFO_0000054 http://www.w3.org/ns/sosa/Actuation) http://purl.obolibrary.org/obo/BFO_0000017)) ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001787 http://www.w3.org/ns/sosa/Actuation) http://purl.obolibrary.org/obo/BFO_0000040)`
- `class` `sosa:Procedure` `rdfs:subClassOf` `ObjectIntersectionOf(ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001942 http://purl.obolibrary.org/obo/BFO_0000015) https://www.commoncoreontologies.org/ont00000965)`
- `class` `sosa:Sampler` `owl:equivalentClass` `ObjectIntersectionOf(ObjectSomeValuesFrom(http://purl.obolibrary.org/obo/BFO_0000196 ObjectIntersectionOf(ObjectSomeValuesFrom(http://purl.obolibrary.org/obo/BFO_0000054 http://www.w3.org/ns/sosa/Sampling) http://purl.obolibrary.org/obo/BFO_0000017)) ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001787 http://www.w3.org/ns/sosa/Sampling) http://purl.obolibrary.org/obo/BFO_0000040)`
- `class` `sosa:Sensor` `rdfs:subClassOf` `ObjectIntersectionOf(ObjectSomeValuesFrom(http://purl.obolibrary.org/obo/BFO_0000196 ObjectIntersectionOf(ObjectSomeValuesFrom(http://purl.obolibrary.org/obo/BFO_0000054 http://www.w3.org/ns/sosa/Observation) http://purl.obolibrary.org/obo/BFO_0000017)) ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001787 http://www.w3.org/ns/sosa/Observation) http://purl.obolibrary.org/obo/BFO_0000040)`
- `class` `sampling:SampleRelationship` `rdfs:subClassOf` `ObjectSomeValuesFrom(http://www.w3.org/ns/sosa/sampling/natureOfRelationship http://www.w3.org/ns/sosa/sampling/RelationshipNature)`
- `class` `sampling:SampleRelationship` `rdfs:subClassOf` `ObjectSomeValuesFrom(http://www.w3.org/ns/sosa/sampling/relatedSample http://www.w3.org/ns/sosa/Sample)`
- `class` `ssn-system:ActuationRange` `rdfs:subClassOf` `ObjectIntersectionOf(ObjectSomeValuesFrom(http://purl.obolibrary.org/obo/BFO_0000054 ObjectIntersectionOf(ObjectIntersectionOf(ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001920 https://www.commoncoreontologies.org/ont00000118) ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001986 http://purl.obolibrary.org/obo/BFO_0000020)) http://www.w3.org/ns/sosa/Actuation)) http://purl.obolibrary.org/obo/BFO_0000034)`
- `class` `ssn-system:Sensitivity` `rdfs:subClassOf` `ObjectIntersectionOf(ObjectSomeValuesFrom(http://purl.obolibrary.org/obo/BFO_0000054 ObjectIntersectionOf(ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001801 https://www.commoncoreontologies.org/ont00000853) ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001904 https://www.commoncoreontologies.org/ont00001022) ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001920 https://www.commoncoreontologies.org/ont00000118) http://purl.obolibrary.org/obo/BFO_0000015)) http://purl.obolibrary.org/obo/BFO_0000034)`
- `object_property` `sosa:isActedOnBy` `rdfs:subPropertyOf` `https://www.commoncoreontologies.org/ont00001886`
- `object_property` `sosa:isResultOf` `rdfs:subPropertyOf` `https://www.commoncoreontologies.org/ont00001816`
- `object_property` `sosa:madeBySampler` `rdfs:subPropertyOf` `https://www.commoncoreontologies.org/ont00001833`
- `object_property` `sosa:madeBySensor` `rdfs:subPropertyOf` `https://www.commoncoreontologies.org/ont00001833`
- `object_property` `sosa:madeObservation` `rdfs:subPropertyOf` `https://www.commoncoreontologies.org/ont00001787`
- `object_property` `sosa:madeSampling` `rdfs:subPropertyOf` `https://www.commoncoreontologies.org/ont00001787`
- `object_property` `sosa:observes` `rdfs:subPropertyOf` `http://www.w3.org/ns/ssn/forProperty`
- `object_property` `ssn:deployedOnPlatform` `rdfs:subPropertyOf` `http://purl.obolibrary.org/obo/BFO_0000057`
- `object_property` `ssn:deployedSystem` `rdfs:subPropertyOf` `http://purl.obolibrary.org/obo/BFO_0000057`
- `object_property` `ssn:detects` `rdfs:subPropertyOf` `https://www.commoncoreontologies.org/ont00001886`
- `object_property` `ssn:hasDeployment` `rdfs:subPropertyOf` `http://purl.obolibrary.org/obo/BFO_0000056`
- `object_property` `ssn:hasSubSystem` `rdfs:subPropertyOf` `http://purl.obolibrary.org/obo/BFO_0000178`
- `object_property` `ssn:inDeployment` `rdfs:subPropertyOf` `http://purl.obolibrary.org/obo/BFO_0000056`
- `object_property` `ssn-system:hasOperatingRange` `rdfs:subPropertyOf` `http://purl.obolibrary.org/obo/BFO_0000196`
- `object_property` `ssn-system:hasSurvivalRange` `rdfs:subPropertyOf` `http://purl.obolibrary.org/obo/BFO_0000196`
- `object_property` `ssn-system:hasSystemCapability` `rdfs:subPropertyOf` `http://purl.obolibrary.org/obo/BFO_0000196`
- `object_property` `ssn:wasOriginatedBy` `rdfs:subPropertyOf` `https://www.commoncoreontologies.org/ont00001962`
- `property_chain` `sosa:hasSample` `owl:propertyChainAxiom` `https://www.commoncoreontologies.org/ont00001873 o http://purl.obolibrary.org/obo/BFO_0000084`
- `property_chain` `sosa:hosts` `owl:propertyChainAxiom` `http://purl.obolibrary.org/obo/BFO_0000196 o http://purl.obolibrary.org/obo/BFO_0000054 o http://purl.obolibrary.org/obo/BFO_0000057`
- `property_chain` `sosa:isHostedBy` `owl:propertyChainAxiom` `http://purl.obolibrary.org/obo/BFO_0000056 o http://purl.obolibrary.org/obo/BFO_0000055 o http://purl.obolibrary.org/obo/BFO_0000197`
- `property_chain` `sosa:isSampleOf` `owl:propertyChainAxiom` `http://purl.obolibrary.org/obo/BFO_0000101 o https://www.commoncoreontologies.org/ont00001938`
- `property_chain` `ssn:implementedBy` `owl:propertyChainAxiom` `https://www.commoncoreontologies.org/ont00001942 o https://www.commoncoreontologies.org/ont00001833`

## Class-Expression Differences

- `sampling:SampleRelationship` `rdfs:subClassOf`: generated=['https://www.commoncoreontologies.org/ont00000958']; current=['ObjectSomeValuesFrom(http://www.w3.org/ns/sosa/sampling/natureOfRelationship http://www.w3.org/ns/sosa/sampling/RelationshipNature)', 'ObjectSomeValuesFrom(http://www.w3.org/ns/sosa/sampling/relatedSample http://www.w3.org/ns/sosa/Sample)', 'https://www.commoncoreontologies.org/ont00000958']
- `ssn-system:Sensitivity` `rdfs:subClassOf`: generated=['ObjectIntersectionOf(ObjectSomeValuesFrom(http://purl.obolibrary.org/obo/BFO_0000054 ObjectIntersectionOf(ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001801 ObjectIntersectionOf(ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001904 ObjectIntersectionOf(ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001920 https://www.commoncoreontologies.org/ont00000118) https://www.commoncoreontologies.org/ont00001022)) https://www.commoncoreontologies.org/ont00000853)) http://purl.obolibrary.org/obo/BFO_0000015)) http://purl.obolibrary.org/obo/BFO_0000034)']; current=['ObjectIntersectionOf(ObjectSomeValuesFrom(http://purl.obolibrary.org/obo/BFO_0000054 ObjectIntersectionOf(ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001801 https://www.commoncoreontologies.org/ont00000853) ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001904 https://www.commoncoreontologies.org/ont00001022) ObjectSomeValuesFrom(https://www.commoncoreontologies.org/ont00001920 https://www.commoncoreontologies.org/ont00000118) http://purl.obolibrary.org/obo/BFO_0000015)) http://purl.obolibrary.org/obo/BFO_0000034)']

## Object-Property Mapping Differences

- none

## Property-Chain Differences

- none

## Domain Axioms Present In Both

- none

## Domain Axioms Only In Generated Candidate

- none

## Domain Axioms Only In Current Validated Ontology

- `sosa:isActedOnBy` `rdfs:domain` `http://www.w3.org/ns/sosa/ActuatableProperty`
- `sosa:isObservedBy` `rdfs:domain` `http://www.w3.org/ns/sosa/ObservableProperty`
- `sosa:isSampleOf` `rdfs:domain` `http://www.w3.org/ns/sosa/Sample`
- `sosa:madeByActuator` `rdfs:domain` `http://www.w3.org/ns/sosa/Actuation`
- `sosa:madeObservation` `rdfs:domain` `http://www.w3.org/ns/sosa/Sensor`
- `sosa:madeSampling` `rdfs:domain` `http://www.w3.org/ns/sosa/Sampler`
- `sosa:observedProperty` `rdfs:domain` `http://www.w3.org/ns/sosa/Observation`
- `ssn:detects` `rdfs:domain` `http://www.w3.org/ns/sosa/Sensor`
- `ssn:hasDeployment` `rdfs:domain` `http://www.w3.org/ns/ssn/System`
- `ssn:hasInput` `rdfs:domain` `http://www.w3.org/ns/sosa/Procedure`
- `ssn:hasOutput` `rdfs:domain` `http://www.w3.org/ns/sosa/Procedure`
- `ssn:hasSubSystem` `rdfs:domain` `http://www.w3.org/ns/ssn/System`
- `ssn:implements` `rdfs:domain` `http://www.w3.org/ns/ssn/System`
- `ssn:inDeployment` `rdfs:domain` `http://www.w3.org/ns/sosa/Platform`
- `ssn:isProxyFor` `rdfs:domain` `http://www.w3.org/ns/ssn/Stimulus`
- `ssn-system:hasOperatingProperty` `rdfs:domain` `http://www.w3.org/ns/ssn/systems/OperatingRange`
- `ssn-system:hasOperatingRange` `rdfs:domain` `http://www.w3.org/ns/ssn/System`
- `ssn-system:hasSurvivalProperty` `rdfs:domain` `http://www.w3.org/ns/ssn/systems/SurvivalRange`
- `ssn-system:hasSurvivalRange` `rdfs:domain` `http://www.w3.org/ns/ssn/System`
- `ssn-system:hasSystemCapability` `rdfs:domain` `http://www.w3.org/ns/ssn/System`
- `ssn-system:hasSystemProperty` `rdfs:domain` `http://www.w3.org/ns/ssn/systems/SystemCapability`
- `ssn:wasOriginatedBy` `rdfs:domain` `http://www.w3.org/ns/sosa/Observation`

## Domain Target Differences

- none

## Range Axioms Present In Both

- none

## Range Axioms Only In Generated Candidate

- none

## Range Axioms Only In Current Validated Ontology

- none

## Range Target Differences

- none

## Spreadsheet Rows Intentionally Producing No Mapping

- `sosa:hasFeatureOfInterest` at `Sheet2!6`
- `sosa:isFeatureOfInterestOf` at `Sheet2!8`
- `sosa:phenomenonTime` at `Sheet2!9`
- `ssn-system:inCondition` at `Sheet2!11`
- `ssn:isPropertyOf` at `Sheet2!13`

## Terms Requiring Human Review

Human review should consider mapping differences separately from domain/range property-typing differences, plus explicitly blank spreadsheet rows.
