# Cover letter draft for author review

Dear Editors,

Please consider our manuscript, “Top-k descriptor concatenation for texture classification: direct use versus margin-gated acquisition,” as an original research article for *Pattern Recognition*.

Concatenating texture descriptors raises two practical questions: how many blocks to extract, and which images need the joint representation. We address them separately on six texture datasets. We first assess the effect of retaining whole descriptor blocks ranked by individual validation performance. We then fix the four-block representation and compare direct extraction with conditional acquisition on the same images, using a randomized control with the same number of escalations.

The paired comparison shows which first-stage errors the gate identifies and which correct predictions are overwritten by the joint classifier. It also identifies datasets where additional blocks remain valuable. We estimate extraction cost for the fixed Top-4 cascade and separately measure end-to-end inference latency for a margin-gated ensemble. The results distinguish average savings from tail-latency and accuracy trade-offs. We provide code, archived prediction counts, and protocol details to support verification.

We believe the study would interest readers working on feature fusion and cost-aware inference for recognition systems.

Sincerely,

Carlos Ayala and Joaquín Delgado
