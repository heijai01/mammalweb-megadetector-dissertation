# PROJECT_CONTEXT.md

# MammalWeb Dissertation Project

## Student

Raymond Cheng

## Supervisor

Phil

## Project Overview

This dissertation project focuses on evaluating the use of MegaDetector confidence thresholds for filtering human images within MammalWeb camera trap datasets.

The project investigates how different confidence thresholds affect:

* Human image detection performance
* Privacy and safeguarding risks
* False positives and false negatives
* Retention of useful wildlife images

The work is primarily evaluation and analysis focused rather than training a new object detection model from scratch.

---

# Key Concepts

## MegaDetector

MegaDetector is an object detection model used for identifying:

* Animals
* Humans
* Vehicles

The model outputs confidence scores for detections.

Example:

* Human: 0.92
* Animal: 0.81

Thresholds can then be applied to determine whether an image should be filtered or retained.

---

# Current Dissertation Direction

Main areas of investigation:

* Relationship between confidence scores and filtering thresholds
* Precision and recall at different thresholds
* False positive vs false negative trade-offs
* Ethical/privacy implications of missed human detections
* Categories of human images and associated risk levels

Examples:

* High-risk human images:

  * Visible faces
  * Children
  * Sensitive situations

* Lower-risk human images:

  * Distant humans
  * Blurry/non-identifiable humans
  * Partially obscured humans

---

# Technical Areas

Planned topics/tools:

* Python
* Pandas
* Jupyter Notebook
* Object detection
* MegaDetector
* Threshold analysis
* Precision / Recall
* Confusion matrix
* ROC curves
* Data visualisation

---

# Current Status

* Database login working
* Initial supervisor guidance received
* Learning CNN and object detection fundamentals
* Preparing exploratory analysis workflow

---

# Notes

This repository may contain sensitive research material and should remain private unless cleaned for public release.
