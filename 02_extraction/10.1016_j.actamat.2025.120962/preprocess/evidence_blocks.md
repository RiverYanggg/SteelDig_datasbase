[BLOCK b0001]
Full length article

[BLOCK b0002]
A novel training-free approach to efficiently extracting material microstructures via visual large model

[BLOCK b0003]
Changtai Li <sup>a,b,1</sup> , Xu Han <sup>b,1</sup> , Chao Yao <sup>c,d,e</sup> , Yu Guo <sup>a</sup>, Zixin Li <sup>a</sup>, Lei Jiang <sup>a</sup>, Wei Liu <sup>b</sup>, Haiyou Huang <sup>a</sup> , Huadong Fu <sup>a,f,\*</sup> , Xiaojuan Ban a,b,d,e,f,\*

[BLOCK b0004]
<sup>a</sup> Beijing Advanced Innovation Center for Materials Genome Engineering, University of Science and Technology Beijing, 100083, Beijing, China

[BLOCK b0005]
<sup>b</sup> School of Intelligence Science and Technology, University of Science and Technology Beijing, 100083, Beijing, China

[BLOCK b0006]
<sup>c</sup> School of Computer and Communication Engineering, University of Science and Technology Beijing, 100083, Beijing, China

[BLOCK b0007]
<sup>d</sup> Beijing Key Laboratory of Big Data Innovation and Application for Skeletal Health Medical Care, 100083, Beijing, China

[BLOCK b0008]
<sup>e</sup> Key Laboratory of Advanced Materials and Devices for Post-Moore Chips, Ministry of Education, 100083, Beijing, China

[BLOCK b0009]
<sup>f</sup> Institute of Materials Intelligent Technology, Liaoning Academy of Materials, 110004, Shenyang, China

[BLOCK b0010]
A R T I C L E I N F O

[BLOCK b0011]
Keywords: Material microstructure Image recognition Visual large model Deep learning

[BLOCK b0012]
A B S T R A C T

[BLOCK b0013]
The precise quantitative description of material microstructures is essential for deeply exploring the relationship between material composition and property. This significant understanding efficiently enables composition design, process optimization, and property enhancement. Traditionally, the analysis of material microstructures has relied heavily on professional expertise. Even with machine /deep learning (ML/DL)-based analysis methods, substantial expert annotation is required for training, and the trained models often suffer from weak general izability and poor recognition of new images. This study proposed MatSAM (Materials Segment Anything Model), a novel training-free approach for efficient material microstructure extraction based on the Segment Anything Model (SAM), a type of visual large model (VLM). Integrating region marking and microscopy-adapted points, an automated point-based prompt strategy was developed to achieve accurate and efficient material microstructure recognition. Without any manual annotations, MatSAM precisely identified 11 kinds of metallic material mi crostructures obtained through various characterization methods. Compared to optimal conventional rule-based methods that do not involve a learning process (non-ML/DL), MatSAM achieved an average relative improve ment of 35.4 % in metrics combining the adjusted Rand index (ARI) and Intersection over Union (IoU), out performing the original SAM by an average of 13.9 %. On four public microstructure segmentation datasets, the IoU of MatSAM showed an average improvement of 7.5 % over corresponding specialist deep models requiring annotations. Meanwhile. MatSAM satisfied the generalization capability of a single model for various microstructures, including grain boundaries, phases, and defects. This approach significantly reduces the labor and computational costs of quantitatively characterizing material microstructures, further accelerating the devel opment of advanced materials.

[BLOCK b0014]
1. Introduction

[BLOCK b0015]
Having long been a central pursuit in materials science research, a clear relationship between composition, microstructure, and property is essential for material design, process optimization, and property enhancement [1–5]. Notably, the microstructure of materials acts as a critical link between composition and performance, providing deep in sights into material properties [6–8]. Various characterization techniques are employed to obtain images that describe material microstructural information, including optical microscopy (OM), scan ning electron microscopy (SEM), transmission electron microscopy (TEM), and X-ray computed tomography (XCT) [9,10].

[BLOCK b0016]
However, the extraction of key microstructural information—both qualitative and quantitative—from various types of micrographs heavily depends on expert experience and demands huge human and compu tational resources [11]. An even greater concern is the inconsistency when different experts handle the same images, leading to a lack of general comparability. Furthermore, with the advancement of auto mated characterization equipment and experiment robots [12,13], the volume of micrographs requiring analysis has been growing exponen tially [14,15]. Therefore, developing standardized, highly accurate, and robust models for extracting microstructural information from massive images is essential [16]. Such models are expected to significantly accelerate the extraction of microstructures, thereby enabling more efficient optimization of material processes and properties.

[BLOCK b0017]
Fig. 1. Microscopy datasets used in this study. Different metallic materials are demonstrated. Based on structural features, the materials are classified into polycrystalline & single-phase, polycrystalline & multiphase, and single crystal & multiphase. The characterizing methods include OM, SEM, and XCT.

[BLOCK b0018]
In recent years, conventional rule-based and deep learning-based (DL-based) image processing techniques have been increasingly applied in microstructure recognition and analysis [11,17]. Conven tional rule-based algorithms, which are non-machine learning or deep learning (non-ML/DL), work well only on high-contrast micrographs with homogeneous compositions [18–20]. Oppositely, DL methods can recognize diverse and complex structures under inconsistent imaging protocols and conditions [6,21,22]. Nonetheless, annotating (or label ing) microstructure regions demands significant expertise and substan tial manpower, making it difficult to acquire a large volume of high-quality annotations for model training. Meanwhile, most existing DL approaches struggle to achieve universal and robust microstructure recognition, i.e., weak generalizability across different microscopy datasets [16]. Those specialist models often perform optimally on the datasets they are trained on, restricting their applicability to new images with varying scales, resolutions, and complexities. To reduce the need for annotations and enhance generalizability, pre-training (acquiring robust initial feature representations) on large-scale datasets followed by fine-tuning (fitting the target data domain) has been widely utilized [23] and applied for micrographs [16]. However, these approaches still require annotations to fine-tune the model and hardly handle unseen images. In a nutshell, typical DL methods [6], trained on specific mi crographs [24–26] or borrowing pre-training and fine-tuning paradigms [27], still exhibit limited transferability and generalization or in efficiency, making achieving optimal results across different materials, scales, and conditions difficult [28].

[BLOCK b0019]
More recently, visual large models (VLMs) have been profoundly reshaping the development of image analysis [29]. Segment Anything Model (SAM) has emerged as the first VLM for recognizing any object in any image, as reported in [30]. It was trained on an unprecedented large-scale dataset (SA-1B). Notably, SAM’s everything mode automat ically generates grid points as a prompt. It identifies all objects without human intervention, which has the potential to greatly assist in effi ciently recognizing microstructures of various materials. Unfortunately, despite SAM’s strong feature representation ability, it fails to identify microstructures plausibly, mainly due to SAM’s inherent bias toward natural images [31–33].

