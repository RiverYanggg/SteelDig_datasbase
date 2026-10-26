[BLOCK b0001]
Full Length Article

[BLOCK b0002]
Deciphering the composition-microstructure correlation in low-density FeMnAlC steels with machine learning

[BLOCK b0003]
Peng Tiexu <sup>a,1</sup>, Yu Haoyang <sup>a,1</sup>, Huang Jiaxin <sup>a,1</sup>, Fang wei <sup>a,\*</sup>, Li Cong <sup>a</sup>, Yao Zitong Zhang Xin <sup>a</sup>, Feng Jianhang <sup>a</sup>, Ji Puguang <sup>a,b</sup>, Xia Chaoqun <sup>a</sup>, Yu Hui <sup>a</sup>, Yin Fuxing <sup>a,c</sup>

[BLOCK b0004]
<sup>a</sup> Tianjin Key Laboratory of Materials Laminating Fabrication and Interface Control Technology, School of Materials Science and Engineering, Hebei University of Technology, Tianjin 300132, China

[BLOCK b0005]
<sup>b</sup> Xuzhou Jihua Metal Material Technology Co., Ltd., Xuzhou 221100, China

[BLOCK b0006]
<sup>c</sup> Institute of New Materials, Guangdong Academy of Science, Guangzhou 510651, China

[BLOCK b0007]
A R T I C L E I N F O

[BLOCK b0008]
Keywords: Fe-Mn-Al-C alloy Compositional design κ-carbide Machine-learning

[BLOCK b0009]
A B S T R A C T

[BLOCK b0010]
FeMnAlC steels have been regarded as prospective candidates for the advanced high-strength steel with reduced density. However, the correlation between the complex steel composition and the resulting microstructure re mains unclear. This study presents a robust and efficient approach for establishing the correlation between the composition and microstructure of low-density FeMnAlC steel using a machine learning algorithm. By employing classification and regression models, we successfully predicted four significant characteristics: the existence of the κ phase, a dual-phase region (γ + κ) at the aging temperature, a solitary γ phase region, and the volume fraction of the κ phase. Notably, the elements Al and C, with a particular emphasis on Al, exert significant in fluence on the phase structure. For example, when the Mn element content is 30 wt%, an estimated minimum Al content of around 4 wt% is required to guarantee the existence of the κ phase. Furthermore, the anticipated content range of Al and C required for the existence of the (γ + κ) duplex region at the aging temperature spans from 4.5 to 9.3 wt% and 0.4 to 1.1 wt%, respectively. Ultimately, the Fe-30Mn-8Al-1C steel was chosen for experimental validation, and the predicted characteristics exhibited excellent agreement with the experimental results. Our research offers a roadmap for the development of low-density steel. and the approach we devised holds promise for application in other metallic materials as well.

[BLOCK b0011]
1. Introduction

[BLOCK b0012]
The use of low-density steel in the automotive industry is known to enhance fuel efficiency and decrease carbon dioxide emissions [1–4]. However, steel must possess advantageous mechanical properties, such as high formability, recyclability, and low cost to be commonly utilized in this sector. Among all lightweight materials, FeMnAlC austenitic lowdensity steels are highly attractive as they offer a superior combination of specific strength, ductility, and fatigue properties. Hence, it is a body structure material with great potential. researchers have shown a growing interest in their development with high strength and low density.

[BLOCK b0013]
The microstructure of FeMnAlC low density steel varies with the alloy composition. The principal alloy elements utilized in the produc tion of low-density steels are manganese (Mn), aluminum (Al), and carbon (C). Incorporating Al into FeMnAlC steels can decrease C diffu sivity, promote the formation of a protective alumina layer (Al O ), and stabilize the α phase [5–8]. α phase (α-ferrite) is a slender strip, which undergoes continuous and orderly transformation during aging and becomes a B2 or DO3 intermetallic compound [4,5]. Moreover, the addition of Al improves the stacking fault energy (SFE) of the FeMnAlC system, which curbs the transformation from the austenitic γ to ε phase [5,6]. This ultimately results in a reduction in steel density by decreasing the material’s average molar mass and lattice expansion [9,10]. Mn enhances γ phase stability by raising the FCC lattice parameter and impeding additional ferrite formation caused by Al inclusion [5,7]. Nevertheless, an excessive amount of Mn can lead to the formation of the brittle β-Mn phase [11]. Typically, the inclusion of β-Mn precipitates leads to a substantial increase in steel strength but a reduction in plas ticity [12]. The presence of β-Mn precipitates also tends to induce brittle fractures within the FeMnAlC system, resulting in diminished impact energy [4,5]. Meanwhile, carbon stabilizes the γ phase and encourages the precipitation of the κ phase, thus maintaining the steel’s mechanical properties. FeMnAlC austenitic steels have been observed to form a metastable phase of coherent ordered precipitate called the κ-carbide (κ-phase) within their austenite grains [3,14]. It has been indicated that the aging of coherent, nanosized κ-carbides is primarily impacted within the intermediate temperature range of 500-600 ℃. During force defor mation, κ-carbides are sheared by dislocations belonging to the {1 11} 〈1 1 0〉 slip system, while dislocation bypassing can also occur [15]. The microstructure of FeMnAlC austenitic low-density steel remains stable, exhibiting an exceptional blend of strength and toughness, attributed to its remarkable strain hardening capability and the κ carbide precipitation strengthening mechanism [4,5]. Thus, the study of the κ phase is pivotal for FeMnAlC austenitic low-density steels. The literature reports that the composition of FeMnAlC austenitic low-density steels usually ranges from 18-30 wt% Mn, 8–12 wt% Al, and 0.6–1.8 wt% C [1,3,7,16–18]. With over 100,000 possible candidate compositions for steel, it is practically impossible to experimentally test each one.

