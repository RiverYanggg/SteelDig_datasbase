[BLOCK b0001]
Extreme high accuracy prediction and design of Fe-C-Cr-Mn-Si steel using machine learning

[BLOCK b0002]
Hao Wu , Jianyuan Zhang , Jintao Zhang , Chengjie Ge , Lu Ren , Xinkun Suo

[BLOCK b0003]
Multidimensional Additive Manufacturing Institute, Faculty of Mechanical Engineering and Mechanics, Ningbo University, 315211 Ningbo, PR China

[BLOCK b0004]
A R T I C L E I N F O

[BLOCK b0005]
Keywords: Fe-C-Cr-Mn-Si steel Machine learning Conditional generative adversarial networks Solid solution strengthening Firefly optimization algorithm

[BLOCK b0006]
A B S T R A C T

[BLOCK b0007]
Solid solution strengthening theory is essential for designing steel with high microhardness. Experimental determination is quite time consuming and costly. It is necessary to develop an alternate approach to rapidly and accurately predict new solid solution strengthening theory for steel. In this study, a data-driven model combining machine learning (ML), firefly optimization algorithm (FA) and conditional generative adversarial network (CGANs) were proposed to predict solid solution strengthening theory of Fe-C-Cr-Mn-Si steel. Three alloys were fabricated using cladding to validate the predict accuracy of the models. The results show that the trained support vector regression (SVR) model demonstrated the highest prediction precision for microhardness. The coefficient of determination $( R ^ { 2 } )$ value increased from 0.85 to 0.89 and root mean square error (RMSE) decreased from 0.39 to 0.31 after introducing the modified solid solution strengthening theory. The experimental validation revealed a minimum error of 1.17% between the predicted value and the experimental value. The investigation provides a valuable method to expedite design of Fe-C-Cr-Mn-Si steel with extreme high accuracy.

[BLOCK b0008]
1. Introduction

[BLOCK b0009]
Fe-C-Cr-Mn-Si alloy steel is susceptible to wear and cracking due to low surface hardness. Various efforts have been made to improve the surface hardness and service life of the steel [1]. Machine learning (ML) is an effective method to develop new theory and new materials with low time and cost [2–5]. Huang et al. developed a ML model for the prediction of time–temperature-transformation diagrams of high-alloy steel [6] and stainless steel [7].Geng et al. [8] proposed a ML approach to predict the continuous cooling transformation diagrams in synthetic weld heat-affected zones for Ni-Cr-Mo steel. Wei et al. [9] constructed a ML model for predicting the creep life of the austenitic steel. The gaussian regression model exhibited high predictive accuracy, with a determination coefficient $( R ^ { 2 } )$ of 0.97. Wang et al. [10] employed ML and stochastic optimization to accelerate the design of the Fe-based soft magnetic materials. The $R ^ { 2 }$ value with random forest (RF) model was 0.86 and 0.82 for predicting magnetic saturation and magneto striction, respectively. Ruiz et al. [11] constructed a regression model based on the gradient boosting algorithm with the $R ^ { 2 ^ { \prime } }$ value of 0.87, revealing the correlation between the tempering temperature and fa tigue life. Yang et al. [12] predicted the hardness and yield strength of the oxide dispersion strengthened steel using six ML models. The results showed that the extreme gradient boosting model (XGBoost) had the lowest RMSE value of 63.78 and the highest $R ^ { 2 }$ value of 0.91 for hard ness prediction. In terms of yield strength prediction, the XGBoost model had the lowest RMSE value of 54.06 and the highest $R ^ { 2 }$ value of 0.90.

[BLOCK b0010]
Prediction accuracy of ML is affected by many factors, for example material science theory and quantity of data [13]. Solid solution strengthening is a basic mechanism in metallurgy, playing a crucial role in improving microhardness of alloys. Ren et al. [14] proposed a datadriven ML model combined with the modified solid solution strength ening theory $( \Delta \sigma _ { S S S } = Z \xi G ^ { * } M . E )$ for the hardness prediction of the high entropy alloys. The $R ^ { 2 }$ and RMSE value was 0.97 and 39.25 respectively. The prediction error of the model was 2.01 %. Gao et al. [15] con structed the generic model combining solid solution strengthening for hardness prediction of the high entropy alloys. The $R ^ { 2 }$ value reached 0.91 in an independent test set. However, the investigation on the solid solution strengthening theory for Fe-based alloy steel has not been found.