[BLOCK b0020]
To respond to the above issues and focus on efficiently recognizing material microstructures, we propose MatSAM (Materials Segment Anything Model), a training-free approach built upon SAM, which flexibly and cost-effectively recognizes microstructures in poly crystalline or multiphase micrographs by injecting domain prior knowledge of structure and characterization into the model. In partic ular, besides the native grid point prompt, MatSAM employs a structureaware point generation to adaptively provide the prompt to guide the VLM in yielding expected recognition results. Of note, the generation and adaptation of prompt points are automated; when adapting to a batch of new micrographs, users only need to provide the image cate gory (polycrystalline or multiphase for grain boundary or phase extraction), instead of prompt points for each target object.

[BLOCK b0021]
Further. we evaluated MatSAM's versatility and performance across 11 in-house and public microscopy datasets, including 5 polycrystalline and 6 multiphase datasets characterized by OM, SEM, or XCT. MatSAM, without training and annotations, demonstrated notable improvements over SAM, specialist DL models and rule-based methods, validating the effectiveness of our automated structure-aware prompt strategy. Consequently, these results highlight the potential of leveraging VLM with tailored optimization to reduce human labor in microstructural information extraction, accelerating the development of advanced materials.

[BLOCK b0022]
2. Materials and methods

[BLOCK b0023]
2.1. Microscopy datasets

[BLOCK b0024]
We have collected and curated 11 materials microscopy datasets (see Fig. 1), five public (solid border), and six in-house (dashed border), to explore the recognition capability of MatSAM on different materials and microstructures (distinguished by three colors) under various imaging conditions. Each card includes an example image, the names of the material and dataset, the type of microstructure, and the real size and resolution of the micrograph. Polycrystalline & single phase, poly crystalline & multiphase, and single crystal & multiphase have blue, green, and light-yellow backgrounds, respectively. The micrographs in these 11 datasets were acquired using either OM. SEM, or XCT, and all in-house datasets have manual annotations. Specifically, images of pure irons (PI-1/2), stainless steel (SS), high-entropy alloy (HEA), and low carbon steel (LCS) [11] were captured using OM; images of dual-phase steels (DP590–1/2), nickel-based superalloys (NBS-1/2) [16], and ul trahigh carbon steel (UHCS) [11] were obtained using SEM; images of AlZn alloy (AZA) [25] were generated using XCT. To be noted, for public micrograph datasets—AZA [25], NBS-1/2 [16], and UHCS [11]—we used the attached test data. For another public dataset, LCS [11], where labels were not provided, part of the raw images was annotated for evaluation.

[BLOCK b0025]
Fig. 2. Illustration of visual differences between polycrystalline and multiphase micrographs.

[BLOCK b0026]
Fig. 3. Schematic of MatSAM for training-free microstructure recognition.

[BLOCK b0027]
We elucidate the characteristics of two common material micrographs, i.e., polycrystalline images and multiphase images, exemplified in Fig. 2. The conspicuous difference between them stems from whether there are voids or gaps between multiple target objects. For a poly crystalline image, boundaries separate grains that adhere closely without voids between them, containing two classes - grain and its boundary with no background. For a multiphase image, gaps usually remain between phase regions that disperse across the whole image, consisting of multiple classes - different types of phases with back ground. Despite the above diversity, we deem they share a commonality: Regions of Interest (ROIs) can be effectively segmented as long as the prompt points abide by their features and distribution, which the pro posed structure-aware prompt point generation of MatSAM can uni versally provide.

[BLOCK b0028]
2.2. Training-free MatSAM framework

[BLOCK b0029]
We implemented MatSAM based on SAM [30] which was pre-trained on the largest segmentation dataset to date. SAM used a primary ar chitecture of an image encoder, a prompt encoder, and a segmentation mask decoder. Its emergent zero-shot capability and prompt engineering flexibility have created the conditions for training-free adaptation to various downstream tasks. Based on the pre-trained parameters of SAM and the orchestrated prompt strategy, MatSAM does not require extra training and human labeling; it processes a raw image input through the encoder, tokenizes a prompt, and combines the learned image feature with prompt embedding to output segmentation masks that extract material microstructures like grains, phases, precipitates, cracks, and so on. The schematic of MatSAM is shown in Fig. 3.

[BLOCK b0030]
MatSAM utilizes SAM’s cropping strategy to generate hierarchical crop boxes for multi-scale recognition. Each image is divided into mul tiple cropped regions of three different sizes: 1/1 (original size), 1/4, and $_ { 1 / 1 6 }$ of the image, with exact pixel sizes depending on the original resolution. To ensure that objects near the crop boundaries are adequately captured in neighboring crops, overlaps were applied across different crops, with a default overlap ratio of 0.5. The image encoder compresses the input image using a pre-trained Vision Transformer (ViT) [34], handling varying resolutions and outputting embeddings. The prompt encoder receives merged structure-aware prompt points and encodes the position information (mapping the prompt to feature embedding). Along with the prompt embedding, the image embedding is refined through self-attention (SA) and cross-attention (CA) in both prompt-to-image and image-to-prompt directions [35]. The mask decoder then upsamples the fused image embedding and, via a multi layer perceptron (MLP) and linear classifier, generates multiple candi date regions. To manage the resulting ambiguity, like SAM, candidate masks (up to three) are ranked by score, retaining those with the highest confidence, and Non-Maximum Suppression (NMS) is applied first within each cropped frame and then across all frames to produce the final, non-overlapping segmentation masks.

[BLOCK b0031]
2.3. Automated structure-aware prompt generation

[BLOCK b0032]
The native point prompt of SAM (everything mode) provided a fixed number of points $( \mathbf { e } . \mathbf { g } . , \mathbf { a } 3 2 \times 3 2$ grid of equally spaced points over the entire image), which was enough to consider all ROIs in a natural image. Nevertheless, directly using the strategy in microscopy resulted in massive unacceptable false masks, i.e., local mis-segmentation of grain

[BLOCK b0033]
Table 1

[BLOCK b0034]
Evaluation protocols of 11 public and in-house microscopy datasets.

[BLOCK b0035]
An upward arrow indicates that a higher value of the metric corresponds to better segmentation performance

[BLOCK b0036]
<table><tr><td>Type</td><td>Name</td><td>Material</td><td>Resolution (pixels)</td><td>#</td><td>Metrics</td></tr><tr><td>grain</td><td>PI-1</td><td>pure iron</td><td> $1024 \times 1024$ </td><td>59</td><td>ARI↑</td></tr><tr><td rowspan="4">boundary</td><td>SS</td><td>stainless steel</td><td> $1024 \times 1024$ </td><td>44</td><td>F1↑</td></tr><tr><td>HEA</td><td>high-entropy alloy</td><td> $1771 \times 1061$ </td><td>38</td><td>Recall</td></tr><tr><td>PI-2</td><td>pure iron</td><td> $1280 \times 960$ </td><td>12</td><td></td></tr><tr><td>LCS [11]</td><td>low carbon steel</td><td> $1360 \times 600$ </td><td>16</td><td></td></tr><tr><td rowspan="9">phase</td><td>NBS-1</td><td>Ni-based</td><td> $512 \times 512$ </td><td>4</td><td>IoU↑</td></tr><tr><td>[16]</td><td>superalloy</td><td></td><td></td><td>F1↑</td></tr><tr><td>NBS-2</td><td>Ni-based</td><td> $512 \times 512$ </td><td>5</td><td>Recall</td></tr><tr><td>[16]</td><td>superalloy</td><td></td><td></td><td></td></tr><tr><td>AZA [25]</td><td>AlZn alloy</td><td> $852 \times 852$ </td><td>2</td><td></td></tr><tr><td>UHCS</td><td>ultrahigh</td><td> $645 \times 475$ </td><td>5</td><td></td></tr><tr><td>[11]</td><td>carbon steel</td><td></td><td></td><td></td></tr><tr><td>DP590–1</td><td>dual-phase steel</td><td> $512 \times 512$ </td><td>23</td><td></td></tr><tr><td>DP590–2</td><td>dual-phase steel</td><td> $1024 \times 768$ </td><td>21</td><td></td></tr></table>