[BLOCK b0014]
Fig. 1. Framework of the design process of the low-density Fe–Mn–Al–C austenitic steels by machine learning.

[BLOCK b0015]
Utilizing calculation methods based on material properties to opti mize the material design process enhances efficiency and lowers costs. FeMnAlC systems are characterized by a range of constituent element and complex phase structures, making the implementation of molecular dynamics and density functional theory potentially time-consuming. As a result, a novel approach is necessary to efficiently and accurately forecast the phase properties that correspond to low-density steel com positions in the FeMnAlC system. In recent years, the data-driven ma chine learning assisted design of new materials has gained significant attention [19–22]. The machine learning process involves the creation of a mathematical model based on the characteristics and features of computational or experimental data [23]. The process consists of three primary steps: dataset construction, model building, and model evalu ation [24]. The creation of an optimized model enables the efficient design of candidates that satisfy the design requirements and provide good prediction performance. Based on the predicted results, experi mental testing follows to validate the material’s performance. Steel, being a widely used structural material. plays a fundamental function in supporting our industries and livelihoods [25–27]. The challenge of designing steel materials using traditional trial-and-error approaches is further complicated because of its lengthy development history [25], mature process, and numerous processing parameters. Machine learning offers a solution to this challenge by facilitating the design process through the establishment of a complex relationship between produc tion processes and steel material performance [28–30]. This approach has been extensively used in designing steel materials; for instance, the relationship between the composition, treatment process, and tensile properties of reduced activation ferritic/martensitic (RAFM) steels [31] was established using the machine learning method. Ultimately, the model, which was trained with random forest regressors, conclusively confirmed the effects of tempering temperature and C content on the yield strength of RAFM steels.

[BLOCK b0016]
Hence, for a precise and effective examination of phase properties associated with the composition of low-density steel in the FeMnAlC system, the data-driven alloy design method offers distinct advantages. This study introduces a methodology for establishing the connection between the intricate composition and the microstructure traits of FeMnAlC austenitic low-density steel through the utilization of machine learning algorithms. This method mainly predicts the complex compo sition and corresponding phase structure of FeMnAlC system lowdensity steel, and achieves the purpose of directional selection of com ponents and phase structure. Multiple machine learning algorithms were employed to establish predictive models based on four significant steel features: the existence of κ precipitates, a (γ + κ) two-phase area, a single γ phase area, and a substantial volume fraction of κ. Subsequently, the best models were selected to optimize the design of FeMnAlC austenitic low-density steel, guaranteeing the steel possessed κ precipitates, a (γ + κ) dual-phase region, a single γ phase area, a high volume fraction of the κ phase, and lower density relative to conventional steel. Furthermore, relationships between the four features and chemical composition were established. The model-predicted outcomes for the FeMnAlC single phase austenitic low-density steel were discovered to approximate experimental test properties. Lastly, material limitation conditions were incorporated into a larger component space to achieve the preferred material orientation design.

[BLOCK b0017]
2. Methods

[BLOCK b0018]
2.1. Design process

[BLOCK b0019]
We propose a novel machine learning-based design strategy aimed at expediting the development of low-density Fe-Mn-Al-C austenitic steels. Fig. 1 illustrates the framework the design process, focused on estab lishing the correlation between the composition of low-density steel and its microstructure characteristics.

[BLOCK b0020]
The design process involves constructing predictive models using machine learning for four significant steel features. Classification models predict the existence of the κ phase (Y ), and the main purpose is the significant precipitation-strengthening effect of the κ phase. A (γ + κ) dual-phase area at 500–600 <sup>◦</sup>C (Y ), and the main purpose is to exclude the influence of other phase structures on the system. A single γ phase area (Y ), and the main purpose is that the single γ phase area is convenient for deformation processing. Regression models predict the volume fraction (Y ) of the κ phase, and a higher κ-phase volume frac tion generally gives the system better mechanical property potential. Although the precipitation size and distribution of the κ phase have an important influence on the performance of the system, they can be regulated by a suitable heat treatment process. Once the database is complete, our research scope will extend to include factors such as kappa phase size, morphology, and location. The steel density is then calculated using an empirical formula. The predictive models for these attributes are combined with the empirical density formula. Possible candidates are filtered based on the design requirements for different steel properties. The predicted results are verified through experimental testing. If the experimental results show a significant deviation from the predicted results, the model is altered to improve accuracy based on the new test data. Ultimately, an integrated model can successfully design low-density Fe-Mn-Al-C austenitic steels with good properties.