[BLOCK b0011]
In this study, a ML-based prediction model combining firefly opti mization algorithm (FA) was proposed to predict the microhardness of the Fe-C-Cr-Mn-Si steel. Conditional generative adversarial networks (CGANs) were employed to generate synthetic data to overcome the limitation of the data set. Modified solid solution strengthening theory was introduced to improve the physical interpretability and predictive accuracy of the model. The Fe-C-Cr-Mn-Si steel with the predicted composition was produced by cladding to validate the prediction ac curacy of the ML model.

[BLOCK b0012]
Fig. 1. Flow chart of microhardness prediction and design of Fe-C-Cr-Mn-Si steel.

[BLOCK b0013]
<table><tr><td colspan="3">Generator network</td><td colspan="3">Discriminator network</td></tr><tr><td>Layer name</td><td>Architecture</td><td>Detail</td><td>Layer</td><td>Architecture</td><td>Detail</td></tr><tr><td>Input layer</td><td>Random noise</td><td>100</td><td>Input layer</td><td>Feature + property</td><td>12(11 + 1)</td></tr><tr><td rowspan="4">Hidden layer 1</td><td>Dense layer</td><td>64</td><td>Hidden layer 1</td><td>Dense layer</td><td>128</td></tr><tr><td>Activation</td><td>Relu</td><td></td><td>Activation</td><td>Relu</td></tr><tr><td>Batch normalization</td><td>Yes</td><td></td><td>Batch normalization</td><td>Yes</td></tr><tr><td>Regularizer</td><td>L2 = 0.01</td><td></td><td>Regularizer</td><td>L2 = 0.01</td></tr><tr><td rowspan="4">Hidden layer 2</td><td>Dense layer</td><td>128</td><td>Hidden layer 2</td><td>Dense layer</td><td>64</td></tr><tr><td>Activation</td><td>Relu</td><td></td><td>Activation</td><td>Relu</td></tr><tr><td>Batch normalization</td><td>Yes</td><td></td><td>Batch normalization</td><td>Yes</td></tr><tr><td>Regularizer</td><td>L2 = 0.01</td><td></td><td>Regularizer</td><td>L2 = 0.01</td></tr><tr><td rowspan="3">Output layer</td><td>Feature + property</td><td>12(11 + 1)</td><td>Output layer</td><td>Dense layer</td><td>1</td></tr><tr><td>Activation</td><td>Tanh</td><td></td><td>Activation</td><td>Sigmoid</td></tr><tr><td>Regularizer</td><td>L2 = 0.01</td><td></td><td>Regularizer</td><td>L2 = 0.01</td></tr></table>

[BLOCK b0014]
2. Materials and methodology

[BLOCK b0015]
2.1. Construction of the ML model

[BLOCK b0016]
The design strategy of the ML model is summarized in Fig. $^ { 1 , }$ con sisting of data collection and pre-processing, feature engineering, model construction, and inverse design.

[BLOCK b0017]
2.1.1. Data collection and pre-processing

[BLOCK b0018]
173 Fe-C-Cr-Mn-Si steel data points were obtained from the widely recognized material information repository MatWeb [16]. In the data set, 11 elements were collected, including C, Si, Mn, Cr, S, Ni, P, Fe, Mo, V and $\mathsf { W } ,$ as well as microhardness of steel.

[BLOCK b0019]
The Z-score method was applied to screen each feature in the dataset, and the data points with |z| > 1.50 were defined as the outliers. Sub sequently, the isolation forest model was used to further refine the outlier detection process based on the pre-screened dataset. The data points lower than 0 or higher than 0.15 were classified as the outliers, and then they were removed from the data set.

[BLOCK b0020]
CGANs were used to augment the rest of the data set. The double hidden layers were employed to strengthen the learning ability of the generator and the accuracy of the discriminator. The detailed parame ters of the CGANs are shown in Table 1. As a result, the data set was expanded from 98 data points to 192 data points.

[BLOCK b0021]
The correlation scatter matrix graph was employed to reveal the relationship between the composition and microhardness of the steel, in which the elements and microhardness of the data set was employed to create a variable list, and the Seaborn library was used to plot the graph [17].

[BLOCK b0022]
2.1.2. Feature engineering

[BLOCK b0023]
41 features were collected and standardized to ensure equal contri bution of each feature and eliminated the bias from the scale differences. The feature calculation formulas are shown in Table 2.

[BLOCK b0024]
Here, $c _ { i }$ and $c _ { j }$ are the mole fractions of the $i ^ { t h }$ and $j ^ { t h }$ elements, respectively. k is the corresponding element parameter.