[BLOCK b0037]
or phase regions and loss of a considerable quantity of objects at the edge of the image. Therefore, improving the prompt strategy was considered to achieve the practical training-free purpose (without manual annota tion). Based on this motivation, we constructed a novel prompt strategy that enhanced point generation by tailoring it to microscopy with proper modification. The introduced structure-aware prompt point generation module provided centroid points for each potential target, thus auto mating the process of generating appropriate points. The workflow of the point generation (Generation of ROI points and Modulation of grid points below) is described in Algorithm 1, where I is the input microscopic image, c is the category (‘polycrystalline’ or ‘multiphase’), the threshold (preset to 3 pixels) is used to determine the distance be tween two points are too close, and $\mathrm { P o i n t s } _ { \mathrm { m e r g e } }$ comprises adjusted ROI and grid points.

[BLOCK b0038]
Generation of ROI points. Rule-based image segmentation tech niques (Canny [18] or OTSU [19]) are employed to pre-segment the visually distinct target regions. For polycrystalline, the edge detection method (Canny) is used to extract the boundary of grains; for multiphase images, the threshold method (OTSU) is employed to extract phase re gions. Then, the separated connected domain regions are obtained using the OpenCV library [36], of which the centroid points serve as part of the input to prompt encoder. It should be noted that outlier small regions are removed to eliminate the influence of impurities in the image.

[BLOCK b0039]
Modulation of grid points. Providing the model with opportune points is the prerequisite to segmenting the micrograph correctly. Thus, the grid points are generated to prevent missing regions that may be overlooked during ROI extraction. Specifically, the potential inaccuracies and incompleteness of pre-segmentation, particularly in regions with subtle grayscale differences, necessitate the addition of grid points to compensate for the omission of the centroid points produced by the conventional method. To reduce redundancy, the added grid points too close to the ROI points (<3 pixels) are removed, as detailed in lines 9–15 of the algorithm.

[BLOCK b0040]
In addition, a common issue is that the micrograph exhibits uneven quality caused by unstable light or imaging conditions (See SS and PI-2 images in Fig. 1). To address the problem and cover the ROIs near the edge of the image, MatSAM also generates more dense points in the edge regions (corresponding to $\begin{array} { r } { \mathrm { P o i n t s } _ { \mathrm { e d g e } } = \mathrm { E d } \mathrm { g e } ( I , } \end{array}$ $\mathrm { P o i n t s } _ { \mathrm { g r i d } } )$ in the algo rithm), enhancing the segmentation validity of incomplete objects at edges.

[BLOCK b0041]
Aggregation of points. Fusing the ROI and grid points is straight forward to attain a set of more comprehensive locations. Here, we merge the Points and $\mathrm { P o i n t s } _ { \mathrm { g r i d } }$ set to form $\mathrm { P o i n t s _ { m e r g e } , }$ containing all posi tion information. SAM’s points encoder is reused to map the coordinate into latent embeddings, concretely,

[BLOCK b0042]
$$
P _ {\text { fused }} = \varepsilon_ {\text { point }} (\text { Points } _ {\text { merge }}),\tag{1}
$$

[BLOCK b0043]
where $P _ { \mathrm { f u s e d } }$ is the points embedding of size $N _ { \mathrm { p o i n t s } } \times 2 5 6 ~ ( N _ { \mathrm { p o i n t s } }$ is the number of the merged points) and $\varepsilon _ { \mathrm { p o i n t } }$ represents the points encoder. Hereto, the structure-aware prompt points are obtained through the designed automated strategy, considering most ROIs and imaging fac tors together.

[BLOCK b0044]
2.4. Evaluation protocols

[BLOCK b0045]
As for evaluation, conventional rule-based methods, specialist DL models, and the original SAM were selected to compare to MatSAM. For polycrystalline images (PI-1, PI-2, SS, HEA, LCS), grain boundary masks were extracted from the segmented grain regions using a contourfinding approach, enabling the calculation of discrepancies between different methods and human labels. For multiphase images (DP590–1, DP590–2, NBS-1, NBS-2, AZA, UHCS), phase masks are directly segmented for comparisons. Importantly, MatSAM’s recognition results are all under the training-free condition.

[BLOCK b0046]
The corresponding evaluation settings of 11 datasets are given in

[BLOCK b0047]
Fig. 4. Visual results of MatSAM and rule-based methods on polycrystalline microscopy.

[BLOCK b0048]
Table 1, including input resolution, the main type of microstructure, the number of test images, and evaluation metrics. Four metrics are chosen to demonstrate the performance of recognition: adjusted Rand index (ARI, exclusive for polycrystalline images), Intersection over Union (IoU, exclusive for multiphase images), F1 score, and recall. Higher values of ARI, IoU, and F1 score indicate better recognition perfor mance. Note that all numerical results are given in “mean+SD” form.

[BLOCK b0049]
ARI [37], the corrected-for-chance version of the Rand index (RI), measures the degree to which instances are correctly clustered in a given set, accounting for random chance [38]. The RI, taking values in the range [0,1], is calculated as (TP+TN) / (TP+FP+FN+TN), where TP, TN, FP, and FN are the number of true positives, true negatives, false positives, and false negatives. and the ARI penalizes incorrect classifi cations more heavily than the RI does, namely,

[BLOCK b0050]
$$
\mathrm{ARI} = (\mathrm{RI} - E [ \mathrm{RI} ]) / (\max (\mathrm{RI}) + E [ \mathrm{RI} ]),\tag{2}
$$

[BLOCK b0051]
where E[RI] represents the expected value of the RI, the ARI assigns different weights to correct and incorrect classifications, with a range of [− 1,1]. Image segmentation can be viewed as clustering pixels into segments. In grain boundary segmentation, a class imbalance arises with fewer pixels in boundary regions compared to grains, while boundaries exhibit complex. irregular, and multi-branch structures. The clusterbased ARI metric evaluates segmentation accuracy by comparing clus tering results with ground truth, accounting for random clustering ef fects to ensure unbiased evaluation. This makes ARI well-suited for handling class imbalance and capturing complex topological structures in grain boundary segmentation [15,39]. A higher value indicates greater similarity between the segmentation results and the ground truth.

[BLOCK b0052]
IoU [40] or Jaccard index evaluation metric is a commonly used metric for assessing the performance of object detection and image segmentation models, specifically,