[BLOCK b0021]
Table 1 Original six input features used in machine learning model.

[BLOCK b0022]
<table><tr><td>Descriptor</td><td>Formula</td><td>Ref.</td></tr><tr><td>valence electron concentration (VEC)</td><td> $VEC = \sum_{i=1}^{n} c_i VEC_i$ </td><td>[32]</td></tr><tr><td>melting point (Tm)</td><td> $\Delta T_m = \sum_{i=1}^{n} c_i T_{mi}$ </td><td>[33]</td></tr><tr><td>entropy of mixing ( $\Delta$ Smix)</td><td> $\Delta S_{mix} = -R \sum_{i=1}^{n} c_i \ln(c_i)$ </td><td>[32]</td></tr><tr><td>enthalpy of mixing ( $\Delta$ Hmix)</td><td> $\Delta H_{mix} = 4 \sum_{i \neq j}^{n} c_i c_j H_{ij}$ </td><td>[34]</td></tr><tr><td>Pauli electronegativity difference ( $\Delta \chi$ )</td><td> $\overline{\chi} = \sum_{i=1}^{n} c_i r_i, \Delta \chi = \sqrt{\sum_{i=1}^{n} c_i (\overline{\chi} - \chi_i)^2}$ </td><td>[35]</td></tr><tr><td>atomic size difference ( $\delta$ )</td><td> $\delta = \sqrt{\sum_{i=1}^{n} \sum_{j>i}^{n} c_i c_j (1 - \frac{r_i + r_j}{2\bar{r}})^2}$ </td><td>[36]</td></tr></table>

[BLOCK b0023]
2.2. Machine learning

[BLOCK b0024]
2.2.1. Dataset

[BLOCK b0025]
To optimize the design of low-density austenitic steels containing iron, Mn, Al, and $\mathrm { C } ,$ the (100-x-y-z)Fe-xMn-yAl-zC family was chosen as the system of interest. The potential composition space was defined according to the following parameters (the element content is the mass percentage): $1 0 \% \leq \mathbf { x } \leq 3 0 \% , 2 \% \leq \mathbf { y } \leq 1 2 \% ,$ , and $0 . 2 \% \leq \mathbf { z } \leq 2 \% .$ . The dataset for this study included information from historical literature sources $[ 1 , 3 , 7 , 1 6 , 1 7 ]$ as well as phase balance data obtained using the JMatPro v9.0 general steel database. Considering the physical and chemical properties of the system and the binding force between the atoms, the descriptor of the machine learning calculation needs to be selected. Six input features or descriptors (See Table 1 for details) were identified in order to improve the accuracy of the machine learning models, these included the valence electron concentration $\mathrm { ( V E C ) } ,$ atomic size difference (δ), enthalpy of mixing $\left( \Delta \mathrm { H } _ { \mathrm { m i x } } \right)$ , entropy of mixing $( \Delta S _ { \mathrm { m i x } } )$ , melting point $\left( \mathrm { T } _ { \mathrm { m } } \right)$ , and Pauli electronegativity difference $( \Delta \chi )$ $\mathtt { A }$ total of 448 samples, each with 10 features, including the four con stituent elements and the six input features, were collected. The original dataset comprises samples with diverse compositions. To ensure proper algorithm processing, missing data will be handled by elimination for the regression analysis, resulting in a total of 448 samples for $\mathrm { Y } _ { 1 } ,$ 448 for $\mathrm { Y } _ { 2 } , 4 4 8$ for $\mathrm { Y } _ { 3 } ,$ and 298 for $\mathrm { Y } _ { 4 } .$ Each sample in $\mathrm { Y } _ { 1 } , \mathrm { Y } _ { 2 } ,$ and $\mathrm { Y } _ { 3 }$ is cate gorized as $^ { 6 6 } 1 ^ { \prime \prime }$ or “0” to denote the presence or absence of specific phases: the κ phase in $\Upsilon _ { 1 } , \textsf { a } ( \gamma + \kappa )$ dual-phase region at 500– $6 0 0 ^ { \circ } \mathrm { C }$ in $\mathrm { Y } _ { 2 } ,$ and a single γ region in $\mathrm { Y } _ { 3 } ,$ making the data suitable for machine learning algorithms.

[BLOCK b0026]
2.2.2. Machine learning algorithm

[BLOCK b0027]
K-nearest neighbor (KNN) [37] is a fundamental machine-learning algorithm. Given a feature space (consisting of 10 descriptors), KNN identifies the most similar K samples (target components) in the same category $\left( \mathrm { Y } _ { 1 } , \mathrm { Y } _ { 2 } , \right.$ Y and $\mathrm { Y } _ { 4 } )$