[BLOCK b0025]
The process of feature engineering was as follows [18,19]:

[BLOCK b0026]
(1) Feature importance voting: The Recursive Feature Elimination (RFE) models wrapped the random forest (RF), light gradient boosting machine (LightGBM) or extreme gradient boosting (XGBoost) algorithm separately were used to rank the features. Only the first features ranked by all the three models were selected as the candidate features.

[BLOCK b0027]
Table 2 List of input material features.

[BLOCK b0028]
<table><tr><td>Feature name</td><td>Abbreviation</td><td>Calculation formula</td></tr><tr><td>Weighting parameters</td><td></td><td></td></tr><tr><td>Valence electron concentration</td><td>VEC</td><td> $k = \sum_{i=1}^{n} c_i * k_i$ </td></tr><tr><td>Melting point</td><td>Tm</td><td></td></tr><tr><td>Number of itinerant electrons</td><td>e/a</td><td></td></tr><tr><td>Shear modulus</td><td>G</td><td></td></tr><tr><td>Young&#x27;s modulus</td><td>E</td><td></td></tr><tr><td>Cohesive energy</td><td>Ec</td><td></td></tr><tr><td>Work function</td><td>w</td><td></td></tr><tr><td>Atomic radii</td><td>r</td><td></td></tr><tr><td>Pauling electronegativity</td><td> $\chi$ </td><td></td></tr><tr><td>Bulk modulus</td><td>B</td><td></td></tr><tr><td>Poisson&#x27;s ratio</td><td> $\nu$ </td><td></td></tr><tr><td>First ionization energy</td><td> $E_{l-1st}$ </td><td></td></tr><tr><td>Second ionization energy</td><td> $E_{l-2nd}$ </td><td></td></tr><tr><td>Thermodynamic parameters</td><td></td><td></td></tr><tr><td>Mixing entropy</td><td> $\Delta Smix$ </td><td> $\Delta Smix = -8.314 \sum_{i=1}^{n} c_i * \ln(c_i)$ </td></tr><tr><td>Mixing enthalpy</td><td> $\Delta Hmix$ </td><td> $\Delta Hmix = 4 \sum_{i=1,j>i}^{n} c_i c_j H_{i-j}^{mix}$ </td></tr><tr><td>Gibbs free energy</td><td>Gmix</td><td> $Gmix = Hmix - Tm * Smix$ </td></tr><tr><td>Mismatch parameters</td><td></td><td></td></tr><tr><td>Shear module mismatch in strengthening model</td><td> $\eta_G$ </td><td rowspan="2"> $\eta_k = \frac{2(k_i - \sum_{j=1}^{n} c_j k_j)}{c_i + \sum_{j=1}^{n} c_j k_j} \sum_{i=1}^{n} \frac{2(k_i - \sum_{j=1}^{n} c_j k_j)}{k_i + \sum_{j=1}^{n} c_j k_j}$ </td></tr><tr><td>Bulk module mismatch in strengthening model</td><td> $\eta_B$ </td></tr><tr><td>Difference in shear modulus</td><td> $\delta G$ </td><td rowspan="10"> $\delta k = \sqrt{\sum_{i=1}^{n} c_i * \left(1 - \frac{k_i}{k}\right)^2}$ </td></tr><tr><td>Difference in bulk modulus</td><td> $\delta B$ </td></tr><tr><td>Difference in poisson&#x27;s ratio</td><td> $\delta_\nu$ </td></tr><tr><td>Difference of radius</td><td> $\delta_r$ </td></tr><tr><td>Difference in melting temperature</td><td> $\delta_{Tm}$ </td></tr><tr><td>Difference in valence electron concentration</td><td> $\delta_{VEC}$ </td></tr><tr><td>Difference in free electron concentration</td><td> $\delta_{e/a}$ </td></tr><tr><td>Difference in cohesive energy</td><td> $\delta_{Ec}$ </td></tr><tr><td>Difference in first ionization energy</td><td> $\delta_{EI-1st}$ </td></tr><tr><td>Difference in second ionization energy</td><td> $\delta_{EI-2nd}$ </td></tr><tr><td> $\gamma$  parameter</td><td> $\gamma$ </td><td> $\gamma = \frac{1 - \sqrt{\frac{(r + r_{min})^2 - r^2}{(r + r_{min})^2}}}{1 - \sqrt{\frac{(r + r_{max})^2 - r^2}{(r + r_{max})^2}}}$ </td></tr><tr><td>Difference in electronegativity</td><td> $\Delta \chi$ </td><td> $\Delta \chi = \sqrt{\sum_{i=1}^{n} c_i * (\chi - \chi_i)^2}$ </td></tr><tr><td>Local shear modulus mismatch</td><td> $D_G$ </td><td> $D_k = \sum_{i=1}^{n} \sum_{j=1,i\neq 1}^{n} c_j c_j |k_i - k_j|$ </td></tr><tr><td>Local bulk modulus mismatch</td><td> $D_B$ </td><td></td></tr><tr><td>Local radius mismatch</td><td> $D_r$ </td><td></td></tr><tr><td>Local poisson&#x27;s ratio mismatch</td><td> $D_\nu$ </td><td></td></tr><tr><td>Local electronegativity mismatch</td><td> $D_\chi$ </td><td></td></tr><tr><td>Local melting temperature mismatch</td><td> $D_{Tm}$ </td><td></td></tr><tr><td>Local valence electron concentration mismatch</td><td> $D_{VEC}$ </td><td></td></tr><tr><td>Local free electron concentration mismatch</td><td> $D_{e/a}$ </td><td></td></tr><tr><td>Local cohesive energy mismatch</td><td> $D_{Ec}$ </td><td></td></tr><tr><td>Local first ionization energy mismatch</td><td> $D_{EI-1st}$ </td><td></td></tr><tr><td>Local second ionization energy mismatch</td><td> $D_{EI-2nd}$ </td><td></td></tr></table>