[BLOCK b0053]
$$
\mathrm{IoU} = \mathrm{TP} / (\mathrm{TP} + \mathrm{FP} + \mathrm{FN}),\tag{3}
$$

[BLOCK b0054]
which measures the overlap between the predicted region of the model and the ground truth and is used to assess the model’s localization ac curacy for the target.

[BLOCK b0055]
We conducted extensive quantitative evaluations by comparing the metrics of different methods (ARI, IoU, F1, and Recall), as well as qualitative evaluations through visual comparisons, including over laying segmentation masks and error visualizations. Conventional methods–Canny [18], OTSU [19], and Watershed [41] are implemented for polycrystalline images, and OTSU and adaptive thresholding (Adaptive) [20] for multiphase images. Additionally, for public datasets, the recognition results of MatSAM are directly compared with those of corresponding specialist DL models. All the validation experiments are conducted on a single Nvidia RTX3090 24 GB GPU using the PyTorch 1.13.1 library [42].

[BLOCK b0056]
Performance comparison of MatSAM and other methods on polycrystalline datasets.

[BLOCK b0057]
For the primary metric (ARI), bold and underlined values indicate the best and second-best results, respectively.

[BLOCK b0058]
<table><tr><td rowspan="2">Dataset</td><td rowspan="2">Metric</td><td colspan="5">Method</td></tr><tr><td>MatSAM</td><td>SAM</td><td>Canny</td><td>OTSU</td><td>Watershed</td></tr><tr><td rowspan="3">PI-1</td><td>ARI</td><td>0.62 (±2.4 %)</td><td>0.48(±0.8%)</td><td>0.52(±4.1%)</td><td>0.50(±3.8%)</td><td>0.44 (±4.7%)</td></tr><tr><td>F1</td><td>0.71(±1.6 %)</td><td>0.37(±0.5%)</td><td>0.64(±3.0%)</td><td>0.67(±2.9%)</td><td>0.56 (±3.2%)</td></tr><tr><td>Recall</td><td>0.71(±1.5 %)</td><td>0.86(±1.4%)</td><td>0.86(±3.8%)</td><td>0.79(±3.8%)</td><td>0.63 (±9.2%)</td></tr><tr><td rowspan="3">SS</td><td>ARI</td><td>0.56 (±6.6 %)</td><td>0.54(±1.1%)</td><td>0.34(±7.2%)</td><td>0.23(±5.8%)</td><td>0.24 (±4.3%)</td></tr><tr><td>F1</td><td>0.65(±5.0 %)</td><td>0.66(±1.7%)</td><td>0.51(±7.9%)</td><td>0.46(±5.7%)</td><td>0.41 (±5.6%)</td></tr><tr><td>Recall</td><td>0.59(±6.0 %)</td><td>0.60(±5.5%)</td><td>0.41(±8.2%)</td><td>0.48(±7.9%)</td><td>0.33 (±6.6%)</td></tr><tr><td rowspan="3">HEA</td><td>ARI</td><td>0.59 (±10.8%)</td><td>0.56(±6.0%)</td><td>0.35(±14.3%)</td><td>0.37(±13.3%)</td><td>0.29 (±10.8%)</td></tr><tr><td>F1</td><td>0.35(±11.1%)</td><td>0.52(±11.5%)</td><td>0.42(±13.3%)</td><td>0.41(±11.9%)</td><td>0.39(±10.4%)</td></tr><tr><td>Recall</td><td>0.24(±7.8 %)</td><td>0.43(±9.3%)</td><td>0.33(±10.4%)</td><td>0.34(±9.4%)</td><td>0.33 (±8.7%)</td></tr><tr><td rowspan="3">PI-2</td><td>ARI</td><td>0.75 (±2.0 %)</td><td>0.69(±3.3%)</td><td>0.42(±8.2%)</td><td>0.19(±4.0%)</td><td>0.20 (±4.6%)</td></tr><tr><td>F1</td><td>0.82(±1.7 %)</td><td>0.80(±1.6%)</td><td>0.51(±7.9%)</td><td>0.29(±4.0%)</td><td>0.28 (±5.2%)</td></tr><tr><td>Recall</td><td>0.83(±1.8 %)</td><td>0.81(±1.3%)</td><td>0.45(±9.0%)</td><td>0.26(±5.8%)</td><td>0.24 (±6.5%)</td></tr><tr><td rowspan="3">LCS[11]</td><td>ARI</td><td>0.96 (±3.7 %)</td><td>0.86(±9.8%)</td><td>0.73(±5.3%)</td><td>0.64(±4.3%)</td><td>0.54 (±4.6%)</td></tr><tr><td>F1</td><td>0.96(±3.2 %)</td><td>0.88(±0.7%)</td><td>0.77(±4.8%)</td><td>0.69(±4.3%)</td><td>0.61 (±4.8%)</td></tr><tr><td>Recall</td><td>0.97(±2.5 %)</td><td>0.88(±1.8%)</td><td>0.71(±6.4%)</td><td>0.72(±7.7%)</td><td>0.69 (±4.5%)</td></tr></table>

[BLOCK b0059]
3. Results

[BLOCK b0060]
3.1. Training-free microstructure recognition

[BLOCK b0061]
3.1.1. For polycrystalline microscopy datasets

[BLOCK b0062]
Polycrystalline images typically comprise tightly packed grains, whose boundaries are the target objects of the analysis [43]. As shown in Fig. 4, in some micrographs imaged via OMs, grayscale values vary little between adjacent grains and largely across regions (SS, HEA, and PI-2, see the first column). MatSAM, after receiving structure-aware points, the reasonable prior knowledge of the target regions to the model de livers more accurate and refined recognition results among five datasets (see the third column). On the other hand. threshold methods (OTSU) often suffer from grayscale variations (SS and PI-2, the fourth column).

[BLOCK b0063]
Canny is less affected than threshold methods and can effectively detect most grain boundaries with instinct grayscale differences. However, it is significantly affected by blurred or incomplete grain boundaries (PI-1, SS, and HEA, the fifth column).

[BLOCK b0064]
Table 2 presents the numerical results of the comparison of MatSAM and other methods, including the original SAM and other rule-based methods. Overall, MatSAM achieves the best ARI results across all five datasets, consistently outperforming SAM, which validates the effec tiveness of the automated structure-aware prompt strategy. Addition ally, MatSAM significantly outperforms other conventional methods, as expected.

[BLOCK b0065]
For PI-1, MatSAM achieves an ARI of 0.62 on 59 test images, out performing SAM (0.48) and Canny (the second best, 0.52). The SS dataset, collected under relatively non-ideal imaging conditions with more blurry regions, scratches, and impurities, poses a significant challenge. MatSAM achieves an ARI of 0.56 on 44 test images, out performing SAM (0.54) and Canny (0.34). For HEA micrographs, due to the limited field of view, each image is stitched from multiple smaller ones, resulting in visible horizontal or vertical stitching artifacts caused by brightness variations. Additionally, extensive non-closed grain boundaries and protruding cracks make segmentation particularly challenging. MatSAM achieves an ARI of 0.59, higher than SAM (0.56), and the best rule-based method, OTSU (0.37).