[BLOCK b0028]
Artificial neural network (ANN) [38] is one of the most extensively used machine-learning algorithms today, comprising interconnected units termed the input layer, output layer, and hidden layer. Within this structure, the input layer processes the input data x (consisting of 10 descriptors) and subsequently produces prediction results $\boldsymbol { \tau } \left( \mathrm { Y } _ { 1 } , \mathrm { Y } _ { 2 } , \mathrm { Y } _ { 3 } \right.$ and $\mathrm { Y } _ { 4 } )$ in the output layer following processing by the hidden layer. The hidden layer hosts one or more computing units tasked with executing significant mathematical operations on the input data.

[BLOCK b0029]
Classification and regression tree (CART) [38] is a popular machine learning algorithm that utilizes single-tree models to process classifica tion or regression tasks of continuous data. CART consists of four com ponents, which include a root node (the highest decision node that represents the ultimate objective of the tree), branches (connecting the tree elements), leaf nodes (situated at the end of branches and repre senting decisions to be made), and the decision node (represents the condition that results in a dataset split).

[BLOCK b0030]
Support vector machine (SVM), a supervised learning technique, can perform classification and regression analysis by recognizing data. It is capable of efficiently handling high-dimensional, nonlinear, and scat tered samples, especially for binary classification. Essentially, SVM distinguishes a set of data features (consisting of 10 descriptors) iden tified as vectors.

[BLOCK b0031]
Random forest (RF) classifiers use ensemble methods applied to randomly selected training samples and subsets of the variables. Unlike traditional decision tree models, random forests do not use all available features in each splitting process of subtrees. Instead, a specific subset of features is randomly selected from the full set of features, with the best features chosen from the selected subset. This creates variability among the decision trees in the random forest, which improves the overall di versity of the system and, subsequently, its classification performance.

[BLOCK b0032]
To prevent overfitting, k-fold cross-validation was utilized. In this study, the established dataset was randomly divided into ten approxi mately equal parts and the predictive model was trained ten times. For the regression model, ten-fold cross-validation was also utilized to pre vent overfitting. Four evaluation indicators were used for regression models, including the correlation coefficient (R), explained variance $( \mathsf { R } ^ { 2 } )$ , mean absolute error (MAE), and root mean square error (RMSE).

[BLOCK b0033]
2.3. Experimental procedure

[BLOCK b0034]
The validity of the model-recommended compositions was tested through experimentation on a Fe-Mn-Al-C steel with the following chemical composition (wt.%): Mn-30, Al-8, C-1, and balance Fe. The steel was prepared by induction melting under an Ar atmosphere. The as-cast 25 kg ingot was homogenized at 1200 <sup>◦</sup>C for 2 h and then forged into a cross-sectional billet of 60 $\mathrm { m m } \times 6 0 \mathrm { m m }$ . After homogenization at $1 0 5 0 ~ ^ { \circ } \mathrm { C }$ for 100 min, the forging stock was hot-rolled to 12 mm thick plates, air-cooled to room temperature, and then cold-rolled with a 75 % thickness reduction at room temperature. The rolled plate was then annealed at $1 0 0 0 ~ ^ { \circ } \mathrm { C }$ for 15 min to achieve a recrystallized microstruc ture, subsequently water-quenched to room temperature, and aged at $5 5 0 ~ ^ { \circ } \mathrm { C }$ for 2 h.

[BLOCK b0035]
Phase identification analysis was conducted using X-ray diffraction (XRD) measurements with a Bruker D8 DISCOVER utilizing Cu Kα ra diation between $3 0 ^ { \circ }$ and ${ } ^ { 1 0 0 ^ { \circ } }$ (2θ) with a step size of 3<sup>◦</sup>/minute. The microstructure and compositional analysis were characterized using scanning electron microscopy (SEM, JEOL 7100F), electron probe microanalysis (EPMA, JEOL 8530F), and transmission electron micro scopy operating at 200 kV (TEM, JEOL 2100F). The EBSD samples were polished with SiC sandpaper to 3000 grit and electrochemically polished in a solution of $\mathrm { H C l O } _ { 4 } \colon \mathrm { C } _ { 2 } \mathrm { H } _ { 5 } \mathrm { O H } = 1 \colon 9$ (volume ratio) at $2 5 \mathrm { ~ V ~ }$ at room temperature. Uniaxial tensile tests were conducted on dog-bone-shaped specimens with a nominal strain rate of $1 \times 1 0 ^ { - 3 } s ^ { - 1 }$ at ambient tem perature using a SHIMADZU AGS universal electronic tensile tester with gauge dimensions of 10 mm (length) × 4 mm (width) $\times ~ 2$ mm (thick ness) prepared by electrical discharge machining.

[BLOCK b0036]
Fig. 2. Feature selection to identify the most important features from the feature pool. The heatmap of Pearson correlation coefficient matrix between the original 10 descriptors. A larger circle with deeper color indicates a high level of correlation.

[BLOCK b0037]
3. Results and discussion

[BLOCK b0038]
3.1. Descriptors selection