[BLOCK b0029]
Table 3 Parameter configurations of the optimization algorithms.

[BLOCK b0030]
<table><tr><td>Algorithm</td><td>Parameter configurations</td></tr><tr><td>FA</td><td>max_iter = 500, firefly_num = 100, alpha = 0.01, betamin = 0.2, gamma = 1,</td></tr><tr><td>SA</td><td>max_iter = 500, initial_temperature = 100, cooling_rate = 0.95,</td></tr><tr><td>PSO</td><td>max_iter = 500, particle_num = 100, c1 = 0.8, c2 = 0.5, w = 0.5</td></tr><tr><td>GWO</td><td>max_iter = 500, num_wolves = 100, alpha = 2, beta = 1.5, delta = 0.5, a = 2,</td></tr></table>

[BLOCK b0031]
Parameters of cladding.

[BLOCK b0032]
<table><tr><td>Current (A)</td><td>Voltage (V)</td><td>Cladding speed (m/h)</td><td>Interlayer temperature (°C)</td><td>Wire feed speed (m/h)</td></tr><tr><td>440 ~ 600</td><td>30 ~ 32</td><td>24</td><td>380 ~ 410</td><td>76.8</td></tr></table>

[BLOCK b0033]
(2) Feature correlation analysis: The Pearson Correlation Coefficient (PCC) of the candidate features was calculated, which can be calculated by the formula as follows:

[BLOCK b0034]
$$
P C C = \sum_ {i = 1} ^ {n} (y _ {i} - \frac {\overline {{y _ {i}}}) (\widehat {y _ {i}} - \widehat {\overline {{y _ {i}}}})}{\sqrt {\sum_ {i = 1} ^ {n} (y _ {i} - \overline {{y _ {i}}}) ^ {2} \sum_ {i = 1} ^ {n} (\widehat {y _ {i}} - \widehat {\overline {{y _ {i}}}}) ^ {2}}}\tag{1}
$$

[BLOCK b0035]
where $y _ { i }$ and $\widehat { y _ { i } }$ represent two different features of the $i ^ { t h }$ sample in the N-samples dataset; y and $\widehat { \overline { { y _ { i } } } }$ are their average values. The two fea tures were judged as high correlation features if the absolute value of their PCC was greater than or equal to 0.95.

[BLOCK b0036]
(3) Redundant feature elimination: One of the high correlation fea tures was remained through the average importance scores of the candidate features using the extra tree (ET), decision tree (DT), RF and XGBoost algorithm, and the features with higher scores were remained. The calculation of the average importance scores was described in detail by Chen [20].

[BLOCK b0037]
Exhaustive screening was employed to optimize the feature combi nation. The details of the exhaustive screening were described by Fang [21]. The feature combination with the lowest score was selected as the final feature combination.

[BLOCK b0038]
2.1.3. Algorithm selection and optimization

