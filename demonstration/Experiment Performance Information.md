# Experiment run times:





reference this doc in the creation of the demonstration slide pack, link each plot to the PC specs performing the simulation, and comment on the performance, describe how altering the circuit execution logic to enable multiprocessor execution improved runtime duration. reference the scaling image to describe the relationship between parameter set up, and the quantity of calculations required.



##### 1\. Baseline Proof: 

* &#x09;Bar chart of Mutual Info \& QBER for all three protocols on an ideal channel.

  * Trial 1 duration (SHEILA): 01:05, completed successfully





##### 2\. Noise Resilience: 

* &#x09;Noise vs. Secure Key Rate for BB84, B92, and E91, overlaid on the same plot.

  * Trial 1 duration (SHEILA): 20:45, completed successfully



##### 3\. Eve Vulnerability: 

* &#x09;Eve Rate vs. QBER for BB84 and B92, overlaid on the same plot, with dynamic QBER security thresholds (where D-W bound,  K = 0), and perpendicular x-line for intercept thresholds in contrasting colours for plot visibility.

  * Trial 1 duration (SHEILA): 15:32, failed due to missaligned logic
  * Trial 2 duration (SHEILA): 32:30, improved performance, muddled up the plotting code and incorrectly presented the threshold lines
  * Trial 3 duration (SHEILA): 25:10, completed successfully





##### 4\. E91 Entanglement Mechanics (2D Twin-Axis): 

* &#x09;Noise vs. S-Parameter \& QBER (Proves E91's unique security mechanism), with current static security thresholds at tsireslon bound S = 2sqrt2, and classical bound S = 2.

  * Trial 1 duration (SHEILA): 10:48, completed successfully







##### Multivariable Systems:

I redeveloped the processing logic to enable multicore processing for the v.2 systems



###### 5\. BB84 Noise Strength vs. Eve Rate vs. QBER with the 11% threshold plane

* &#x09;Plot data was exported as a .csv file for MATLAB plotting

  * V.1:

    * Trial 1 duration (SHEILA): 16:47, original config parameters, completed successfully, plotted in MATLAB
  * V.2:

    * Trial 1 duration (big PC): 14:40, increased parameter density to improve the voracity of the 3D surface plots, overall much more presentable but the QBER threshold is not exceeded for noise strength axis
  * V.3:

    * Trial 1 duration (big PC): 13:20, parameters adapted in this final version to optimise the plots.









###### 6\. B92 Noise Strength vs. Eve Rate vs. QBER with the 6.5% threshold plane 

* &#x09;Plot data was exported as a .csv file for MATLAB plotting

  * V.1:

    * Trial 1 duration (SHEILA): 16:27, original config parameters, completed successfully, plotted in MATLAB
  * V.2:

    * Trial 1 duration (big PC): 11:28, increased parameter density to improve the voracity of the 3D surface plots, overall much more presentable but the QBER threshold is not exceeded for noise strength axis
  * V.3:

    * Trial 1 duration (big PC): 11:14, parameters adapted in this final version to optimise the plots.