[BLOCK b0066]
On the PI-2 dataset, MatSAM achieves an ARI of 0.75, outperforming SAM (0.69) and Canny (0.42). Uneven lighting, as shown in the fourth row of Fig. 4, leads to fatal false recognition by OTSU and Watershed. For the public LCS dataset, which benefits from good imaging condi tions, MatSAM demonstrates the greatest accuracy, achieving an ARI of 0.96 on 16 test images, compared to SAM (0.86) and other recognition techniques by a large margin. From the visual recognition results, MatSAM not only segments almost all grains in the LCS (see the fifth row of Fig. 4) but also accurately identifies the vast majority of incomplete and blurred grain boundaries. Furthermore, despite the large variation in image resolution within this dataset, MatSAM consistently outputs satisfactory results, demonstrating its strong robustness. This robustness is believed to stem from the combination of structure-aware prior knowledge (provided by rule-based methods) and universal feature representations from SAM.

[BLOCK b0067]
3.1.2. For multiphase microscopy datasets

[BLOCK b0068]
Micrographs of multiphase microstructures contain one or multiple types of phases (the secondary phase, the precipitate, etc.). Unlike grain structures, the phase regions to be segmented do not typically fill the entire image but are irregularly distributed. Also, different phases have conspicuous differences in morphology, structure, and quantity, which can be used to distinguish them after getting the segmented masks.

[BLOCK b0069]
Subjective differences between MatSAM and other methods are shown in Fig. 5. Since the threshold-based Adaptive method performed poorly and lacked reference value, it is not included in the figure. To provide a more comprehensive comparison, we have also included the edge detection results from the Canny and Watershed methods. Overall, the recognition results of MatSAM are the most consistent with the expert labels, significantly outperforming other rule-based methods. MatSAM is capable of effectively identifying phase regions of various sizes in images. For the NBS-2, DP590–2, and UHCS micrographs, MatSAM can most comprehensively identify the small regions in the images (various precipitate phases), whereas the OTSU method suffers from under-segmentation due to the minimal grayscale difference be tween the phase regions and the background.

[BLOCK b0070]
When it comes to AZA, the round circle boundary is unexpectedly detected by methods such as OTSU, Canny, and Watershed. Thi discrepancy can be attributed to the nature of these algorithms. Canny and Watershed, as edge detection methods, are highly sensitive to abrupt intensity changes, making them prone to identifying the circle’s strongly contrasting boundary as a meaningful edge. Similarly, OTSU, due to the circle’s low gray value, likely includes the boundary as part of the foreground during thresholding. Without post-processing to remove noise, these methods tend to over-segment the image. In contrast, MatSAM focuses on identifying meaningful regions rather than abrupt edges, leading to the suppression of this boundary.

[BLOCK b0071]
Fig. 5. Visual results of MatSAM and rule-based methods on multiphase microscopy.

[BLOCK b0072]
Table 3 shows the numerical segmentation results on multiphase microscopy datasets, comparing MatSAM and other methods. On the two dual-phase steel datasets (DP590–1 and DP590–2), martensite precipitates formed during cold and hot rolling are the targets of inter est. For the DP590–1 dataset, it consists of 23 hot-rolled martensitic precipitate images with relatively low definition. The precipitates exhibit low gray values and are contoured by black boundaries, with most appearing more blurred compared to the cold-rolled DP590–2 dataset (see Fig. 1), making them more difficult to distinguish. Among conventional methods, OTSU achieves an IoU of 0.64, while SAM ach ieves an IoU of 0.75. However, both results are significantly lower than MatSAM’s IoU of 0.77, which is 13.0 % higher than OTSU and out performs SAM by 2.0 %. For the DP590–2 dataset, martensite pre cipitates appear as light white streaks in the images. The IoU between MatSAM-segmented masks and annotations is 0.82, which is observ ably higher than the SAM method (0.68) and the OTSU threshold method (0.66).

[BLOCK b0073]
3.1.3. For public microscopy datasets

[BLOCK b0074]
To validate the zero-shot generalizability of MatSAM across broader scenarios, we performed comparative experiments with conventional approaches and specialist models on 4 materials microscopy test data sets released by previous works, including NBS-1 and NBS-2 (corre sponding to Super-2 and Super-4 in the original article) [16], AZA [25], and UHCS [11]. The quantitative results are given in Table 3. LCS [11] is analyzed qualitatively in Fig. 6 due to the lack of released labels. As shown in Table 3, compared to specialist models, MatSAM acquired the best results on three datasets—NBS-1, NBS-2, and UHCS—and ranked second on AZA, slightly lower than the specialist method.

[BLOCK b0075]
NBS-1 and NBS-2 contain multiple precipitates of significantly different sizes. The tertiary precipitates are particularly small and blurry, making recognition challenging. MatSAM achieves an IoU of 0.91 on NBS-1, outperforming SAM (0.85) and the specialist model (0.77); it also scores 0.82 on NBS-2, 3.0 % higher than the specialist model. Regular matrix and secondary precipitates are well recognized with few phase contour distortions. For smaller and blurred tertiary precipitates with low contrast, MatSAM also exhibits better perfor mance, as shown in the first column of Fig. 6 (yellow arrows highlight regions where MatSAM correctly segments areas that the original method under-segments). When tested on unseen images without fine tuning, the recognition performance of the specialist model dropped significantly. In contrast, when handling the same diverse unseen im ages, MatSAM can surpass their results without additional training, underscoring its superior efficiency and adaptability.

[BLOCK b0076]
AZA comprises two XCT (X-ray computed tomography) images of AlZn dendrite, with the dark precipitate phase in the foreground, located in the center of the circular region to be segmented. For this simple task, dendrites are accurately extracted (see the second column of Fig. 6), achieving an IoU of 0.96, which approaches 0.97 of the corresponding specialist model trained on over 1000 annotated image samples. Be sides, for the UHCS dataset, which contains numerous light-colored precipitates (spheroidite particles) uniformly distributed on the top surface of a rough alloy crack, MatSAM attains 0.76, outperforming the specialist model by 5.0 %, with the vast majority of cementite particles correctly identified and segmented. Due to the complex background and large grayscale differences, SAM, OTSU, and Adaptive methods perform poorly on this dataset, with IoU scores of 0.58, 0.56, and 0.46, respec tively. Additionally, for polycrystalline images of LCS (the fourth column of Fig. 6), MatSAM demonstrates a comparable recognition performance to the original method without human intervention.

[BLOCK b0077]
Performance comparison of MatSAM and other methods on in-house and public and multiphase datasets.

[BLOCK b0078]
For the primary metric (IoU), bold and underlined values indicate the best and second-best results, respectively.