[BLOCK b0039]
Ten different ML models were trained to optimize the composition and predict the microhardness of Fe-C-Cr-Mn-Si steel, including support vector machine (SVR), ET, XGBoost, ridge regression (Ridge), LightGBM, multilayer perceptron (MLP), RF, linear regression (LR), DT, and k-nearest neighbor (KNN) [22–26]. The coefficient of determination $( R ^ { 2 } )$ and root mean square error (RMSE) were employed to ensure the reliability of the prediction model. The $R ^ { 2 }$ and RMSE defined by the formula [16]:

[BLOCK b0040]
$$
R ^ {2} = 1 - \frac {\sum_ {i = 1} ^ {n} \left(\widehat {y _ {P _ {i}}} - y _ {P _ {i}}\right) ^ {2}}{\sum_ {i = 1} ^ {n} \left(\overline {{y _ {P _ {i}}}} - y _ {P _ {i}}\right) ^ {2}} \#\tag{2}
$$

[BLOCK b0041]
$$
R M S E = \sqrt {\frac {1}{n} \sum_ {i = 1} ^ {n} \left(\widehat {y _ {P _ {i}}} - y _ {P _ {i}}\right) ^ {2}} \#\tag{3}
$$

[BLOCK b0042]
$R ^ { 2 }$ is a value between 0 and 1 that represents the proportion of variability in the dependent variable. RMSE represents the average of the model prediction error. $\widehat { y _ { P _ { i } } } , \overline { { y _ { P _ { i } } } } , y _ { P _ { i } }$ represent the predicted, mean and experimental value of each attribute, respectively. Subsequently, Bayesian optimization algorithm was employed with the optimization criterion of minimizing the RMSE to optimize the hyperparameters of ML model. Finally, the optimal model was selected by comparing the $R ^ { 2 }$

[BLOCK b0043]
Fig. 2. Correlation scatter matrix graph.

[BLOCK b0044]
and RMSE of the model.

[BLOCK b0045]
The original solid solution strengthening theory was modified by the selected features to further improve the prediction accuracy of the model [14]. The original solid solution theory could be found in the reference [27].

[BLOCK b0046]
Finally, 117 data points from the material information repository MatWeb were served as a validation data set to verify the prediction performance of the model through the ten-fold cross-validation and Bayesian optimization method, respectively.

[BLOCK b0047]
2.2. Inverse design

[BLOCK b0048]
C, Si, Mn, Cr, S, Ni, P, Mo, V and W elements were optimized, and the composition ranges were [0.02 wt%, 2 wt%], [0.1 wt%, 1 wt%], [0.15 wt%, 2 wt%], [0.5 wt%, 25 wt%], [0, 0.035 wt%], [0, 2 wt%], [0, 0.045 wt%], [0, 3 wt%], [0, 0.5 wt%], [0, 2 wt%], respectively, according to the relative references [28–31]. The element content was determined using firefly optimization algorithm (FA), simulated annealing algo rithm (SA), particle swarm optimization (PSO) and grey wolf optimi zation algorithm (GWO) [32]. Table 3 shows the parameter configurations of the algorithms. The microhardness was optimized by the selected ML model.

[BLOCK b0049]
2.3. Coating preparation and characterization

[BLOCK b0050]
The wire with the optimized element content was used as the feeding material. The ASTM A36 steel plates with the size of 300 mm × 120 mm × 40 mm were used as the substrates in the experiment. The arc cladding equipment (IDEALARC DC-1000, Lincoln Electric, America) was used to prepare the Fe-C-Cr-Mn-Si coatings. The cladding parameters were shown in Table 4.

[BLOCK b0051]
(a) Feature selection for hardness prediction (c)

[BLOCK b0052]
(b)

[BLOCK b0053]
Fig. 3. Feature selection: (a) Feature selection by RFE voting. (b) Heatmap showing the PCC between the 9 features (c) The importance ranking of the 9 features.

[BLOCK b0054]
Fig. 4. Exhaustive screening results with different numbers of features.

[BLOCK b0055]
The phases of the coatings were analyzed by X-ray diffraction (SmartLab SE, Rigaku, Japan) with Cu Kα radiation, operated at a working voltage of 40 kV and current of 40 mA. The Vicker’s micro hardness of the coatings was measured using a microhardness indenter (HVS-1000A, Laizhou Huayin Testing Instrument Co., Ltd., China). The load was 1 kg with the holding time of 20 s.

[BLOCK b0056]
3. Results and discussion

[BLOCK b0057]
3.1. ML algorithm modeling

[BLOCK b0058]
3.1.1. Screening results of elements