[BLOCK b0039]
To increase the robustness of the model, highly correlated de scriptors were reduced by eliminating redundant features utilizing the Pearson correlation coefficient filter [39]. In order to avoid redundancy when modeling, only one highly correlated feature was retained while the others were removed. The Pearson correlation coefficient map be tween diverse features is plotted in the lower left corner of Fig. 2. Highly correlated features were defined as those with a correlation coefficient greater than 0.95 and removed accordingly, thus, $\Delta \chi$ and δ were elim inated from the model. The Pearson correlation coefficient (PCC) for mula for describing the correlations between features is:

[BLOCK b0040]
(a) (d)

[BLOCK b0041]
(c)

[BLOCK b0042]
$$
P C C = \frac {\sum_ {i = 1} ^ {n} (x _ {i} - \overline {{x}}) (y _ {i} - \overline {{y}})}{\sqrt {\sum_ {i = 1} ^ {n} (x _ {i} - \overline {{x}}) ^ {2}} \sqrt {\sum_ {i = 1} ^ {n} (y _ {i} - \overline {{y}}) ^ {2}}}\tag{4}
$$

[BLOCK b0043]
in the above formula, ${ \bf \nabla } , { \bf X _ { i } }$ and y represent the values for descriptors x and ${ \bf y } ,$ respectively. The mean values of x and y are represented by x and ${ \bar { y } } ,$ respectively, while their corresponding standard deviations are repre sented by $\mathbb { S } _ { \mathbf { X } }$ and $\mathsf { \Delta } \mathsf { s } _ { \mathsf { y } }$ .

[BLOCK b0044]
3.2. Algorithm determination and performance evaluation

[BLOCK b0045]
3.2.1. Classification models

[BLOCK b0046]
In this study, five algorithms (KNN, ANN, SVM, RF, and CART) were used for training data via 10-fold cross-validation. Fig. 3 compares the performance of these algorithms in terms of the 10-fold cross-validation accuracy and the relative importance of the 8 descriptors used in the classifications. For the training dataset, KNN, ANN, RF, and CART all performed well in the classification task, with high cross-validation ac curacy (CVA) values, ranging from above 0.9 to less than 1. Among these algorithms, RF achieved the best performance, with CVA values of 0.98 $\left( \mathrm { Y } _ { 1 } \right)$ , 0.98 (Y<sub>2</sub>), and 0.96 (Y<sub>3</sub>). Although ANN showed satisfactory per formance on the partial classification (Y ), it performed poorly in the remaining classifications. Therefore, RF was chosen as the most appro priate algorithm for the classification prediction in this study.

[BLOCK b0047]
To determine the optimal 8 descriptors inputted into the model, the relative importance of each was evaluated. A model’s relative impor tance was assessed by successively removing each descriptor, one at a time, from the 8 descriptors and testing the model’s accuracy with the

[BLOCK b0048]
Fig. 3. Algorithm determination and the relative importance of 8 descriptors for the classifications. (a) The comparison between different machine learning methods. (b) the relative importance of 8 descriptors for a single γ region. (c) the relative importance of 8 descriptors for a $( \gamma + \kappa )$ region in 500– $6 0 0 ~ ^ { \circ } \mathrm { C } .$ (d) the relative importance of 8 descriptors for the existence of the κ-phase.

[BLOCK b0049]
Fig. 4. (a) The comparison between different machine learning methods in the high κ-phase fraction. (b) The relative importance of 8 descriptors for the high κ-phase fraction. (c) The predicted κ-phase fraction by ML model for 10-fold cross-validation.