[BLOCK b0079]
<table><tr><td rowspan="2">Dataset</td><td rowspan="2">Metric</td><td colspan="5">Method</td></tr><tr><td>MatSAM</td><td>SAM</td><td>OTSU</td><td>Adaptive</td><td>Specialist method</td></tr><tr><td rowspan="3">DP590-1</td><td>IoU</td><td>0.77 (±8.2 %)</td><td>0.75(±13.4%)</td><td>0.64(±9.7%)</td><td>0.48(±5.3 %)</td><td>/</td></tr><tr><td>F1</td><td>0.79(±8.3%)</td><td>0.85(±9.2%)</td><td>0.68(±11.3%)</td><td>0.49(±8.9 %)</td><td>/</td></tr><tr><td>Recall</td><td>0.81(±14.7%)</td><td>0.66(±26.0%)</td><td>0.91(±8.6%)</td><td>0.65(±10.0%)</td><td>/</td></tr><tr><td rowspan="3">DP590-2</td><td>IoU</td><td>0.82 (±3.1 %)</td><td>0.68(±6.7%)</td><td>0.66(±1.3%)</td><td>0.28(±0.9%)</td><td>/</td></tr><tr><td>F1</td><td>0.84(±3.2%)</td><td>0.81(±4.8%)</td><td>0.66(±2.0%)</td><td>0.17(±2.1 %)</td><td>/</td></tr><tr><td>Recall</td><td>0.80(±4.9%)</td><td>0.81(±2.1%)</td><td>0.58(±2.7%)</td><td>0.22(±1.9 %)</td><td>/</td></tr><tr><td rowspan="3">NBS-1[16]</td><td>IoU</td><td>0.91 (±1.2 %)</td><td>0.85(±7.6%)</td><td>0.75(±3.2%)</td><td>0.45(±1.6 %)</td><td>0.77</td></tr><tr><td>F1</td><td>0.96(±0.4%)</td><td>0.91(±4.6%)</td><td>0.86(±3.6%)</td><td>0.52(±1.9 %)</td><td>-</td></tr><tr><td>Recall</td><td>0.94(±0.4%)</td><td>0.89(±6.5%)</td><td>0.87(±8.4%)</td><td>0.38(±1.9%)</td><td>-</td></tr><tr><td rowspan="3">NBS-2[16]</td><td>IoU</td><td>0.82 (±6.3 %)</td><td>0.81(±6.1%)</td><td>0.67(±14.1%)</td><td>0.52(±9.2 %)</td><td>0.79</td></tr><tr><td>F1</td><td>0.89(±4.9%)</td><td>0.90(±3.8%)</td><td>0.80(±9.4%)</td><td>0.62(±9.8%)</td><td>-</td></tr><tr><td>Recall</td><td>0.84(±8.8%)</td><td>0.84(±9.0%)</td><td>0.79(±7.8%)</td><td>0.53(±10.8%)</td><td>-</td></tr><tr><td rowspan="3">AZA[25]</td><td>IoU</td><td>0.96(±0.6%)</td><td>0.73(±6.8%)</td><td>0.89(±1.2%)</td><td>0.61(±2.3%)</td><td>0.97</td></tr><tr><td>F1</td><td>0.96(±0.5%)</td><td>0.84(±4.5%)</td><td>0.88(±1.7%)</td><td>0.48(±5.8 %)</td><td>-</td></tr><tr><td>Recall</td><td>0.96(±0.9%)</td><td>0.96(±0.5%)</td><td>0.97(±0.1%)</td><td>0.76(±3.2%)</td><td>-</td></tr><tr><td rowspan="3">UHCS[11]</td><td>IoU</td><td>0.76 (±0.7 %)</td><td>0.58(±8.2%)</td><td>0.56(±3.1%)</td><td>0.46(±3.5%)</td><td>0.71</td></tr><tr><td>F1</td><td>0.75(±0.9%)</td><td>0.73(±6.6%)</td><td>0.72(±2.5%)</td><td>0.43(±5.6%)</td><td>-</td></tr><tr><td>Recall</td><td>0.78(±2.7%)</td><td>0.77(±3.3%)</td><td>0.59(±3.2%)</td><td>0.93(±1.3 %)</td><td>0.88</td></tr></table>

[BLOCK b0080]
3.2. Microstructure recognition in complex scenarios

[BLOCK b0081]
While validating MatSAM’s capabilities, we observed that even in challenging scenarios involving complex, variable, and difficult-to interpret micrographs, MatSAM consistently provided reasonable out puts. This effectiveness is illustrated through examples from poly crystalline and multiphase images (See Fig. 7).

[BLOCK b0082]
The common issue for grains in the images is that incompleteness o non-closing occurs on the boundary, as marked on the left in Fig. 7, often due to uneven or incomplete etching during the preparation process. Most untailored approaches underperform in the situation, causing under-segmentation and further affecting statistical fidelity. By contrast, MatSAM mitigates this problem, as exemplified in (b); the grain boundaries in the region indicated by the arrow are nearly invisible, yet MatSAM can still infer the missing parts. We believe this is due to SAM’s extensive pre-training on a vast number of images, which has enabled it to effectively capture the characteristics and patterns of such imaging. Combined with the optimized point prompt in MatSAM, it can detect that a corresponding boundary should exist in this region based on the pixel distribution surrounding the area. Also, in (d), some boundaries are hard to tell at the grain interfaces. Nevertheless, MatSAM captures and reasonably recognizes the subtle changes near the boundaries, demonstrating the flexibility of MatSAM when handling this pervasive and troublesome challenge.

[BLOCK b0083]
For multiphase images from (e) to (h), with phase regions containing tiny holes (e), target phase boundaries intermingled with surrounding areas (f), precipitate sizes differing amongst large, medium, and small (g), and small-sized particles scattered throughout the image (h), Mat SAM ideally identifies the difficult areas. The designed structure-aware prompt strategy enables MatSAM to recognize target regions of varying sizes without labeling accurately. This capability is highly beneficial for automated phase detection and quantitative analysis.

[BLOCK b0084]
4. Discussion

[BLOCK b0085]
4.1. Effectiveness of MatSAM

[BLOCK b0086]
SAM [30] excels at extracting general features due to extensive pre-training but exhibits suboptimal performance on micrographs, where grayscale variations dominate. Besides, SAM’s foreground bias, which stems from pre-training on sparse distinct targets within natural scene images [31], does not align with the imaging features of micro scopy. While SAM performs well with human-provided prompts, its ef ficiency diminishes for large-scale tasks. MatSAM addresses these challenges and transfers the general capability of SAM to microscopy scenarios by automating prompt point generation. Using rule-based methods and optimizing grid points to guide the mask decoder effec tively, our approach thereby better handles various micrographs better.

[BLOCK b0087]
To evaluate the effectiveness of the automated structure-aware prompt strategy, we conducted comparative validation experiments against the original SAM method on representative SEM and XCT images from DP590–2 and AZA datasets, respectively. Three common types of noise frequently encountered in microscopic images—salt-and-pepper (S&P) noise, speckle noise, and Gaussian noise—were selected [44,45] and introduced into the images using the random noise generation function from the sci-kit image [46] library. The robustness of MatSAM compared to SAM was further investigated under varying levels of these noise types. Fig. 8 presents the comparative results of two microscopic images with varying levels of S&P noise processed by each method (details for the other two types of noise are provided in Supplementary Note 1). The noise levels were adjusted by the variance (Var. = 0.01, 0.05, 0.1, 0.2).