[BLOCK b0059]
Fig. 2 presents the correlation scatter matrix graph, revealing the correlation between the chemical composition and microhardness of the alloy. The diagonal probability density histograms indicated that the Cr element exhibited a positive correlation with the microhardness. fol. lowed by Ni, Mo. Whereas, Mn, V and W showed weaker correlations. Cr, Ni and Mo can form solid solution alloys and carbides as the strengthening phases [33], and Ni can reduce the grain size of the alloys [34].

[BLOCK b0060]
3.1.2. Screening results of features

[BLOCK b0061]
The recursive feature elimination (RFE) method wrapped the RF, LightGBM and XGBoost algorithm was used to rank the importance of the original features, and the results are shown in Fig. 3a. The dark blue cells in Fig. 3a indicated the significant features (marked by 1). The result shows that $E _ { I - 2 n d } ,$ η , w, δE , D , δ , r, G and e/a presented the highest importance ranking in the RF, LightGBM and XGBoost algo rithm. Fig. 3b shows the heat map of the selected features used to predict microhardness. It is found that the PCC absolute value of the E and $w ,$ $\eta _ { B }$ and w, $E _ { I - 2 n d }$ and $\eta _ { B } ,$ r and $D _ { E C } , E _ { I - 2 n d }$ and $\delta E _ { I - 2 n d } , \delta E _ { I - 2 n d }$ and $\eta _ { B }$ pair were equal to or greater than 0.95, showing the high correlation. The importance scores of the nine features were employed to remove one of the features with the high correlation in the six pairs, shown in Fig. 3c. It is found that $\eta _ { B } , w , \delta E _ { I - 2 n d }$ and r were removed in the pairs due to the low importance scores. Finally, e/a, G, E , δ and $D _ { E C }$ were found to be the key features for the microhardness. The $e / a$ ratio affected the phase stability of alloys during the formation of FCC and BCC phases: i $\dot { \mathbf { \eta } } e / a <$ 1.65, the alloy tended to form the FCC phase; if $e / a > 2 . 0 5 $ , the alloy tended to form the BCC phase [35]. The shear modulus G was crucial in increasing the plastic deformation resistance by increasing the solute atom-dislocation interaction energy, thereby increasing the hardness [36]. The second ionization energy $E _ { I - 2 n d }$ was also an important factor influencing solid solution strengthening involving in the electron cloud interaction and charge redistribution between adjacent atoms [37].The cohesive energy mismatch parameters, $\delta _ { E C }$ and $D _ { E c } ,$ were utilized to describe the bonding states and bonding strength [38].

[BLOCK b0062]
(a) (d)

[BLOCK b0063]
(c)

[BLOCK b0064]
(f)

[BLOCK b0065]
(g)

[BLOCK b0066]
(h)

[BLOCK b0067]
(i) Fig. 5. The predictive microhardness based on the SVR model (a), ET model (b), MLP model (c), Ridge model (d), LightGBM model (e), XGBoost model (f), RF model (g), LR model (h), and DT model (i).

[BLOCK b0068]
Table 5 Hyperparameter configurations of the SVR model.

[BLOCK b0069]
<table><tr><td>Model</td><td colspan="8">Hyperparameter configuration</td></tr><tr><td>SVR</td><td>C</td><td>cache_size</td><td>coef0</td><td>degree</td><td>epsilon</td><td>gamma</td><td>kernel</td><td>tol</td></tr><tr><td>____</td><td>4.98</td><td>118.85</td><td>0.63</td><td>4</td><td> $1.87 \times 10^{-4}$ </td><td> $3.57 \times 10^{-2}$ </td><td>ploy</td><td> $1.22 \times 10^{-3}$ </td></tr></table>

[BLOCK b0070]
Fig. 4 illustrates the result of the exhaustive search analysis, revealing the cross-validation scores as a function of the number of the features. It is found that the minimum RMSE was 0.341, 0.267, 0.257, 0.271, 0.281 for the cross-validation scores with the 1, 2, 3, 4, 5 features, respectively, indicating that 3 features presented the optimal prediction accuracy. Besides, the feature combination $\{ \delta _ { E c } , D _ { E c } , G \}$ presented the smallest RMSE value (0.257), and was identified as the key factors. The local cohesive energy mismatch $\delta _ { E C }$ and the difference in cohesive en ergy $D _ { E C }$ were the parameters related to cohesive energy $E c ,$ which changed linearly with the chemical composition in complete solid so lution systems [39]. The shear modulus change was suggested as one of the most predominant effects in solid solution. which was related to the interaction force between the solid solution obstacles and dislocation

[BLOCK b0071]
[40].

[BLOCK b0072]
3.1.3. Screening results of models

