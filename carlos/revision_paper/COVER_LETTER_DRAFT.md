# Cover letter draft for author review

Dear Editors,

Please consider our manuscript, “Top-k descriptor concatenation for texture classification: direct use versus margin-gated acquisition,” as an original research article for *Pattern Recognition*.

Concatenating texture descriptors raises two practical questions: how many blocks to extract, and which images need the joint representation. We address them separately on six texture datasets. We first assess the effect of retaining whole descriptor blocks ranked by individual validation performance. We then fix the four-block representation and compare direct extraction with conditional acquisition on the same images, using a randomized control with the same number of escalations.

The paired comparison shows which first-stage errors the gate identifies and which correct predictions are overwritten by the joint classifier. It also identifies datasets where additional blocks remain valuable. We estimate extraction cost for the fixed Top-4 cascade and separately measure end-to-end inference latency for a margin-gated ensemble. The results distinguish average savings from tail-latency and accuracy trade-offs. We provide code, archived prediction counts, and protocol details to support verification.

We believe the study would interest readers working on feature fusion and cost-aware inference for recognition systems.

**Comparison with published methods.** The manuscript places its results beside five texture-recognition studies: Neshov et al. on multilayer aggregation, Gupta et al. on HyTexNet, Chang et al. on multiscale LBP and cellular-network contours, Simon and Uma on DeepLumina, and Paiva et al. on RGB pixel n-grams. We identify the data and split for each published accuracy. The paired comparisons use our own models under common conditions because the published protocols and model setups differ.

**Public benchmarks.** We use DTD, FMD, grayscale CUReT, Outex TC 00013, KTH-TIPS2-b, and the original-image subset of the Comprehensive Soil Classification Datasets. The data guide links the manifests and original distributions or archived source descriptions.

**Validation measures.** We report accuracy and, where available in the paired analyses, macro-precision, macro-recall, and macro-F1. The online experiment measures single-image latency, including mean and tail behavior, from the calls that make the predictions. For the fixed Top-4 cascade, the evaluation reports escalation rate and projected extraction cost.

Sincerely,

Carlos Ayala and Joaquín Delgado