[BLOCK b0088]
Overall, MatSAM demonstrates better recognition accuracy (both subjective and objective) on images with varying levels of noise compared to SAM, identifying more target regions. Additionally, the introduction of noise exacerbates the uncertainty of both methods in recognizing prominent regions within the images. The boundaries of the target regions become increasingly blurred and more easily confused with the background, which has a more detrimental impact on micro scopic images—characterized by inherently lower contrast compared to natural scene images. MatSAM’s IoU on DP590–2 images decreases from 0.822 to 0.549 (SAM drops from 0.768 to 0.485), while on AZA images, the IoU declines from 0.946 to 0.815 (SAM drops from 0.903 to 0.776). As noise intensity increases, under-segmentation gradually becomes the dominant type of error, leading to a significant decline in accuracy for both methods. These results highlight the challenge of noise in micro scopic image segmentation and demonstrate MatSAM’s relative robustness in maintaining higher accuracy compared to SAM.

[BLOCK b0089]
Fig. 6. Visual results of MatSAM and other specialist models. The first row shows open-sourced images: (a) NBS-2 [16], (b) AZA [25], (c) UHCS [11], and (d) LCS [11]. The second row displays the results of MatSAM, while the third row presents the results from data-specific models (the mask images are cropped from the raw figures in their respective articles). We adopt the color styles from each article: for the results of (a) and (b), pink and blue represent under- and over-segmentation, respectively; for (c), pink areas are the masks.

[BLOCK b0090]
4.2. Efficiency of MatSAM

[BLOCK b0091]
Given MatSAM’s effective segmentation capability without the need for training, we believe it, as an out-of-the-box tool, has the potential to significantly accelerate the process in real-world quantitative charac terization of material microstructures. We qualitatively compared several common modes conducted by researchers for microstructure extraction tasks, elaborated in Fig. 9. These include "fully manual annotation (Mode 1)," "rule-based methods with manual correction (Mode 2)," "learning-based methods with manual correction (Mode 3)," and "visual large models with manual correction (Mode 4).'

[BLOCK b0092]
Mode 1: this mode has the longest time cost, and due to the sub jective influence of annotators, the final annotation accuracy may be affected detrimentally. Mode 2: while the runtime for general rulebased methods is minimal, significant time is often required to adjust the algorithm’s hyperparameters for new images to accommodate their visual characteristics. The complexity of the images also necessitates manual intervention for corrections, which can be time-consuming. Mode 3: researchers typically annotate a batch of data, followed by training with DL methods. The trained model is then applied to the full dataset to generate predictions, which are followed by manual adjust ments to finalize the outputs. Compared to the first two modes, this approach significantly reduces time costs while improving accuracy, both during model development and the manual correction phase. This is currently the most widely adopted approach, though it still demands substantial time and resources. Mode 4: by using an improved version of a general-purpose visual model, such as MatSAM, researchers can perform full inference on all images without adjusting method param eters. While MatSAM’s inference time per image is longer than that of classical deep learning methods and traditional methods, it requires no additional effort for model training or annotation. The segmentation results are almost immediately usable without extensive modification, allowing researchers to obtain high-quality recognition results in a significantly shorter time with minimal effort.

[BLOCK b0093]
For normal micrographs, segmentation masks generated by MatSAM can meet the accuracy requirement for subsequent descriptive statistics. MatSAM can replace conventional or DL-based methods as a segmenter in challenging scenarios at inconsistent imaging conditions and various structures to give a more reliable initial result, e.g., continuous threedimensional (3D)-slice images acquired by serial sectioning techniques [47–49]. Then, the false-segmented regions are corrected for mode training through interactive correction involving human intervention. Empirically, it usually takes about 45 min to pre-segment and manually correct a microscopic image with approximately 300 grains using con ventional methods. This process is highly susceptible to the operator’s subjective biases. In contrast, using MatSAM can reduce the delineation plus correction time to within 5 min. The essential reason is that the initial results from MatSAM are already precise enough to identify and segment most grains. The operator only needs to correct the over- or under-segmentation regions caused by distinct defects or image blur ring, less susceptible to visual fatigue and distraction.

[BLOCK b0094]
In general, MatSAM’s efficiency can be attributed to the following two factors: First, because SAM has already extensively learned

[BLOCK b0095]
Raw image

[BLOCK b0096]
MatSAM

[BLOCK b0097]
Raw image

[BLOCK b0098]
Fig. 7. Illustration of MatSAM segmenting microstructures under different morphologies. The left is polycrystalline images, and the right is multiphase images. (a) PI-1, (b) HEA, (c) SS. (d) PI-2, (e) DP590–2, (f) DP590–1, (g) NBS-1, and (h) UHCS. Arrows point to noteworthy areas (a pair of arrows shares the same color)

[BLOCK b0099]
universal image features, there is no need for additional feature learning or selection when applied to material micrographs. Second, MatSAM leverages conventional methods to direct the model’s attention to ROIs. Since this step only requires a rough estimation of potential regions and does not demand high precision, there is no need to modify the model for specific image types. Therefore, MatSAM can serve as a powerful and fast tool for microscopy analysis, accelerating quantitative characterization.

[BLOCK b0100]
4.3. Extensibility of MatSAM

[BLOCK b0101]
MatSAM’s extensibility or generalizability enables accurate and robust recognition of various microstructures at different scales and morphologies within a single micrograph. To elucidate that, we con ducted extended experiments on six additional micrographs, extracting corresponding microstructures, i.e., NBS-3 (γ’ phase), NBS-3 (TCP phase), IN939–1 (melted pool boundary), IN939–2 (cracks), C22000 and C21000 brasses (twin grain) [50]. These image samples are not provided with corresponding annotations. Fig. 10, which demonstrates MatSAM’s capability to identify different phases and key microstruc tures. See Supplementary Note 2 for results on a wider variety of images.

[BLOCK b0102]
For micrographs of NBS-3, as shown in (a) and (b) of the figure, γ (small light grey areas) and TCP phases (fine needle-like) are the key objects of the analysis. Additionally, impurities, which are deeply dark in color and distinctly larger in area, are also present. MatSAM accu rately recognizes all phases, as illustrated in the Overlay columns. For micrographs of superalloy IN939–1 and IN939–2, shown in (c) and (d) of the figure, the melted pool boundary and crack are the main focus. The boundaries of melted pools and crack regions are reasonably recognized and clearly separated. For micrographs of brasses, commercial bronze (C22000) and gilding metal (C21000) shown in the (e) and (f) of the image, the twin grains—characterized by straight or planar boundaries and contrasting regions—are the primary components of interest.

[BLOCK b0103]
MatSAM, prompted by structure-aware points, segments nearly all the mentioned phases. Following the recognition process, each type of microstructure can finally be extracted by filtering all generated masks based on their morphological features, such as area, color distribution, orientation, and shape characteristics. As shown in the Key structure columns of the figure, the binary mask results of the corresponding ROIs are precisely separated. Consequently, researchers can launch autono mous parameter calculations and further statistical analyses without concerning themselves with the annotation and training processes.

[BLOCK b0104]
Fig. 8. Visual results of MatSAM and SAM on micrographs with different levels of S&P noise. Pink and blue regions represent under- and over-segmentation, respectively. (a) Results visualization on an SEM image from the dual-phase steel dataset (DP590–2). (b) Results visualization on an XCT image from AlZn alloy dataset (AzA)