[BLOCK b0073]
The SVR, ET, MLP, Ridge, LightGBM, XGBoost, RF, LR and DT model were trained to select the optimal model. The hyperparameters of each model were optimized using Bayesian optimization and ten-fold crossvalidation. The three key features $\{ G , \delta _ { E c } , D _ { E c } \}$ were used as the input parameters and the microhardness was used as an output parameter. Fig. 5 shows the $R ^ { 2 }$ and RMSE values of the different ML models. It is found that the $R ^ { 2 }$ values obtained by SVR, ET, MLP, Ridge, LightGBM, XGBoost. RF. LR and DT were 0.85, 0.80. 0.81, 0.82, 0.63. 0.79. 0.74 0.76 and 0.72 respectively, and the RMSE values were 0.39, 0.45, 0.44, 0.43, 0.62, 0.46, 0.52, 0.48 and 0.54 respectively. The $R ^ { 2 }$ values ob tained by SVR, ET, MLP and Ridge were higher than 0.80, and the RMSE values were lower than 0.45, indicating great linear correlation. Although the $R ^ { 2 }$ values of ET, XGBoost and DT reached 0.80, 0.79 and 0.72, there was a potential risk of overfitting between these three models based on testing data. The SVR model presented the highest $R ^ { 2 }$ value (0.85) and the lowest RMSE value (0.39), suggesting the SVR model had the best prediction capability. The key hyperparameter configurations of the SVR model are listed in Table 5.

[BLOCK b0074]
Fig. 6. The prediction results of solid solution strengthening under ten-fold cross validation with $\{ \delta _ { E c } , D _ { E c } , G \}$ as the input features.

[BLOCK b0075]
Fig. 7. The microhardness of the inverse designed material through different algorithms.

[BLOCK b0076]
3.1.4. Model optimization by solid solution strengthening theory

[BLOCK b0077]
The solid solution strengthening equation was introduced to modify the SVR model, and the equation was as follow:

[BLOCK b0078]
$$
\Delta \sigma_ {s s s} = Z \cdot M \cdot G \cdot \delta_ {E c} \cdot D _ {E c}\tag{4}
$$

[BLOCK b0079]
Z is a fitting parameter with a value of 0.0056; M is the Taylor factor and its value was 3.06 for both FCC and BCC structures.

[BLOCK b0080]
Fig. 6 shows the validation result of the SVR model equipped with the modified solid solution strengthening theory. 117 experiment results from the materials information repository MatWeb were served as the validation dataset. It is found that the $R ^ { 2 }$ and RMSE value was 0.89 and 0.31, respectively. The $R ^ { 2 }$ increased by 4.71 %, and the RMSE decreased by 8.34 %, compared to the values without the modified solid solution strengthening theory (Fig. 5a).

[BLOCK b0081]
3.1.5. Screening results of inverse design

[BLOCK b0082]
Four intelligent optimization techniques, including simulated annealing (SA) [41], firefly optimization algorithm (FA) [42], particle swarm optimization (PSO) [43], and grey wolf optimization algorithm (GWO) [44] were employed to predict the alloy microhardness with the designed composition, and the results are shown in Fig. 7. The maximum microhardness calculated through the FA, PSO, SA, and GWO algorithm was 733.59 HV, 730.04 HV, 700.37 HV, and 708.60 HV, respectively. The alloy microhardness designed using the FA algorithm presented the highest value, followed by PSO, GWO and SA. FA was a generalized form of SA, PSO and differential evolution (DE), exhibiting superior local attraction capacity [42].

[BLOCK b0083]
3.2. Experimental verification

[BLOCK b0084]
The developed microhardness prediction model was validated by experiments. The mass percentages of the three Fe-C-Cr-Mn-Si alloy samples were listed in Table 6. Fig. 8 shows the XRD patterns of the three samples. The main phase structure of the sample 1 was Fe-Cr phase with the diffraction peaks of 100, 200 and 211. The Cr atoms randomly substituted Fe atoms in FCC lattice. With the Ni content increased, the main phase structure of the sample transferred to the Fe-Cr-Ni phase with the diffraction peaks of 100, 200 and 211. Fig. 8b reveals the enlarged XRD peaks at 2θ of 40-50<sup>◦</sup>. Compared with the standard diffraction peak of Fe, it is found that the diffraction peak of the alloy was shifted to the right at the corresponding diffraction peak, which was due to the atomic radius differences between Cr, Ni and Fe, resulting in lattice distortion [45,46].