[BLOCK b0050]
Fig. 5. Scheme of the optimization process of the Fe-Mn-Al-C austenitic lowdensity steels. The screening process is mainly divided into two steps, the first step is the phase component screening and the second step is the screening of other features (high κ-phase content $\mathrm { ( Y _ { 4 } ) }$ and low density $( \mathrm { Y } _ { 5 } ) .$ . Finally, 150 candidates are left for the search space.

[BLOCK b0051]
remaining descriptor set. The evaluation results were displaved in Fig. 3b-d. The graph indicated that Al played the most significant role in the partial classification problems (a single γ region and κ exists) since accuracy decreased the most when Al was removed from the set. This view has been confirmed by earlier studies. Al is a BCC phase stable element, and an increase in the FCC lattice parameters has a significant negative impact on the stability of single-phase austenite [7]. Addi tionally, Fig. 3c demonstrates that Mn and Fe are the most important in the $( \gamma +$ κ) region in $5 0 0 { - } 6 0 0 \ { ^ { \circ } } \mathrm { C }$ classification studies, and C still shows the least effect on the model. This result depends on the complex rela tionship between different Mn levels and phase transitions. Mn can stabilize the γ phase while increasing the FCC lattice parameter[7,9], avoiding the production of additional ferrite as a result of the addition of

[BLOCK b0052]
Al, and β-Mn phase promotion is also possible in the FeMnAlC system [13], which would affect the mechanical properties of low-density steel. The γ→ε→α<sup>ʹ</sup> and the γ→ε are separately favored for Mn contents ranging between (5–12 %) Mn and (15–30 %) Mn [14,15]. It is thus established that Mn plays a crucial role in the phase stability of steel. Similarly, Fig. 3d shows that Al has a strong influence on the presence of the κ phase, which is in alignment with earlier findings. Originally, the diffusion and enrichment of C elements were the primary causes of the formation of the κ phase, but the Al element can reduce the diffusivity of the C element while higher Al element and C element synergistically stabilize the κ phase[7]. The results of the significance analysis revealed that C had no significant impact on the presence of the κ phase. This study (Fig. 6) identified a strong correlation between the presence of the κ phase and the Al element. For instance, when the Mn content is 30 wt $^ { \% , }$ the Al content only needs to surpass the lower limit (approximately 5 wt%) to initiate precipitation of the κ phase in the system. At temper atures ranging from 500 to $6 0 0 ^ { \circ } \mathrm { C } ,$ , while the C content has an impact on the formation of the $\gamma + \kappa$ duplex region, it is closely intertwined with the role of Al. Thus, even though C plays a significant role in the composition of the κ phase in this study, the precipitation of the κ phase is primarily governed by Al. It should be noted that this assessment result variation was negligible, even after changing the sampling. The final sequence of these descriptors was inputted into the model in descending order of mean decrease accuracy values.

[BLOCK b0053]
3.2.2. Regression models

[BLOCK b0054]
The dataset is trained with five regression algorithms (KAA, ANN, SVM, RF, and GART), following a methodology akin to that used for classification problems, and undergoes 10-fold cross-validation. Fig. 4 compares the five algorithms in terms of the 10-fold cross-validation accuracy and the relative importance of eight descriptors for the regression. SVM displayed robust performance in the regression task for the training dataset, with low cross-validation RMSE values of less than 1 %. The final sequencing of descriptors for inputting into the model for the regression problem was in the following order: $\Delta S _ { \mathrm { m i x } } , \mathrm { F e } , \Delta \mathrm { H } _ { \mathrm { m i x } } , \mathrm { C } ,$ Mn, T , VEC, and Al.

[BLOCK b0055]
Fig. 4c depicts the prediction results of the training data for the regression model. The X-axis and Y-axis represent the true and predicted regression problem values $\mathrm { ( Y _ { 4 } ) _ { : } }$ , respectively. The data aligns with the blue line in Fig. 4c when the predicted κ fraction equals the true κ fraction. Correlation coefficients were utilized to evaluate the regression models’ predictive performance, revealing that the SVM algorithm had satisfactory performance across all the data.

[BLOCK b0056]
Fig. 5 demonstrates that $^ { 7 8 , 4 7 7 }$ possible composition-feature combinations were enumerated to predict $\mathrm { Y } _ { 1 } , \mathrm { Y } _ { 2 } , \mathrm { Y } _ { 3 }$ and $\mathrm { Y } _ { 4 }$ using screened models. The optimization of this search space was carried out in two stages. The initial stage involved the screening of process parameters and structures $( \mathrm { Y } _ { 1 } , \mathrm { Y } _ { 2 } ,$ and Y ). Subsequently, the boundary conditions were established in the composition space to locate a single γ region, (γ $+ \ \kappa )$ region at $5 0 0 { - } 6 0 0 \ ^ { \circ } \mathrm { C } ,$ , and κ phases. Consequently, 1,320 satisfactory candidates were screened out. The second stage was the performance filtering for $\mathrm { Y } _ { 4 }$ and low density, leading to the identifica tion of 150 candidates with high κ fractions (more than 10 %) and low density (less than or equal to $7 \ { \mathrm { g } } / { \mathrm { c m } } ^ { 3 } )$ .

[BLOCK b0057]
(a) (d)

[BLOCK b0058]
(b) (e)

[BLOCK b0059]
(c)

[BLOCK b0060]
Fig. 6. Process parameters and structural optimization process of FeMnAlC austenitic low-density steel in the 30 % Mn search space. (The first step in screening). (a) The existence of the κ phase (Y ). (b) $\mathsf { a } \gamma + \kappa$ dual-phase region at 500– $6 0 0 \ ^ { \circ } \mathrm { C } \ \left( \mathrm { Y } _ { 2 } \right)$ . (c) a single γ phase region (Y ). (d) the component space in which ${ \bf Y } _ { 1 }$ and ${ \mathrm { Y } } _ { 3 }$ are screened together. (e) the component space in which $\mathrm { Y } _ { 1 } , \mathrm { Y } _ { 2 }$ and ${ \mathrm { Y } } _ { 3 }$ are screened together. (The overall data is relatively large, and the two-dimensional search space of 30 % Mn is specially used for display.).

[BLOCK b0061]
(b)

[BLOCK b0062]
Fig, 7. Performance screening based on process parameters and structure screening, (The second step of screening). (a) The volume fraction of κ (Y4). (b) Composition optimization process (c) The density of steels $\left( \Upsilon _ { 5 } \right)$

[BLOCK b0063]
Fig. 6 illustrates the composition-structure relationship of FeMnAlC low-density steels. Due to a large amount of available data, the 30 % Mn two-dimensional search space was employed for display purposes (Fig. 6). The red area in Fig. 6a signifies the presence of the κ-phase, with an Al content critical value ranging from 4 to 4.5 %. The introduction of Al elevated the stacking fault energy, facilitating the precipitation of κ carbides; however, excessive Al content could induce the formation of the BCC phase[7]. Furthermore, the results indicate that while C plays a significant role in the composition of the κ phase, it does not solely govern its precipitation. At temperatures of $5 0 0 { - } 6 0 0 ^ { \circ } \mathrm { C } ,$ , the $( \gamma + \kappa )$ dualphase region is depicted in the red region of Fig. 6b. The boundary el ements of the red region in Fig. 6b are predominantly composed of (4.5–9.3 %) Al and (0.4–1.1 %) C. Likewise, Fig. 6c shows the relationship between the single γ region and element composition, with the boundary line between the red region (Yes) and the blue region (No) fluctuating significantly as the C content escalates to 1.1 %. This vari ation is mainly attributed to C being an austenitic stable element in the FeMnAlC system, with the content of 1.1 % being critical.

[BLOCK b0064]
To offer a better understanding of the FeMnAlC system’s composition and microstructure relationship of low-density steels and the optimiza tion process, Fig. 6d-e was created. The intersection of $\mathrm { Y } _ { 1 }$ and $\mathrm { Y } _ { 3 }$ is represented by the red area in Fig. 6d, and the intersection of $\mathrm { Y } _ { 1 } , \mathrm { Y } _ { 2 } ,$ and $\mathrm { Y } _ { 3 }$ is depicted in the red region of Fig. 6e. Candidates in the red zone meet multiple requirements $\left( \mathrm { Y } _ { 1 } , \mathrm { Y } _ { 2 } , \right.$ and $\mathrm { Y } _ { 3 } )$ , indicating that they are potentially optimal for the system.

[BLOCK b0065]
The second step in the optimization process of the study is demon strated in Fig. 7a-c, with the search space based on the first step opti mization process. Fig. 7a illustrates the correlation between the κ phase fraction (Y ) and the composition of the FeMnAlC system, while Fig. 7c presents the scatter plot between density $\left( \Upsilon _ { 5 } \right)$ and FeMnAlC composition. The correlogram’s legend on the right side shows the κ fraction/density and the corresponding color intensity. Increasing the volume fraction range of the κ phase often improves the system’s strength. To further perfect the system composition, 30 potential can didates were identified by imposing additional constraints on the orig inal screening criteria (i.e., κ fraction ≥ 10 % and density $\leq 7 \ { \mathrm { g } } / { \mathrm { c m } } ^ { 3 } ) .$ with a minimum volume fraction of κ phase of 11 % and maximum system density of $6 . 9 \ \mathrm { g } / \mathrm { c m } ^ { 3 }$ . The screening protocol is delineated in Fig. 7b. In order to validate the precision of the calculated outcomes, (Fe-30Mn-8Al-1C) was chosen for experimental corroboration.

[BLOCK b0066]
Fig. 8. Experimental results of the Fe-30Mn-8Al-1C austenitic low-density steel. (a) XRD profile. (b) Inverse pole figure (IPF) map. (c) EBSD phase map. (d) Bright field (BF) TEM micrograph. (e) Dark field (DF) TEM micrograph. (f) Selected area electron diffraction (SAED).

[BLOCK b0067]
The outlined optimization process effectively screened the in gredients, combined them with the phase feature, and identified a potentially optimal composition. Concerning the optimization outcomes of the established composition space, Fe-30Mn-8Al-1C steel aged at 550 <sup>◦</sup>C was predicted to be a single-phase austenitic steel featuring low density and high strength.

[BLOCK b0068]
3.3. Experimental results

[BLOCK b0069]
The measured chemical composition of the alloy is as follows (wt.%): Mn 30.4 %, Al 7.9 %, C 1.1 %, Fe (balance). Fig. 8 displays the micro structure and structural characteristics of Fe-30Mn-8Al-1C single-phase austenitic low-density steel. Fig. 8a reveals only FCC single-phase peaks in the XRD profile of the samples. Fig. 8b and Fig. 8c display EBSD in verse pole figure (IPF) maps and phase maps (PM), respectively. The microstructure of the low-density steel is recrystallized, with an average grain size of 17 μm and a single FCC phase. TEM analysis confirms the generation of κ phase precipitates, as depicted in Fig. 8d-e. The presence of nanoscale κ phases that have precipitated under aging conditions of 550 <sup>◦</sup>C is confirmed by the bright field (BF) and dark field (DF) TEM micrographs. The κ phases were further verified through selected-area diffraction pattern analysis. Prior studies [40] have shown that while the cooling rate may not significantly affect the microstructure’s grain size, it can have a significant effect on the nanoscale microstructure. Cooling rate effects on the formation of the κ phase are similar to that of aging, with slower cooling rates resulting in a higher frequency and even distribution of the nanoscale κ phase. As this experiment employed water cooling, the generation of κ phase is confirmed to occur at 550 <sup>◦</sup>C during aging, which is further confirmed as the (γ + κ) dual-phase at 500–600 <sup>◦</sup>C. The presence of high-density κ carbide contributed significantly to the strengthening through precipitation, thus attributing the exceptional strength of high-Mn austenitic low-density steels to the presence of nano-sized intragranular κ-carbide.

[BLOCK b0070]
Fig. 9 showcases the EPMA maps Fig. 9a, featuring secondary elec tron and backscattered electron images, engineering stress–strain curves (Fig. 9b), and an optical micrograph (Fig. 9c) of the sample. EPMA map results reveal the uniform distribution of all steel elements (Fe, Mn, Al, C). In most cases, different phase structural elements exhibit significant differences in content. However, it is not difficult to confirm the pres ence of a single FCC phase in this study. In Fig. 9b, the engineering stress–strain curve indicates vield strength and tensile strength values of 953 MPa and 1109 MPa, respectively. Additionally, the steel’s elonga tion value of 42 % is impressive. Hence, it can be concluded that the austenitic low-density steel produced in this study effectively combines high strength with excellent ductility.

[BLOCK b0071]
4. Conclusions

[BLOCK b0072]
In summary, this study utilizes machine learning algorithms to explore the correlation between the composition and the associated phase structure of low-density FeMnAlC steel. The use of this method ology enabled successful directional selection of intricate components and phase structures in these steels, making it advantageous for their design. Notably, Aluminum (Al) and carbon (C), particularly Al, played a pivotal role in regulating the phase component. Specifically, for a fixed manganese (Mn) element content of 30 wt%, the kappa phase can be maintained with an aluminum (Al) content of 4 wt%. The predicted concentrations of aluminum (Al) and carbon (C) were found to be 4.5–9.3 wt% and 0.4–1.1 wt%, respectively, and could be present in the (γ + κ) biphasic region during the aging process at temperatures ranging from 500 <sup>◦</sup>C to 600 <sup>◦</sup>C. A maximum Al content of 11.6 wt% is necessary to ensure the presence of a single austenitic zone. The characterization of the Fe-30Mn-8Al-1C component validated our research, demon strating the effectiveness of the proposed design approach. Furthermore, these findings hold potential for application in designing other metallic materials.

[BLOCK b0073]
CRediT authorship contribution statement

[BLOCK b0074]
Peng Tiexu: Writing – original draft, Software, Methodology,

[BLOCK b0075]
Fig. 9. (a) Element distribution maps of element distribution with secondary electron map and backscattered electron map. (b) Engineering stress–strain curves. (c) Optical micrographs.

[BLOCK b0076]
Conceptualization. Yu Haoyang: Methodology, Investigation, Formal analysis. Huang Jiaxin: Visualization, Methodology. Fang wei: . Li Cong: Investigation, Data curation. Yao Zitong: Investigation, Data curation. Zhang Xin: Investigation, Data curation. Feng Jianhang: Methodology. Ji Puguang: Methodology. Xia Chaoqun: Resources. Yu Hui: Methodology, Investigation, Formal analysis. Yin Fuxing: Super vision, Resources.

[BLOCK b0077]
Declaration of competing interest

[BLOCK b0078]
The authors declare that they have no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.

[BLOCK b0079]
Data availability

[BLOCK b0080]
I have shared the link to my data

[BLOCK b0081]
Acknowledgments

[BLOCK b0082]
This research was supported by the National Natural Science Foun dation of China (No. 51701061); the Natural Science Foundation of Hebei Province (No. E2019202059, E2021202075, E2020202124); the foundation strengthening program (No: 2019-JCJQ-142-00); the Key-

[BLOCK b0083]
Area R&D Program of Guangdong Province (No. 2020B0101340004), Guangdong Academy of Science (2021GDASYL-20210102002), Jiangsu Provincial Policy Guidance Program (Special Project for the Introduc tion of Foreign Talents) Talent Introduction Program Project (No. BX2021024), and Chinese Scholarship Council (Grant No. 202106705003).

[BLOCK b0084]
Author contributions

[BLOCK b0085]
Tiexu Peng: Conceptualization, Methodology, Software, Writing - Original Draft; Haoyang Yu: Investigation, Methodology, Formal Analysis, Calculation; Jiaxin Huang: Visualization, Methodology; Wei Fang: Conceptualization, Writing - Review & Editing, Funding acqui sition, Supervision; Cong Li: Investigation, Data curation; Zitong Yao: Investigation, Data curation; Xin Zhang: Investigation, Methodology; Jianhang Feng: Methodology; Puguang Ji: Methodology; Chaoqun Xia: Resources; Hui Yu: Resources, Investigation, Conceptualization; Fuxing Yin: Resources, Supervision.

[BLOCK b0086]
Data and materials availability

[BLOCK b0087]
The data that support the results of this study are available from the corresponding authors upon reasonable request. The original dataset was published on Mendeley at https://data.mendeley.com/drafts/

[BLOCK b0088]
References
