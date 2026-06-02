# QMOF-Rec: AI-Powered Recommender System for Materials Discovery

**QMOF-Rec** is an end-to-end AI platform for **QMOF-based materials discovery, recommendation, property prediction, and scientific assistance**.  
The system combines recommender systems, graph neural networks, retrieval-augmented generation, and large language models to support explainable and interactive discovery of metal–organic frameworks.

---

## Overview

Metal–organic frameworks are highly promising materials for applications such as gas adsorption, hydrogen storage, CO₂ capture, photocatalysis, and drug delivery. However, selecting the right MOF for a target application is challenging due to the large design space and the complexity of structure–property relationships.

**QMOF-Rec** aims to provide an intelligent recommender system that helps researchers:

- Recommend promising QMOFs for a target application
- Predict material properties from structural or metadata inputs
- Explore material similarity using graph and embedding models
- Ask scientific questions through a RAG-powered chat assistant
- Visualize MOF structures and recommendation results
- Improve recommendations through user feedback

---

## System Architecture

The platform follows a modular end-to-end architecture:

```text
Frontend  →  Backend API  →  Recommendation / Prediction / RAG Services
                         →  Databases, Vector Store, ML Models, LLMs