[BLOCK b0085]
Fig. 9 shows the microhardness values of the alloys with the pre dicted composition. It is noteworthy that the minimum error between the predicted value and experimental value was 1.17 %, lower than 2.01 % and 2.96 % for predicting the hardness of high entropy alloys reported by Ren et al. [14] and Huang et al. [47]. The microhardness of the samples can reach 515 HV, which can also be attributed to the solid solution phases. It was reported that the solid solution phases were formed when $\delta _ { r } < 0 . 0 6 6$ and − $. 1 1 . 6 < \Delta H _ { m i x } < 3 . 2 \mathrm { k J / m o l }$ [48]. We can find that the δ values of the samples were in a range of 0.0335 to 0.0595, lower than 0.066, and the $\Delta H _ { m i x }$ values were in a range of − 1.213 to − 0.451 kJ/mol, belonging to the range of − 11.6 to 3.2 kJ/mol.

[BLOCK b0086]
4. Conclusions

[BLOCK b0087]
A machine learning model combined the modified solid solution strengthening theory was built to predict the microhardness of the Fe-C Cr-Mn-Si steel. There steels with the predicted composition were pre pared using cladding to verify the prediction accuracy of the model. The main conclusions can be drawn:

[BLOCK b0088]
(1) Cr had the greatest positive impact on the microhardness of the Fe-C-Cr-Mn-Si steel, followed by Ni and Mo.

[BLOCK b0089]
Mass percentages of the three Fe-C-Cr-Mn-Si alloys used for model validation.

[BLOCK b0090]
<table><tr><td colspan="12">CSiMnCrSNiPFeMoVW mass percentage</td><td rowspan="2"> $\delta_r$ </td><td rowspan="2"> $\Delta H_{mix}$ (kJ/mol)</td></tr><tr><td></td><td>C</td><td>Si</td><td>Mn</td><td>Cr</td><td>S</td><td>Ni</td><td>P</td><td>Fe</td><td>Mo</td><td>V</td><td>W</td></tr><tr><td>Sample 1</td><td>0.45</td><td>0.19</td><td>1.53</td><td>14</td><td>0.01</td><td>0</td><td>0.014</td><td>83.806</td><td>0</td><td>0</td><td>0</td><td>0.0542</td><td>-0.914</td></tr><tr><td>Sample 2</td><td>0.53</td><td>0.4</td><td>1.9</td><td>5.3</td><td>0.01</td><td>1.13</td><td>0.013</td><td>89.277</td><td>0</td><td>0.25</td><td>1.19</td><td>0.0595</td><td>-1.213</td></tr><tr><td>Sample 3</td><td>0.15</td><td>0.5</td><td>1.5</td><td>5.2</td><td>0</td><td>1.2</td><td>0</td><td>89.7</td><td>1.5</td><td>0.25</td><td>0</td><td>0.0335</td><td>-0.451</td></tr></table>

[BLOCK b0091]
(b) Fig. 8. XRD patterns of three samples (a), and the enlarged peaks at 40-50<sup>◦</sup>(b).

[BLOCK b0092]
the work reported in this paper.

[BLOCK b0093]
Fig. 9. Predicted versus actual microhardness of three samples of Fe-C-Cr-Mn-Si alloys.

[BLOCK b0094]
(2) The difference in cohesive energy, local cohesive energy mismatch and shear modulus exhibited more pronounced im pacts on the microhardness of the steel.

[BLOCK b0095]
(3) The solid solution strengthening theory was modified using the difference in cohesive energy, local cohesive energy mismatch and shear modulus, and the predicted $R ^ { 2 }$ and RMSE value ach. jeved 0.89 and 0.31.

[BLOCK b0096]
(4) The microhardness of the predicted samples reached 515 HV, with the error between the predicted value and experimental value of 1.17 %.

[BLOCK b0097]
CRediT authorship contribution statement

[BLOCK b0098]
Hao Wu: Writing – original draft, Software, Resources. Jianyuan Zhang: Validation. Jintao Zhang: Visualization. Chengjie Ge: Valida tion. Lu Ren: Software, Resources. Xinkun Suo: Writing – review & editing, Supervision.

[BLOCK b0099]
Declaration of competing interest

[BLOCK b0100]
The authors declare that they have no known competing financial interests or personal relationships that could have appeared to influence

[BLOCK b0101]
Acknowledgements

[BLOCK b0102]
This work was supported by National Natural Science Foundation of China (No. 52171072).

[BLOCK b0103]
Data availability

[BLOCK b0104]
Data will be made available on request.

[BLOCK b0105]
References