[BLOCK b0105]
4.4. Limitations of MatSAM

[BLOCK b0106]
Despite the significant advancements achieved by MatSAM in ma terial microstructure extraction tasks, several limitations persist that merit further exploration. First, MatSAM exhibits limitations in handling highly noised micrographs with smaller scales, particularly in

[BLOCK b0107]
Key structure (d) Overlay (b) NBS-3 (nickel-based superalloy) TCP phase Fig. 9. Comparison of four modes of microstructure extraction.

[BLOCK b0108]
Image

[BLOCK b0109]
(c) IN939-1 (nickel-based superalloy) melted pool boundary

[BLOCK b0110]
Fig. 10. Examples of extracting different microstructures. (a) NBS-3 (γ’ phase), (b) NBS-3 (TCP phase), (c) IN939–1 (melted pool boundary), (d) IN939–2 (cracks). (e) C22000 brass (twin grain), and (f) C21000 brass (twin grain). On each side, the first column displays raw images: the second column shows segmentation masks overlaying the raw images for better visualization; the third column presents binary images highlighting different phases (foreground).

[BLOCK b0111]
challenging scenarios with inconspicuous targets, substantial noise, and fine atomic details. For the example in (a) of Fig. 11, on HRTEM images of gold nanoparticles, the model fails to comprehensively extract mul tiple particles, likely due to the size disparity between small atomic features and the overall region, as well as variations in atomic orienta tions within individual particles. These factors reduce mask confidence and lead to severe under-segmentation, highlighting MatSAM’s diffi culty in effectively handling fine-grained and noisy datasets.

[BLOCK b0112]
Fig. 11. Demonstrations of limitations of MatSAM. (a) the failure example on the HRTEM image of gold nanoparticles. (b) the process of filtering target twin grain regions on the brass micrograph.

[BLOCK b0113]
Inference time and corresponding segmentation performance of MatSAM and other methods on public LCS and NBS-1 datasets.

[BLOCK b0114]
Bold values indicate the best results.

[BLOCK b0115]
<table><tr><td>Dataset</td><td>Method</td><td>Metric</td><td>Segmentation performance</td><td>Inference time per image (ms)</td></tr><tr><td rowspan="5">LCS (1360 × 600)(Polycrystalline)</td><td>Watershed</td><td>ARI</td><td>0.54</td><td>6.12</td></tr><tr><td>OTSU</td><td></td><td>0.64</td><td>4.54</td></tr><tr><td>Canny</td><td></td><td>0.73</td><td>16.48</td></tr><tr><td>SAM</td><td></td><td>0.86</td><td>1850.35</td></tr><tr><td>MatSAM</td><td></td><td>0.96</td><td>1926.35</td></tr><tr><td rowspan="4">NBS-1 (512 × 512)(Multiphase)</td><td>OTSU</td><td>IoU</td><td>0.75</td><td>0.53</td></tr><tr><td>Adaptive</td><td></td><td>0.45</td><td>0.58</td></tr><tr><td>SAM</td><td></td><td>0.85</td><td>1575.24</td></tr><tr><td>MatSAM</td><td></td><td>0.91</td><td>1812.67</td></tr></table>

[BLOCK b0116]
Second, even though MatSAM performs well in binary foreground background segmentation tasks, delivering accurate and efficient re sults for identifying regions most relevant to the analysis, it should be acknowledged that for images with relatively complex semantic com ponents, further post-processing is often required to extract specific targets. As shown in (b) of Fig. 11, in segmenting brass micrographs, parameters like circularity, contour geometry, area, and grayscale range were calculated for each mask. By setting tailored filtering conditions, elongated twin grains are effectively distinguished. This reliance on additional semantic filtering underscores a limitation of MatSAM in addressing more intricate segmentation demands.

[BLOCK b0117]
Lastly, while MatSAM achieves impressive segmentation accuracy, it comes at a higher computational cost, as shown in Table 4. On the LCS dataset, it achieves an ARI score of 0.96 with an inference time of 1926.35 ms per image, compared to OTSU’s 4.54 ms. Similarly, on the NBS-1 dataset, our method obtains the highest IoU score of 0.91 but requires 1812.67 ms. Although its high accuracy significantly reduces the need for manual corrections, the trade-off in inference speed pre sents challenges for real-time applications, emphasizing the need for further optimization.

[BLOCK b0118]
5. Conclusion

[BLOCK b0119]
In this study, a novel training-free approach, MatSAM, was proposed to efficiently extract material microstructures based on SAM. Without the need for manual annotations, it precisely identified 11 kinds of material microstructures. Combining two key metrics, ARI (for poly crystalline images) and IoU (for multiphase images), MatSAM achieved an average relative improvement of 35.4 % over the best-performing conventional rule-based methods and 13.9 % over the original SAM. On four public microstructure segmentation datasets of various mate rials—nickel-based superalloys (NBS-1/2), ultrahigh carbon steel (UHCS), and AlZn alloy (AZA)—the average IoU attained by MatSAM was 7.5 % higher than that of the corresponding specialist DL models. The proposed MatSAM tackles the challenge of high time and labor costs in the quantitative characterization of microstructures. Meanwhile. it has obtained improved generalization capability, enabling a single model to be reused for different microstructures, including grain boundaries, phases, and defects. The methodology and empirical results of this study deliver a new perspective on addressing key challenges in large-scale, automated microstructural information extraction.

[BLOCK b0120]
Data availability

[BLOCK b0121]
The test data of publicly released datasets can be found in the referenced articles or our code repository: https://github.com/ USTB-AI3DVIP/matsam. All the raw data of in-house datasets are stored at the University of Science and Technology Beijing and are available upon request from the corresponding author. The source code of this work is available in this repository: https://github.com/

[BLOCK b0122]
USTB-AI3DVIP/matsam.

[BLOCK b0123]
CRediT authorship contribution statement

[BLOCK b0124]
Changtai Li: Writing – original draft, Methodology, Formal analysis, Conceptualization. Xu Han: Writing – original draft, Validation, Inves tigation, Data curation. Chao Yao: Writing – review & editing, Valida tion. Yu Guo: Writing – review & editing, Conceptualization. Zixin Li: Resources, Data curation. Lei Jiang: Writing – review & editing. Wei Liu: Resources, Data curation. Haiyou Huang: Writing – review & editing, Data curation. Huadong Fu: Writing – review & editing, Su pervision, Resources, Conceptualization. Xiaojuan Ban: Writing – re view & editing, Supervision, Project administration.

[BLOCK b0125]
Declaration of competing interest

[BLOCK b0126]
The authors declare that they have no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.

[BLOCK b0127]
Acknowledgments

[BLOCK b0128]
This work is supported by the National Major Science and Technol ogy Projects of China (2024ZD0608100), the National Natural Science Foundation of China (52425409, U22A2022, 62332017, 62303043), and Xiaomi Young Scholars Program.

[BLOCK b0129]
Supplementary materials

[BLOCK b0130]
Supplementary material associated with this article can be found, in the online version, at doi:10.1016/j.actamat.2025.120962.

[BLOCK b0131]
References
